from __future__ import annotations

from pathlib import Path

import pytest

from polymarket import db
from polymarket.auth import Access
from polymarket.db import create_tables, fetchall, get_connection
from polymarket.trading.service import TradingService

U1 = Access(1, False)


@pytest.mark.integration
def test_live_spain_world_cup_slug_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    slug = "will-spain-win-the-2026-fifa-world-cup-963"
    path = tmp_path / "integration.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    conn = get_connection(path)
    create_tables(conn)
    conn.close()
    svc = TradingService(1, U1)
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
