from __future__ import annotations

from pathlib import Path

import pytest

from polymarket import db
from polymarket.db import create_tables, execute, fetchall, get_connection, placeholder
from polymarket.trading.service import (
    TradingService,
    _buy_fill_price,
    _resolve_outcome_price,
    _sell_fill_price,
)


@pytest.fixture(autouse=True)
def force_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db.settings, "db_backend", "sqlite")


@pytest.fixture
def paper_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "paper.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    conn = get_connection(path)
    create_tables(conn)
    conn.close()
    return path


@pytest.fixture
def api_market() -> dict:
    return {
        "id": "m1",
        "question": "Test market?",
        "slug": "test-market",
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.5", "0.5"],
        "lastTradePrice": 0.5,
        "bestBid": 0.48,
        "bestAsk": 0.52,
    }


class TestBookFillPrices:
    def test_yes_buy_ask_sell_bid(self, api_market: dict) -> None:
        assert _buy_fill_price(dict(api_market), "Yes") == pytest.approx(0.52)
        assert _sell_fill_price(dict(api_market), "Yes") == pytest.approx(0.48)

    def test_no_uses_inverse_book(self) -> None:
        m = {
            "outcomes": ["Yes", "No"],
            "outcomePrices": ["0.5", "0.5"],
            "bestBid": 0.48,
            "bestAsk": 0.52,
        }
        assert _buy_fill_price(m, "No") == pytest.approx(1.0 - 0.48)
        assert _sell_fill_price(m, "No") == pytest.approx(1.0 - 0.52)


class TestResolveOutcomePrice:
    def test_matches_outcome_index(self) -> None:
        m = {
            "outcomes": ["Up", "Down"],
            "outcomePrices": ["0.2", "0.8"],
            "lastTradePrice": 0.5,
        }
        assert _resolve_outcome_price(m, "Down") == pytest.approx(0.8)

    def test_yes_no_indices(self) -> None:
        m = {"outcomes": ["Yes", "No"], "outcomePrices": ["0.65", "0.35"]}
        assert _resolve_outcome_price(m, "Yes") == pytest.approx(0.65)
        assert _resolve_outcome_price(m, "No") == pytest.approx(0.35)

    def test_case_insensitive_outcome(self) -> None:
        m = {"outcomes": ["Yes", "No"], "outcomePrices": ["0.1", "0.9"]}
        assert _resolve_outcome_price(m, "yes") == pytest.approx(0.1)

    def test_falls_back_to_last_trade(self) -> None:
        m = {"outcomes": [], "outcomePrices": [], "lastTradePrice": 0.42}
        assert _resolve_outcome_price(m, "Yes") == pytest.approx(0.42)

    def test_raises_when_no_price(self) -> None:
        m: dict = {"outcomes": [], "outcomePrices": []}
        with pytest.raises(ValueError, match="no price"):
            _resolve_outcome_price(m, "Yes")


