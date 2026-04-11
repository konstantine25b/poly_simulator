from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from polymarket.api.markets import fetch_market
from polymarket.config import settings
from polymarket.db import Connection, execute, fetchall, get_connection, placeholder

MARKET_LOAD_FAILED = (
    "This market could not be loaded after 3 attempts — it most likely ended or was removed. "
    "If you know the outcome, use close_position_settled(position_id, won=True) for a full $1 per share payout, "
    "or won=False if your side lost (no payout)."
)


def _as_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    return {k: row[k] for k in row.keys()}


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_outcome_price(market: dict[str, Any], outcome: str) -> float:
    label = (outcome or "").strip()
    outcomes = market.get("outcomes") or []
    prices = market.get("outcomePrices") or []
    for i, o in enumerate(outcomes):
        if str(o).strip().lower() == label.lower() and i < len(prices):
            p = _float_or_none(prices[i])
            if p is not None:
                return p
    if label.lower() == "yes" and len(prices) > 0:
        p = _float_or_none(prices[0])
        if p is not None:
            return p
    if label.lower() == "no" and len(prices) > 1:
        p = _float_or_none(prices[1])
        if p is not None:
            return p
    lt = _float_or_none(market.get("lastTradePrice"))
    if lt is not None:
        return lt
    raise ValueError("no price available for this market")


def _outcome_book_index(market: dict[str, Any], outcome: str) -> int | None:
    label = (outcome or "").strip().lower()
    outcomes = market.get("outcomes") or []
    for i, o in enumerate(outcomes):
        if str(o).strip().lower() == label:
            return i
    if label == "yes":
        return 0
    if label == "no" and len(outcomes) >= 2:
        return 1
    return None


def _buy_fill_price(market: dict[str, Any], outcome: str) -> float:
    bb = _float_or_none(market.get("bestBid"))
    ba = _float_or_none(market.get("bestAsk"))
    idx = _outcome_book_index(market, outcome)
    if idx == 0 and ba is not None:
        return ba
    if idx == 1 and len(market.get("outcomes") or []) >= 2 and bb is not None:
        return 1.0 - bb
    return _resolve_outcome_price(market, outcome)


def _sell_fill_price(market: dict[str, Any], outcome: str) -> float:
    bb = _float_or_none(market.get("bestBid"))
    ba = _float_or_none(market.get("bestAsk"))
    idx = _outcome_book_index(market, outcome)
    if idx == 0 and bb is not None:
        return bb
    if idx == 1 and len(market.get("outcomes") or []) >= 2 and ba is not None:
        return 1.0 - ba
    return _resolve_outcome_price(market, outcome)


def _mark_price(market: dict[str, Any], outcome: str) -> float:
    bb = _float_or_none(market.get("bestBid"))
    ba = _float_or_none(market.get("bestAsk"))
    idx = _outcome_book_index(market, outcome)
    if bb is not None and ba is not None:
        mid = (bb + ba) / 2.0
        if idx == 0:
            return mid
        if idx == 1 and len(market.get("outcomes") or []) >= 2:
            return 1.0 - mid
    return _resolve_outcome_price(market, outcome)


def _insert_returning_id(conn: Connection, insert_sql: str, params: tuple) -> int:
    if settings.db_backend == "postgres":
        rows = fetchall(conn, f"{insert_sql} RETURNING id", params)
        return int(rows[0]["id"])
    execute(conn, insert_sql, params)
    rid = fetchall(conn, "SELECT last_insert_rowid() AS id")
    return int(rid[0]["id"])


def _name_taken(conn: Connection, name: str, exclude_id: int | None = None) -> bool:
    ph = placeholder()
    key = name.strip().lower()
    if exclude_id is None:
        rows = fetchall(conn, f"SELECT id FROM portfolios WHERE lower(name) = {ph}", (key,))
    else:
        rows = fetchall(
            conn,
            f"SELECT id FROM portfolios WHERE lower(name) = {ph} AND id <> {ph}",
            (key, exclude_id),
        )
    return len(rows) > 0


def _resolve_portfolio_id(conn: Connection, portfolio: int | str) -> int:
    ph = placeholder()
    if isinstance(portfolio, int):
        rows = fetchall(conn, f"SELECT id FROM portfolios WHERE id = {ph}", (portfolio,))
        if not rows:
            raise ValueError("portfolio not found")
        return int(rows[0]["id"])
    s = str(portfolio).strip()
    if not s:
        raise ValueError("portfolio not found")
    if s.isdigit():
        pid = int(s)
        rows = fetchall(conn, f"SELECT id FROM portfolios WHERE id = {ph}", (pid,))
        if rows:
            return int(rows[0]["id"])
    rows = fetchall(
        conn,
        f"SELECT id FROM portfolios WHERE lower(name) = {ph} ORDER BY id LIMIT 1",
        (s.lower(),),
    )
    if not rows:
        raise ValueError("portfolio not found")
    return int(rows[0]["id"])


