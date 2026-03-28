import json
import sqlite3
from pathlib import Path

import pytest

from polymarket.db import (
    _serialize,
    create_tables,
    get_connection,
    upsert_markets,
)


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = get_connection(Path(":memory:"))
    create_tables(c)
    return c


@pytest.fixture
def market() -> dict:
    return {
        "id": "123",
        "question": "Will X happen?",
        "conditionId": "0xabc",
        "slug": "will-x-happen",
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "volumeNum": 10000.0,
        "liquidityNum": 5000.0,
        "lastTradePrice": 0.65,
        "bestBid": 0.64,
        "bestAsk": 0.66,
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0.65", "0.35"],
        "clobTokenIds": ["token-yes", "token-no"],
        "events": [{"id": "99", "title": "Event X"}],
        "event_title": "Event X",
        "event_slug": "event-x",
    }


class TestSerialize:
    def test_list_becomes_json_string(self) -> None:
        assert _serialize(["Yes", "No"]) == '["Yes", "No"]'

    def test_dict_becomes_json_string(self) -> None:
        result = _serialize({"a": 1})
        assert json.loads(result) == {"a": 1}  # type: ignore[arg-type]

    def test_string_is_unchanged(self) -> None:
        assert _serialize("hello") == "hello"

    def test_int_is_unchanged(self) -> None:
        assert _serialize(42) == 42

    def test_float_is_unchanged(self) -> None:
        assert _serialize(3.14) == 3.14

    def test_bool_is_unchanged(self) -> None:
        assert _serialize(True) is True

    def test_none_is_unchanged(self) -> None:
        assert _serialize(None) is None

    def test_nested_list_is_serialized(self) -> None:
        result = _serialize([{"id": "1"}, {"id": "2"}])
        assert json.loads(result) == [{"id": "1"}, {"id": "2"}]  # type: ignore[arg-type]


class TestGetConnection:
    def test_returns_connection(self) -> None:
        conn = get_connection(Path(":memory:"))
        assert isinstance(conn, sqlite3.Connection)

    def test_row_factory_is_set(self) -> None:
        conn = get_connection(Path(":memory:"))
        assert conn.row_factory == sqlite3.Row

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        db_path = tmp_path / "subdir" / "test.db"
        conn = get_connection(db_path)
        assert db_path.parent.exists()
        conn.close()


class TestCreateTables:
    def test_markets_table_exists(self, conn: sqlite3.Connection) -> None:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='markets'"
        ).fetchone()
        assert result is not None

    def test_markets_table_has_primary_key(self, conn: sqlite3.Connection) -> None:
        info = conn.execute("PRAGMA table_info('markets')").fetchall()
        pk_cols = [row[1] for row in info if row[5] == 1]
        assert "id" in pk_cols

    def test_idempotent_called_twice(self, conn: sqlite3.Connection) -> None:
        create_tables(conn)
        result = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='markets'"
        ).fetchone()[0]
        assert result == 1

    def test_expected_columns_exist(self, conn: sqlite3.Connection) -> None:
        info = conn.execute("PRAGMA table_info('markets')").fetchall()
        col_names = {row[1] for row in info}
        for expected in [
            "id", "question", "conditionId", "slug", "active", "closed",
            "acceptingOrders", "volumeNum", "liquidityNum", "lastTradePrice",
            "bestBid", "bestAsk", "outcomes", "outcomePrices", "clobTokenIds",
            "events", "event_title", "event_slug",
        ]:
            assert expected in col_names, f"missing column: {expected}"


class TestUpsertMarkets:
    def test_inserts_single_market(self, conn: sqlite3.Connection, market: dict) -> None:
        count = upsert_markets(conn, [market])
        assert count == 1
        row = conn.execute("SELECT * FROM markets WHERE id='123'").fetchone()
        assert row is not None
        assert row["question"] == "Will X happen?"

    def test_returns_count_of_inserted(self, conn: sqlite3.Connection, market: dict) -> None:
        second = dict(market, id="456")
        count = upsert_markets(conn, [market, second])
        assert count == 2

    def test_list_fields_stored_as_json(self, conn: sqlite3.Connection, market: dict) -> None:
        upsert_markets(conn, [market])
        row = conn.execute("SELECT outcomes, outcomePrices, clobTokenIds, events FROM markets WHERE id='123'").fetchone()
        assert json.loads(row["outcomes"]) == ["Yes", "No"]
        assert json.loads(row["outcomePrices"]) == ["0.65", "0.35"]
        assert json.loads(row["clobTokenIds"]) == ["token-yes", "token-no"]
        assert json.loads(row["events"]) == [{"id": "99", "title": "Event X"}]

    def test_bool_stored_as_integer(self, conn: sqlite3.Connection, market: dict) -> None:
        upsert_markets(conn, [market])
        row = conn.execute("SELECT active, closed, acceptingOrders FROM markets WHERE id='123'").fetchone()
        assert row["active"] == 1
        assert row["closed"] == 0
        assert row["acceptingOrders"] == 1

    def test_replace_on_duplicate_id(self, conn: sqlite3.Connection, market: dict) -> None:
        upsert_markets(conn, [market])
        updated = dict(market, question="Updated question", lastTradePrice=0.80)
        upsert_markets(conn, [updated])
        rows = conn.execute("SELECT COUNT(*) FROM markets").fetchone()[0]
        assert rows == 1
        row = conn.execute("SELECT question, lastTradePrice FROM markets WHERE id='123'").fetchone()
        assert row["question"] == "Updated question"
        assert row["lastTradePrice"] == 0.80

    def test_unknown_fields_are_ignored(self, conn: sqlite3.Connection, market: dict) -> None:
        market_with_extra = dict(market, nonexistent_field="should_be_ignored")
        count = upsert_markets(conn, [market_with_extra])
        assert count == 1

    def test_empty_list_returns_zero(self, conn: sqlite3.Connection) -> None:
        assert upsert_markets(conn, []) == 0

    def test_none_values_stored_as_null(self, conn: sqlite3.Connection, market: dict) -> None:
        market["lastTradePrice"] = None
        upsert_markets(conn, [market])
        row = conn.execute("SELECT lastTradePrice FROM markets WHERE id='123'").fetchone()
        assert row["lastTradePrice"] is None

    def test_event_title_and_slug_stored(self, conn: sqlite3.Connection, market: dict) -> None:
        upsert_markets(conn, [market])
        row = conn.execute("SELECT event_title, event_slug FROM markets WHERE id='123'").fetchone()
        assert row["event_title"] == "Event X"
        assert row["event_slug"] == "event-x"

    def test_multiple_markets_all_inserted(self, conn: sqlite3.Connection, market: dict) -> None:
        markets = [dict(market, id=str(i), question=f"Q{i}") for i in range(10)]
        count = upsert_markets(conn, markets)
        assert count == 10
        total = conn.execute("SELECT COUNT(*) FROM markets").fetchone()[0]
        assert total == 10
