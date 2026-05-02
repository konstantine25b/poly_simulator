from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from polymarket.auth import Access
from polymarket.api.markets import fetch_market
from polymarket.config import settings
from polymarket.db import Connection, execute, fetchall, get_connection, placeholder
from polymarket.trading.pricing import (
    _buy_fill_price,
    _mark_price,
    _resolve_outcome_price,
    _sell_fill_price,
)

_PRICE_MAX_WORKERS = 8

MARKET_LOAD_FAILED = (
    "This market could not be loaded after 3 attempts — it most likely ended or was removed. "
    "If you know the outcome, use close_position_settled(position_id, won=True) for a full $1 per share payout, "
    "or won=False if your side lost (no payout)."
)


def _as_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    return {k: row[k] for k in row.keys()}


def _insert_returning_id(conn: Connection, insert_sql: str, params: tuple) -> int:
    if settings.db_backend == "postgres":
        rows = fetchall(conn, f"{insert_sql} RETURNING id", params)
        return int(rows[0]["id"])
    execute(conn, insert_sql, params)
    rid = fetchall(conn, "SELECT last_insert_rowid() AS id")
    return int(rid[0]["id"])


def _name_taken(conn: Connection, name: str, owner_id: int, exclude_id: int | None = None) -> bool:
    ph = placeholder()
    key = name.strip().lower()
    if exclude_id is None:
        rows = fetchall(
            conn,
            f"SELECT id FROM portfolios WHERE user_id = {ph} AND lower(name) = {ph}",
            (owner_id, key),
        )
    else:
        rows = fetchall(
            conn,
            f"SELECT id FROM portfolios WHERE user_id = {ph} AND lower(name) = {ph} AND id <> {ph}",
            (owner_id, key, exclude_id),
        )
    return len(rows) > 0


def _price_position(pos: dict[str, Any]) -> dict[str, Any]:
    mid = str(pos["market_id"])
    oc = str(pos["outcome"])
    market = fetch_market(mid)
    mark: float | None = None
    if market is not None:
        try:
            mark = _mark_price(market, oc)
        except ValueError:
            mark = None
    return {"position": pos, "market": market, "mark": mark}


def _price_positions(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not positions:
        return []
    if len(positions) == 1:
        return [_price_position(positions[0])]
    workers = min(_PRICE_MAX_WORKERS, len(positions))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_price_position, positions))


def _resolve_portfolio_id(conn: Connection, portfolio: int | str, access: Access) -> int:
    ph = placeholder()
    if isinstance(portfolio, int):
        pid = int(portfolio)
    else:
        s = str(portfolio).strip()
        if not s:
            raise ValueError("portfolio not found")
        if s.isdigit():
            pid = int(s)
        else:
            if access.is_admin:
                rows = fetchall(
                    conn,
                    f"SELECT id FROM portfolios WHERE lower(name) = {ph} ORDER BY id LIMIT 1",
                    (s.lower(),),
                )
            else:
                rows = fetchall(
                    conn,
                    f"SELECT id FROM portfolios WHERE lower(name) = {ph} AND user_id = {ph} ORDER BY id LIMIT 1",
                    (s.lower(), access.user_id),
                )
            if not rows:
                raise ValueError("portfolio not found")
            pid = int(rows[0]["id"])

    rows = fetchall(conn, f"SELECT id, user_id FROM portfolios WHERE id = {ph}", (pid,))
    if not rows:
        raise ValueError("portfolio not found")
    oid = int(rows[0]["user_id"])
    if not access.is_admin and oid != access.user_id:
        raise ValueError("portfolio not found")
    return int(rows[0]["id"])


