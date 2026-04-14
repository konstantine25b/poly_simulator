from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from polymarket import db
from polymarket.catalog import queries
from polymarket.db import create_tables, get_connection, upsert_markets


@pytest.fixture(autouse=True)
def force_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db.settings, "db_backend", "sqlite")


@pytest.fixture
def catalog_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "catalog_queries.db"
    monkeypatch.setattr(db, "DB_PATH", path)
    conn = get_connection()
    create_tables(conn)
    conn.close()
    return path


def _seed_two_markets(conn) -> None:
    upsert_markets(
        conn,
        [
            {
                "id": "m_alpha",
                "question": "Alpha unique question text",
                "slug": "alpha-slug",
                "active": 1,
                "closed": 0,
                "createdAt": "2020-01-02T00:00:00Z",
                "outcomes": '["Yes", "No"]',
            },
            {
                "id": "m_beta",
                "question": "Beta other",
                "slug": "beta-slug",
                "active": 0,
                "closed": 1,
                "createdAt": "2020-01-01T00:00:00Z",
                "outcomes": '["A", "B"]',
            },
        ],
    )


class TestListMarketsFromDb:
    def test_empty(self, catalog_db: Path) -> None:
        out = queries.list_markets_from_db()
        assert out["total"] == 0
        assert out["items"] == []
        assert out["limit"] == 100
        assert out["offset"] == 0

    def test_filters_active_and_search(self, catalog_db: Path) -> None:
        conn = get_connection()
        _seed_two_markets(conn)
        conn.close()
        out = queries.list_markets_from_db(active=True, closed=False, q="Alpha unique")
        assert out["total"] == 1
        assert len(out["items"]) == 1
        row = out["items"][0]
        assert row["id"] == "m_alpha"
        assert row["outcomes"] == ["Yes", "No"]

    def test_pagination_and_limit_clamp(self, catalog_db: Path) -> None:
        conn = get_connection()
        _seed_two_markets(conn)
        conn.close()
        first = queries.list_markets_from_db(limit=1, offset=0)
        assert first["total"] == 2
        assert first["limit"] == 1
        assert len(first["items"]) == 1
        second = queries.list_markets_from_db(limit=1, offset=1)
        assert second["total"] == 2
        assert len(second["items"]) == 1
        assert first["items"][0]["id"] != second["items"][0]["id"]
        huge = queries.list_markets_from_db(limit=9999, offset=0)
        assert huge["limit"] == 500


class TestMarketFromDb:
    def test_by_id_and_slug(self, catalog_db: Path) -> None:
        conn = get_connection()
        upsert_markets(
            conn,
            [
                {
                    "id": "m_one",
                    "question": "Q?",
                    "slug": "one-slug",
                    "active": 1,
                    "closed": 0,
                    "outcomes": '["Y", "N"]',
                }
            ],
        )
        conn.close()
        by_id = queries.market_from_db("m_one")
        assert by_id is not None
        assert by_id["slug"] == "one-slug"
        assert by_id["outcomes"] == ["Y", "N"]
        by_slug = queries.market_from_db("one-slug")
        assert by_slug is not None
        assert by_slug["id"] == "m_one"

    def test_missing_returns_none(self, catalog_db: Path) -> None:
        assert queries.market_from_db("nope") is None


class TestResolveMarketLiveOrDb:
    def test_live_hit_not_stale(self, catalog_db: Path) -> None:
        conn = get_connection()
        _seed_two_markets(conn)
        conn.close()
        live = {"id": "live-1", "question": "Live", "slug": "live-slug"}

        def fake_fetch(_q: str):
            return live

        with patch.object(queries, "fetch_market", fake_fetch):
            m, stale = queries.resolve_market_live_or_db("any")
        assert m == live
        assert stale is False

    def test_live_none_uses_cache_stale_true(self, catalog_db: Path) -> None:
        conn = get_connection()
        _seed_two_markets(conn)
        conn.close()

        with patch.object(queries, "fetch_market", lambda _q: None):
            m, stale = queries.resolve_market_live_or_db("alpha-slug")
        assert m is not None
        assert m["id"] == "m_alpha"
        assert stale is True

    def test_live_exception_falls_back_to_db(self, catalog_db: Path) -> None:
        conn = get_connection()
        _seed_two_markets(conn)
        conn.close()

        def boom(_q: str):
            raise RuntimeError("network down")

        with patch.object(queries, "fetch_market", boom):
            m, stale = queries.resolve_market_live_or_db("m_beta")
        assert m is not None
        assert m["id"] == "m_beta"
        assert stale is True

    def test_live_empty_no_cache_returns_none(self, catalog_db: Path) -> None:

        with patch.object(queries, "fetch_market", lambda _q: None):
            m, stale = queries.resolve_market_live_or_db("ghost")
        assert m is None
        assert stale is False