class TradingService:
    def __init__(self, portfolio: int | str) -> None:
        conn = get_connection()
        try:
            self.portfolio_id = _resolve_portfolio_id(conn, portfolio)
        finally:
            conn.close()

    @staticmethod
    def list_portfolios() -> list[dict[str, Any]]:
        conn = get_connection()
        try:
            rows = fetchall(conn, "SELECT id, name, balance, created_at FROM portfolios ORDER BY id")
            return [_as_dict(r) for r in rows]
        finally:
            conn.close()

    @staticmethod
    def create_portfolio(
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
            if name is None:
                pending = "__pending__"
                if settings.db_backend == "postgres":
                    rows = fetchall(
                        conn,
                        f"INSERT INTO portfolios (name, balance, created_at) VALUES ({ph}, {ph}, {ph}) RETURNING id",
                        (pending, bal, now),
                    )
                    rid = int(rows[0]["id"])
                else:
                    execute(
                        conn,
                        f"INSERT INTO portfolios (name, balance, created_at) VALUES ({ph}, {ph}, {ph})",
                        (pending, bal, now),
                    )
                    rid = int(fetchall(conn, "SELECT last_insert_rowid() AS id")[0]["id"])
                final_name = f"portfolio{rid}"
                if _name_taken(conn, final_name, exclude_id=rid):
                    raise RuntimeError("could not assign unique default portfolio name")
                execute(conn, f"UPDATE portfolios SET name = {ph} WHERE id = {ph}", (final_name, rid))
            else:
                final_name = str(name).strip()
                if _name_taken(conn, final_name):
                    raise ValueError("portfolio name already exists")
                if settings.db_backend == "postgres":
                    rows = fetchall(
                        conn,
                        f"INSERT INTO portfolios (name, balance, created_at) VALUES ({ph}, {ph}, {ph}) RETURNING id",
                        (final_name, bal, now),
                    )
                    rid = int(rows[0]["id"])
                else:
                    execute(
                        conn,
                        f"INSERT INTO portfolios (name, balance, created_at) VALUES ({ph}, {ph}, {ph})",
                        (final_name, bal, now),
                    )
                    rid = int(fetchall(conn, "SELECT last_insert_rowid() AS id")[0]["id"])
            conn.commit()
            return {"id": rid, "name": final_name, "balance": bal, "created_at": now}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_portfolio(self, portfolio: int | str | None = None) -> dict[str, Any]:
        conn = get_connection()
        try:
            ph = placeholder()
            pid = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio)
            rows = fetchall(
                conn,
                f"SELECT id, name, balance FROM portfolios WHERE id = {ph}",
                (pid,),
            )
            if not rows:
                raise ValueError("portfolio not found")
            balance = float(rows[0]["balance"])
            pname = str(rows[0]["name"])
            positions = self._load_positions_rows_for(conn, pid)
            total_invested = 0.0
            unrealized = 0.0
            market_value = 0.0
            for pos in positions:
                cost = float(pos["cost"])
                sh = float(pos["shares"])
                total_invested += cost
                mid = str(pos["market_id"])
                oc = str(pos["outcome"])
                m = fetch_market(mid)
                if not m:
                    continue
                try:
                    cur = _mark_price(m, oc)
                except ValueError:
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
        finally:
            conn.close()

    def get_positions(self, portfolio: int | str | None = None) -> list[dict[str, Any]]:
        conn = get_connection()
        try:
            pid = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio)
            rows = self._load_positions_rows_for(conn, pid)
            out: list[dict[str, Any]] = []
            for pos in rows:
                d = _as_dict(pos)
                mid = str(d["market_id"])
                oc = str(d["outcome"])
                sh = float(d["shares"])
                cost = float(d["cost"])
                m = fetch_market(mid)
                if not m:
                    d["current_price"] = None
                    d["market_value"] = None
                    d["unrealized_pnl"] = None
                    d["market_load_error"] = MARKET_LOAD_FAILED
                    out.append(d)
                    continue
                try:
                    cur = _mark_price(m, oc)
                except ValueError:
                    d["current_price"] = None
                    d["market_value"] = None
                    d["unrealized_pnl"] = None
                    d["market_load_error"] = MARKET_LOAD_FAILED
                    out.append(d)
                    continue
                mv = sh * cur
                d["current_price"] = cur
                d["market_value"] = mv
                d["unrealized_pnl"] = mv - cost
                d["market_load_error"] = None
                out.append(d)
            return out
        finally:
            conn.close()

    def get_trades(self, portfolio: int | str | None = None) -> list[dict[str, Any]]:
        conn = get_connection()
        try:
            ph = placeholder()
            pid = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio)
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
            pid_pf = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio)
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
            pid_pf = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio)
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
            pid_pf = self.portfolio_id if portfolio is None else _resolve_portfolio_id(conn, portfolio)
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