class TradingService:
    def __init__(self, portfolio: int | str, access: Access) -> None:
        conn = get_connection()
        try:
            self.access = access
            self.portfolio_id = _resolve_portfolio_id(conn, portfolio, access)
        finally:
            conn.close()

    @staticmethod
    def delete_portfolio(access: Access, portfolio: int | str) -> dict[str, Any]:
        ph = placeholder()
        conn = get_connection()
        try:
            pid = _resolve_portfolio_id(conn, portfolio, access)
            execute(conn, f"DELETE FROM trades WHERE portfolio_id = {ph}", (pid,))
            execute(conn, f"DELETE FROM positions WHERE portfolio_id = {ph}", (pid,))
            execute(conn, f"DELETE FROM portfolios WHERE id = {ph}", (pid,))
            conn.commit()
            return {"ok": True, "deleted_id": pid}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def list_portfolios(access: Access) -> list[dict[str, Any]]:
        conn = get_connection()
        try:
            ph = placeholder()
            if access.is_admin:
                rows = fetchall(
                    conn,
                    "SELECT id, name, balance, created_at, user_id FROM portfolios ORDER BY id",
                )
            else:
                rows = fetchall(
                    conn,
                    f"SELECT id, name, balance, created_at, user_id FROM portfolios WHERE user_id = {ph} ORDER BY id",
                    (access.user_id,),
                )
            return [_as_dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def create_portfolio(
        access: Access,
        name: str | None = None,
        balance: float | None = None,
    ) -> dict[str, Any]:
        bal = float(settings.paper_balance if balance is None else balance)
        if bal < 0:
            raise ValueError("balance must be non-negative")
        if name is not None and not str(name).strip():
            raise ValueError("name must be non-empty when provided")
        now = datetime.now(timezone.utc).isoformat()
        ph = placeholder()
        conn = get_connection()
        try:
            oid = access.user_id
            if name is None:
                pending = "__pending__"
                if settings.db_backend == "postgres":
                    rows = fetchall(
                        conn,
                        f"INSERT INTO portfolios (user_id, name, balance, created_at) VALUES ({ph}, {ph}, {ph}, {ph}) RETURNING id",
                        (oid, pending, bal, now),
                    )
                    rid = int(rows[0]["id"])
                else:
                    execute(
                        conn,
                        f"INSERT INTO portfolios (user_id, name, balance, created_at) VALUES ({ph}, {ph}, {ph}, {ph})",
                        (oid, pending, bal, now),
                    )
                    rid = int(fetchall(conn, "SELECT last_insert_rowid() AS id")[0]["id"])
                final_name = f"portfolio{rid}"
                if _name_taken(conn, final_name, oid, exclude_id=rid):
                    raise RuntimeError("could not assign unique default portfolio name")
                execute(conn, f"UPDATE portfolios SET name = {ph} WHERE id = {ph}", (final_name, rid))
            else:
                final_name = str(name).strip()
                if _name_taken(conn, final_name, oid):
                    raise ValueError("portfolio name already exists")
                if settings.db_backend == "postgres":
                    rows = fetchall(
                        conn,
                        f"INSERT INTO portfolios (user_id, name, balance, created_at) VALUES ({ph}, {ph}, {ph}, {ph}) RETURNING id",
                        (oid, final_name, bal, now),
                    )
                    rid = int(rows[0]["id"])
                else:
                    execute(
                        conn,
                        f"INSERT INTO portfolios (user_id, name, balance, created_at) VALUES ({ph}, {ph}, {ph}, {ph})",
                        (oid, final_name, bal, now),
                    )
                    rid = int(fetchall(conn, "SELECT last_insert_rowid() AS id")[0]["id"])
            conn.commit()
            return {"id": rid, "name": final_name, "balance": bal, "created_at": now, "user_id": oid}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_portfolio(self, portfolio: int | str | None = None) -> dict[str, Any]:
        conn = get_connection()
        try:
            ph = placeholder()
            pid = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio, self.access)
            rows = fetchall(
                conn,
                f"SELECT id, name, balance FROM portfolios WHERE id = {ph}",
                (pid,),
            )
            if not rows:
                raise ValueError("portfolio not found")
            balance = float(rows[0]["balance"])
            pname = str(rows[0]["name"])
            positions = [_as_dict(p) for p in self._load_positions_rows_for(conn, pid)]
        finally:
            conn.close()

        priced = _price_positions(positions)
        total_invested = 0.0
        unrealized = 0.0
        market_value = 0.0
        for entry in priced:
            pos = entry["position"]
            cost = float(pos["cost"])
            sh = float(pos["shares"])
            total_invested += cost
            cur = entry["mark"]
            if cur is None:
                continue
            mv = sh * cur
            market_value += mv
            unrealized += mv - cost
        equity = balance + market_value
        return {
            "portfolio_id": pid,
            "name": pname,
            "balance": balance,
            "total_invested": total_invested,
            "unrealized_pnl": unrealized,
            "positions_market_value": market_value,
            "equity": equity,
        }

    def get_positions(self, portfolio: int | str | None = None) -> list[dict[str, Any]]:
        conn = get_connection()
        try:
            pid = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio, self.access)
            positions = [_as_dict(r) for r in self._load_positions_rows_for(conn, pid)]
        finally:
            conn.close()

        priced = _price_positions(positions)
        out: list[dict[str, Any]] = []
        for entry in priced:
            d = entry["position"]
            sh = float(d["shares"])
            cost = float(d["cost"])
            cur = entry["mark"]
            if cur is None:
                d["current_price"] = None
                d["market_value"] = None
                d["unrealized_pnl"] = None
                d["market_load_error"] = MARKET_LOAD_FAILED
            else:
                mv = sh * cur
                d["current_price"] = cur
                d["market_value"] = mv
                d["unrealized_pnl"] = mv - cost
                d["market_load_error"] = None
            out.append(d)
        return out

    def get_trades(self, portfolio: int | str | None = None) -> list[dict[str, Any]]:
        conn = get_connection()
        try:
            ph = placeholder()
            pid = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio, self.access)
            rows = fetchall(
                conn,
                f"SELECT * FROM trades WHERE portfolio_id = {ph} ORDER BY traded_at DESC, id DESC",
                (pid,),
            )
            return [_as_dict(r) for r in rows]
        finally:
            conn.close()

    def place_bet(
        self,
        market_id: str,
        outcome: str,
        shares: float,
        portfolio: int | str | None = None,
    ) -> dict[str, Any]:
        if shares <= 0:
            raise ValueError("shares must be positive")
        market = fetch_market(market_id)
        if not market:
            raise ValueError("market not found")
        price = _buy_fill_price(market, outcome)
        cost = shares * price
        question = market.get("question")
        slug = market.get("slug")
        mid = str(market.get("id") or market_id)
        now = datetime.now(timezone.utc).isoformat()
        ph = placeholder()
        conn = get_connection()
        try:
            pid_pf = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio, self.access)
            if settings.db_backend == "sqlite":
                conn.execute("BEGIN IMMEDIATE")
            if settings.db_backend == "postgres":
                prow = fetchall(
                    conn,
                    f"SELECT balance FROM portfolios WHERE id = {ph} FOR UPDATE",
                    (pid_pf,),
                )
            else:
                prow = fetchall(
                    conn,
                    f"SELECT balance FROM portfolios WHERE id = {ph}",
                    (pid_pf,),
                )
            if not prow:
                raise ValueError("portfolio not found")
            bal = float(prow[0]["balance"])
            if bal < cost:
                raise ValueError("insufficient balance")
            insert_trade = (
                f"INSERT INTO trades (portfolio_id, market_id, market_question, market_slug, outcome, shares, price, side, total, traded_at) "
                f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
            )
            trade_params = (
                pid_pf,
                mid,
                question,
                slug,
                outcome,
                shares,
                price,
                "buy",
                cost,
                now,
            )
            tid = _insert_returning_id(conn, insert_trade, trade_params)
            existing = fetchall(
                conn,
                f"SELECT id, shares, cost FROM positions WHERE portfolio_id = {ph} AND market_id = {ph} AND outcome = {ph}",
                (pid_pf, mid, outcome),
            )
            merged = False
            if existing:
                pos_row_id = int(existing[0]["id"])
                old_sh = float(existing[0]["shares"])
                old_cost = float(existing[0]["cost"])
                new_sh = old_sh + shares
                new_cost = old_cost + cost
                new_avg = new_cost / new_sh
                execute(
                    conn,
                    f"UPDATE positions SET shares = {ph}, avg_price = {ph}, cost = {ph}, market_question = {ph}, market_slug = {ph} WHERE id = {ph}",
                    (new_sh, new_avg, new_cost, question, slug, pos_row_id),
                )
                merged = True
                pos_id_out = pos_row_id
            else:
                insert_pos = (
                    f"INSERT INTO positions (portfolio_id, market_id, market_question, market_slug, outcome, shares, avg_price, cost, opened_at) "
                    f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
                )
                pos_params = (
                    pid_pf,
                    mid,
                    question,
                    slug,
                    outcome,
                    shares,
                    price,
                    cost,
                    now,
                )
                pos_id_out = _insert_returning_id(conn, insert_pos, pos_params)
            execute(
                conn,
                f"UPDATE portfolios SET balance = balance - {ph} WHERE id = {ph}",
                (cost, pid_pf),
            )
            conn.commit()
            return {
                "trade_id": tid,
                "position_id": pos_id_out,
                "merged": merged,
                "portfolio_id": pid_pf,
                "market_id": mid,
                "outcome": outcome,
                "shares": shares,
                "price": price,
                "cost": cost,
                "traded_at": now,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def close_position(
        self,
        position_id: int,
        shares: float | None = None,
        portfolio: int | str | None = None,
    ) -> dict[str, Any]:
        if shares is not None and shares <= 0:
            raise ValueError("shares must be positive")
        conn = get_connection()
        try:
            pid_pf = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio, self.access)
            if settings.db_backend == "sqlite":
                conn.execute("BEGIN IMMEDIATE")
            ph = placeholder()
            rows = fetchall(
                conn,
                f"SELECT * FROM positions WHERE id = {ph} AND portfolio_id = {ph}",
                (position_id, pid_pf),
            )
            if not rows:
                raise ValueError("position not found")
            pos = _as_dict(rows[0])
            mid = str(pos["market_id"])
            oc = str(pos["outcome"])
            sh = float(pos["shares"])
            cost = float(pos["cost"])
            if shares is not None and shares > sh:
                raise ValueError("cannot sell more shares than held")
            sold = sh if shares is None else float(shares)
            market = fetch_market(mid)
            if not market:
                raise ValueError(
                    "market not found after 3 attempts; if the market ended, use "
                    "close_position_settled(position_id, won=True or won=False)"
                )
            price = _sell_fill_price(market, oc)
            total = sold * price
            cost_removed = (cost / sh) * sold if sh > 0 else 0.0
            new_sh = sh - sold
            new_cost = cost - cost_removed
            now = datetime.now(timezone.utc).isoformat()
            insert_trade = (
                f"INSERT INTO trades (portfolio_id, market_id, market_question, market_slug, outcome, shares, price, side, total, traded_at) "
                f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
            )
            trade_params = (
                pid_pf,
                mid,
                pos.get("market_question"),
                pos.get("market_slug"),
                oc,
                sold,
                price,
                "sell",
                total,
                now,
            )
            tid = _insert_returning_id(conn, insert_trade, trade_params)
            if new_sh <= 1e-12:
                execute(conn, f"DELETE FROM positions WHERE id = {ph}", (position_id,))
            else:
                new_avg = new_cost / new_sh
                execute(
                    conn,
                    f"UPDATE positions SET shares = {ph}, cost = {ph}, avg_price = {ph} WHERE id = {ph}",
                    (new_sh, new_cost, new_avg, position_id),
                )
            execute(
                conn,
                f"UPDATE portfolios SET balance = balance + {ph} WHERE id = {ph}",
                (total, pid_pf),
            )
            conn.commit()
            return {
                "trade_id": tid,
                "position_id": position_id,
                "portfolio_id": pid_pf,
                "shares_sold": sold,
                "remaining_shares": max(0.0, new_sh),
                "position_closed": new_sh <= 1e-12,
                "price": price,
                "total": total,
                "traded_at": now,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def close_position_settled(
        self,
        position_id: int,
        won: bool,
        portfolio: int | str | None = None,
    ) -> dict[str, Any]:
        conn = get_connection()
        try:
            pid_pf = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio, self.access)
            if settings.db_backend == "sqlite":
                conn.execute("BEGIN IMMEDIATE")
            ph = placeholder()
            rows = fetchall(
                conn,
                f"SELECT * FROM positions WHERE id = {ph} AND portfolio_id = {ph}",
                (position_id, pid_pf),
            )
            if not rows:
                raise ValueError("position not found")
            pos = _as_dict(rows[0])
            mid = str(pos["market_id"])
            oc = str(pos["outcome"])
            sh = float(pos["shares"])
            now = datetime.now(timezone.utc).isoformat()
            if won:
                price = 1.0
                total = sh * 1.0
                side = "settle_win"
            else:
                price = 0.0
                total = 0.0
                side = "settle_loss"
            insert_trade = (
                f"INSERT INTO trades (portfolio_id, market_id, market_question, market_slug, outcome, shares, price, side, total, traded_at) "
                f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})"
            )
            trade_params = (
                pid_pf,
                mid,
                pos.get("market_question"),
                pos.get("market_slug"),
                oc,
                sh,
                price,
                side,
                total,
                now,
            )
            tid = _insert_returning_id(conn, insert_trade, trade_params)
            execute(conn, f"DELETE FROM positions WHERE id = {ph}", (position_id,))
            if won:
                execute(
                    conn,
                    f"UPDATE portfolios SET balance = balance + {ph} WHERE id = {ph}",
                    (total, pid_pf),
                )
            conn.commit()
            return {
                "trade_id": tid,
                "position_id": position_id,
                "portfolio_id": pid_pf,
                "won": won,
                "shares_settled": sh,
                "price": price,
                "total": total,
                "traded_at": now,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _load_positions_rows(self, conn: Connection) -> list[Any]:
        return self._load_positions_rows_for(conn, self.portfolio_id)

    def _load_positions_rows_for(self, conn: Connection, portfolio_id: int) -> list[Any]:
        ph = placeholder()
        return fetchall(
            conn,
            f"SELECT * FROM positions WHERE portfolio_id = {ph} ORDER BY opened_at DESC, id DESC",
            (portfolio_id,),
        )


__all__ = ["TradingService", "_buy_fill_price", "_resolve_outcome_price", "_sell_fill_price"]