class TestTradingService:
    def test_place_bet_and_close_round_trip(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_fetch(_q: str) -> dict | None:
            return dict(api_market)

        monkeypatch.setattr("polymarket.trading.service.fetch_market", fake_fetch)
        svc = TradingService(1)
        before = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0][
                "balance"
            ]
        )
        placed = svc.place_bet("test-market", "Yes", 10.0)
        assert placed["price"] == pytest.approx(0.52)
        assert placed["cost"] == pytest.approx(5.2)
        assert placed.get("merged") is False
        after_buy = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0][
                "balance"
            ]
        )
        assert after_buy == pytest.approx(before - 5.2)
        rows = fetchall(get_connection(paper_db), "SELECT COUNT(*) AS c FROM positions")
        assert int(rows[0]["c"]) == 1
        closed = svc.close_position(int(placed["position_id"]))
        assert closed["price"] == pytest.approx(0.48)
        assert closed["total"] == pytest.approx(4.8)
        assert closed["position_closed"] is True
        after_sell = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0][
                "balance"
            ]
        )
        assert after_sell == pytest.approx(before - 0.4)
        rows = fetchall(get_connection(paper_db), "SELECT COUNT(*) AS c FROM positions")
        assert int(rows[0]["c"]) == 0
        trades = svc.get_trades()
        assert len(trades) == 2
        assert trades[0]["side"] == "sell"
        assert trades[1]["side"] == "buy"

    def test_place_bet_insufficient_balance(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        conn = get_connection(paper_db)
        ph = placeholder()
        execute(conn, f"UPDATE portfolios SET balance = {ph} WHERE id = 1", (1.0,))
        conn.commit()
        conn.close()

        def fake_fetch(_q: str) -> dict | None:
            return dict(api_market)

        monkeypatch.setattr("polymarket.trading.service.fetch_market", fake_fetch)
        svc = TradingService(1)
        with pytest.raises(ValueError, match="insufficient balance"):
            svc.place_bet("m1", "Yes", 10.0)

    def test_place_bet_non_positive_shares(self, paper_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: {"id": "x"})
        svc = TradingService(1)
        with pytest.raises(ValueError, match="shares must be positive"):
            svc.place_bet("m1", "Yes", 0.0)

    def test_place_bet_market_not_found(self, paper_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: None)
        svc = TradingService(1)
        with pytest.raises(ValueError, match="market not found"):
            svc.place_bet("missing", "Yes", 1.0)

    def test_close_unknown_position(self, paper_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: None)
        svc = TradingService(1)
        with pytest.raises(ValueError, match="position not found"):
            svc.close_position(99999)

    def test_get_portfolio_unrealized_moves_with_price(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[int] = []

        def fake_fetch(_q: str) -> dict | None:
            calls.append(1)
            m = dict(api_market)
            if len(calls) > 1:
                m["bestBid"] = 0.49
                m["bestAsk"] = 0.53
            return m

        monkeypatch.setattr("polymarket.trading.service.fetch_market", fake_fetch)
        svc = TradingService(1)
        svc.place_bet("m1", "Yes", 10.0)
        pf = svc.get_portfolio()
        assert pf["total_invested"] == pytest.approx(5.2)
        assert pf["unrealized_pnl"] == pytest.approx(-0.1)
        assert pf["equity"] == pytest.approx(999.9)

    def test_get_positions_enriched(self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        svc.place_bet("m1", "Yes", 4.0)
        pos = svc.get_positions()
        assert len(pos) == 1
        assert pos[0]["current_price"] == pytest.approx(0.5)
        assert pos[0]["market_value"] == pytest.approx(2.0)
        assert pos[0]["unrealized_pnl"] == pytest.approx(-0.08)
        assert pos[0].get("market_load_error") is None

    def test_get_positions_market_missing_message(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        svc.place_bet("m1", "Yes", 4.0)
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: None)
        pos = svc.get_positions()
        assert len(pos) == 1
        assert pos[0]["current_price"] is None
        assert pos[0]["market_load_error"] is not None
        assert "3 attempts" in (pos[0]["market_load_error"] or "")

    def test_get_positions_no_price_message(
        self, paper_db: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "polymarket.trading.service.fetch_market",
            lambda _q: {"id": "m1", "outcomes": [], "outcomePrices": []},
        )
        conn = get_connection(paper_db)
        ph = placeholder()
        now = "2020-01-01T00:00:00+00:00"
        execute(
            conn,
            f"INSERT INTO positions (portfolio_id, market_id, market_question, market_slug, outcome, shares, avg_price, cost, opened_at) "
            f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})",
            (1, "m1", "Q", None, "Yes", 1.0, 0.5, 0.5, now),
        )
        conn.commit()
        conn.close()
        pos = TradingService(1).get_positions()
        assert pos[0]["market_load_error"] is not None

    def test_get_trades_empty(self, paper_db: Path) -> None:
        svc = TradingService(1)
        assert svc.get_trades() == []

    def test_seed_portfolio_default_name(self, paper_db: Path) -> None:
        row = fetchall(get_connection(paper_db), "SELECT id, name, balance FROM portfolios WHERE id = 1")[0]
        assert row["name"] == "portfolio1"
        assert float(row["balance"]) == pytest.approx(float(db.settings.paper_balance))

    def test_create_portfolio_custom(self, paper_db: Path) -> None:
        p = TradingService.create_portfolio(name="Alpha", balance=500.0)
        assert p["name"] == "Alpha"
        assert p["balance"] == pytest.approx(500.0)
        row = fetchall(
            get_connection(paper_db),
            "SELECT name, balance FROM portfolios WHERE id = ?",
            (p["id"],),
        )[0]
        assert row["name"] == "Alpha"

    def test_create_portfolio_duplicate_name_raises(self, paper_db: Path) -> None:
        TradingService.create_portfolio(name="Dup", balance=1.0)
        with pytest.raises(ValueError, match="portfolio name already exists"):
            TradingService.create_portfolio(name="dup", balance=2.0)

    def test_init_and_get_portfolio_by_name(self, paper_db: Path) -> None:
        svc = TradingService("portfolio1")
        assert svc.portfolio_id == 1
        assert svc.get_portfolio()["name"] == "portfolio1"
        assert svc.get_portfolio(1)["portfolio_id"] == 1
        assert svc.get_portfolio("portfolio1")["portfolio_id"] == 1

    def test_create_portfolio_auto_name(self, paper_db: Path) -> None:
        p = TradingService.create_portfolio()
        assert p["name"] == f"portfolio{p['id']}"

    def test_two_portfolios_isolated(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        p2 = TradingService.create_portfolio(name="Second", balance=100.0)

        def fake_fetch(_q: str) -> dict | None:
            return dict(api_market)

        monkeypatch.setattr("polymarket.trading.service.fetch_market", fake_fetch)
        svc2 = TradingService(p2["id"])
        svc2.place_bet("m1", "Yes", 10.0)
        b1 = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        assert b1 == pytest.approx(1000.0)
        b2 = float(
            fetchall(
                get_connection(paper_db),
                "SELECT balance FROM portfolios WHERE id = ?",
                (p2["id"],),
            )[0]["balance"]
        )
        assert b2 == pytest.approx(94.8)
        assert len(TradingService(1).get_trades()) == 0
        assert len(svc2.get_trades()) == 1

    def test_close_position_wrong_portfolio(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_fetch(_q: str) -> dict | None:
            return dict(api_market)

        monkeypatch.setattr("polymarket.trading.service.fetch_market", fake_fetch)
        placed = TradingService(1).place_bet("m1", "Yes", 10.0)
        pid = int(placed["position_id"])
        p2 = TradingService.create_portfolio(balance=1000.0)
        with pytest.raises(ValueError, match="position not found"):
            TradingService(p2["id"]).close_position(pid)
        with pytest.raises(ValueError, match="position not found"):
            TradingService(1).close_position(pid, portfolio=p2["id"])

    def test_place_bet_and_close_with_portfolio_override(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_fetch(_q: str) -> dict | None:
            return dict(api_market)

        monkeypatch.setattr("polymarket.trading.service.fetch_market", fake_fetch)
        p2 = TradingService.create_portfolio(name="Alt", balance=500.0)
        svc = TradingService(1)
        placed = svc.place_bet("m1", "Yes", 10.0, portfolio=p2["id"])
        assert placed["portfolio_id"] == p2["id"]
        b1 = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        assert b1 == pytest.approx(1000.0)
        b2 = float(
            fetchall(
                get_connection(paper_db),
                "SELECT balance FROM portfolios WHERE id = ?",
                (p2["id"],),
            )[0]["balance"]
        )
        assert b2 == pytest.approx(500.0 - 5.2)
        svc.close_position(int(placed["position_id"]), portfolio=p2["id"])
        b2_after = float(
            fetchall(
                get_connection(paper_db),
                "SELECT balance FROM portfolios WHERE id = ?",
                (p2["id"],),
            )[0]["balance"]
        )
        assert b2_after == pytest.approx(500.0 - 0.4)

    def test_merge_same_market_outcome(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[int] = []

        def fake_fetch(_q: str) -> dict | None:
            calls.append(1)
            m = dict(api_market)
            if len(calls) >= 2:
                m["bestBid"] = 0.40
                m["bestAsk"] = 0.44
            return m

        monkeypatch.setattr("polymarket.trading.service.fetch_market", fake_fetch)
        svc = TradingService(1)
        a = svc.place_bet("m1", "Yes", 10.0)
        b = svc.place_bet("m1", "Yes", 10.0)
        assert a["position_id"] == b["position_id"]
        assert b["merged"] is True
        assert a["price"] == pytest.approx(0.52)
        assert b["price"] == pytest.approx(0.44)
        row = fetchall(
            get_connection(paper_db),
            "SELECT shares, cost, avg_price FROM positions WHERE id = ?",
            (a["position_id"],),
        )[0]
        assert float(row["shares"]) == pytest.approx(20.0)
        assert float(row["cost"]) == pytest.approx(5.2 + 4.4)
        assert float(row["avg_price"]) == pytest.approx((5.2 + 4.4) / 20.0)
        assert len(fetchall(get_connection(paper_db), "SELECT id FROM positions")) == 1

    def test_partial_close_then_full(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        before = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        placed = svc.place_bet("m1", "Yes", 20.0)
        pid = int(placed["position_id"])
        after_buy = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        assert after_buy == pytest.approx(before - 20.0 * 0.52)
        p1 = svc.close_position(pid, 7.0)
        assert p1["shares_sold"] == pytest.approx(7.0)
        assert p1["position_closed"] is False
        assert p1["price"] == pytest.approx(0.48)
        row = fetchall(get_connection(paper_db), "SELECT shares, cost FROM positions WHERE id = ?", (pid,))[0]
        assert float(row["shares"]) == pytest.approx(13.0)
        p2 = svc.close_position(pid)
        assert p2["position_closed"] is True
        assert p2["shares_sold"] == pytest.approx(13.0)
        after = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        assert after == pytest.approx(before - 20.0 * 0.52 + 7.0 * 0.48 + 13.0 * 0.48)

    def test_close_more_shares_than_held_raises(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        placed = svc.place_bet("m1", "Yes", 3.0)
        with pytest.raises(ValueError, match="cannot sell more"):
            svc.close_position(int(placed["position_id"]), 10.0)

    def test_close_non_positive_shares_raises(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        placed = svc.place_bet("m1", "Yes", 2.0)
        with pytest.raises(ValueError, match="shares must be positive"):
            svc.close_position(int(placed["position_id"]), 0.0)

    def test_close_position_market_missing_suggests_settle(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        placed = svc.place_bet("m1", "Yes", 10.0)
        pid = int(placed["position_id"])
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: None)
        with pytest.raises(ValueError, match="close_position_settled"):
            svc.close_position(pid)

    def test_close_position_settled_win(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        before = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        placed = svc.place_bet("m1", "Yes", 10.0)
        pid = int(placed["position_id"])
        after_buy = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        out = svc.close_position_settled(pid, won=True)
        assert out["won"] is True
        assert out["total"] == pytest.approx(10.0)
        assert out["price"] == pytest.approx(1.0)
        after = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        assert after == pytest.approx(after_buy + 10.0)
        assert after == pytest.approx(before - 10.0 * 0.52 + 10.0)
        trades = svc.get_trades()
        assert trades[0]["side"] == "settle_win"
        assert int(fetchall(get_connection(paper_db), "SELECT COUNT(*) AS c FROM positions")[0]["c"]) == 0

    def test_close_position_settled_loss(
        self, paper_db: Path, api_market: dict, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("polymarket.trading.service.fetch_market", lambda _q: dict(api_market))
        svc = TradingService(1)
        before = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        placed = svc.place_bet("m1", "Yes", 10.0)
        pid = int(placed["position_id"])
        after_buy = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        out = svc.close_position_settled(pid, won=False)
        assert out["won"] is False
        assert out["total"] == pytest.approx(0.0)
        assert out["price"] == pytest.approx(0.0)
        after = float(
            fetchall(get_connection(paper_db), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
        )
        assert after == pytest.approx(after_buy)
        assert after == pytest.approx(before - 10.0 * 0.52)
        trades = svc.get_trades()
        assert trades[0]["side"] == "settle_loss"


@pytest.mark.integration
def test_live_spain_world_cup_slug_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    slug = "will-spain-win-the-2026-fifa-world-cup-963"
    path = tmp_path / "integration.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    conn = get_connection(path)
    create_tables(conn)
    conn.close()
    svc = TradingService(1)
    from polymarket.api.markets import fetch_market as live_fetch

    m = live_fetch(slug)
    assert m is not None
    out = str((m.get("outcomes") or ["Yes"])[0])
    placed = svc.place_bet(slug, out, 5.0)
    assert placed["cost"] > 0
    svc.close_position(int(placed["position_id"]))
    bal = float(
        fetchall(get_connection(path), "SELECT balance FROM portfolios WHERE id = 1")[0]["balance"]
    )
    assert bal == pytest.approx(float(db.settings.paper_balance), abs=2.0)
