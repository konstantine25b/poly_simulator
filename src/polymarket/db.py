from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Union

from polymarket.config import settings

try:
    import psycopg2
    import psycopg2.extras

    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False

DB_PATH = Path(__file__).parent.parent.parent / "data" / "markets.db"

# Works in both SQLite and PostgreSQL — INTEGER/REAL/TEXT/BOOLEAN are all valid in both
CREATE_MARKETS_TABLE = """
CREATE TABLE IF NOT EXISTS markets (
    id                          TEXT PRIMARY KEY,
    question                    TEXT,
    conditionId                 TEXT,
    slug                        TEXT,
    description                 TEXT,
    resolutionSource            TEXT,
    image                       TEXT,
    icon                        TEXT,
    category                    TEXT,
    marketType                  TEXT,
    questionID                  TEXT,
    marketMakerAddress          TEXT,
    resolvedBy                  TEXT,
    submitted_by                TEXT,
    groupItemTitle              TEXT,
    groupItemThreshold          TEXT,
    umaBond                     TEXT,
    umaReward                   TEXT,
    feeType                     TEXT,

    startDate                   TEXT,
    endDate                     TEXT,
    startDateIso                TEXT,
    endDateIso                  TEXT,
    createdAt                   TEXT,
    updatedAt                   TEXT,
    closedTime                  TEXT,
    acceptingOrdersTimestamp    TEXT,

    active                      INTEGER,
    closed                      INTEGER,
    archived                    INTEGER,
    restricted                  INTEGER,
    featured                    INTEGER,
    new                         INTEGER,
    enableOrderBook             INTEGER,
    acceptingOrders             INTEGER,
    negRisk                     INTEGER,
    approved                    INTEGER,
    cyom                        INTEGER,
    ready                       INTEGER,
    funded                      INTEGER,
    fpmmLive                    INTEGER,
    automaticallyActive         INTEGER,
    clearBookOnStart            INTEGER,
    manualActivation            INTEGER,
    negRiskOther                INTEGER,
    pendingDeployment           INTEGER,
    deploying                   INTEGER,
    rfqEnabled                  INTEGER,
    hasReviewedDates            INTEGER,
    holdingRewardsEnabled       INTEGER,
    feesEnabled                 INTEGER,
    requiresTranslation         INTEGER,
    pagerDutyNotificationEnabled INTEGER,

    volumeNum                   REAL,
    liquidityNum                REAL,
    volume24hr                  REAL,
    volume1wk                   REAL,
    volume1mo                   REAL,
    volume1yr                   REAL,
    volumeClob                  REAL,
    liquidityClob               REAL,
    volume24hrClob              REAL,
    volume1wkClob               REAL,
    volume1moClob               REAL,
    volume1yrClob               REAL,
    lastTradePrice              REAL,
    bestBid                     REAL,
    bestAsk                     REAL,
    spread                      REAL,
    competitive                 REAL,
    oneDayPriceChange           REAL,
    oneHourPriceChange          REAL,
    oneWeekPriceChange          REAL,
    oneMonthPriceChange         REAL,
    oneYearPriceChange          REAL,
    orderPriceMinTickSize       REAL,
    orderMinSize                REAL,
    rewardsMinSize              REAL,
    rewardsMaxSpread            REAL,

    outcomes                    TEXT,
    outcomePrices               TEXT,
    clobTokenIds                TEXT,
    events                      TEXT,
    clobRewards                 TEXT,
    umaResolutionStatuses       TEXT,

    event_title                 TEXT,
    event_slug                  TEXT,
    tags                        TEXT
)
"""


CREATE_PORTFOLIOS_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS portfolios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    balance     REAL    NOT NULL,
    created_at  TEXT    NOT NULL
)
"""

CREATE_PORTFOLIOS_TABLE_PG = """
CREATE TABLE IF NOT EXISTS portfolios (
    id          SERIAL  PRIMARY KEY,
    name        TEXT    NOT NULL,
    balance     DOUBLE PRECISION NOT NULL,
    created_at  TEXT    NOT NULL
)
"""

CREATE_POSITIONS_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS positions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    INTEGER NOT NULL,
    market_id       TEXT    NOT NULL,
    market_question TEXT,
    market_slug     TEXT,
    outcome         TEXT    NOT NULL,
    shares          REAL    NOT NULL,
    avg_price       REAL    NOT NULL,
    cost            REAL    NOT NULL,
    opened_at       TEXT    NOT NULL
)
"""

CREATE_POSITIONS_TABLE_PG = """
CREATE TABLE IF NOT EXISTS positions (
    id              SERIAL  PRIMARY KEY,
    portfolio_id  INTEGER NOT NULL,
    market_id       TEXT    NOT NULL,
    market_question TEXT,
    market_slug     TEXT,
    outcome         TEXT    NOT NULL,
    shares          REAL    NOT NULL,
    avg_price       REAL    NOT NULL,
    cost            REAL    NOT NULL,
    opened_at       TEXT    NOT NULL
)
"""

CREATE_TRADES_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id    INTEGER NOT NULL,
    market_id       TEXT    NOT NULL,
    market_question TEXT,
    market_slug     TEXT,
    outcome         TEXT    NOT NULL,
    shares          REAL    NOT NULL,
    price           REAL    NOT NULL,
    side            TEXT    NOT NULL,
    total           REAL    NOT NULL,
    traded_at       TEXT    NOT NULL
)
"""

CREATE_TRADES_TABLE_PG = """
CREATE TABLE IF NOT EXISTS trades (
    id              SERIAL  PRIMARY KEY,
    portfolio_id  INTEGER NOT NULL,
    market_id       TEXT    NOT NULL,
    market_question TEXT,
    market_slug     TEXT,
    outcome         TEXT    NOT NULL,
    shares          REAL    NOT NULL,
    price           REAL    NOT NULL,
    side            TEXT    NOT NULL,
    total           REAL    NOT NULL,
    traded_at       TEXT    NOT NULL
)
"""

Connection = Union[sqlite3.Connection, Any]


def get_connection(db_path: Path | None = None) -> Connection:
    if settings.db_backend == "postgres":
        if not _PG_AVAILABLE:
            raise RuntimeError("psycopg2 not installed — run: pip install psycopg2-binary")
        conn = psycopg2.connect(
            settings.postgres_dsn,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        return conn

    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


# ── Schema creation & migration ─────────────────────────────────────────────────

def create_tables(conn: Connection) -> None:
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        for ddl in (
            CREATE_MARKETS_TABLE,
            CREATE_PORTFOLIOS_TABLE_PG,
            CREATE_POSITIONS_TABLE_PG,
            CREATE_TRADES_TABLE_PG,
        ):
            cur.execute(ddl)
        cur.close()
        _migrate_pg(conn)
    else:
        for ddl in (
            CREATE_MARKETS_TABLE,
            CREATE_PORTFOLIOS_TABLE_SQLITE,
            CREATE_POSITIONS_TABLE_SQLITE,
            CREATE_TRADES_TABLE_SQLITE,
        ):
            conn.execute(ddl)
        _migrate_sqlite(conn)
    _migrate_legacy_portfolio_table(conn)
    _seed_portfolio(conn)
    conn.commit()


def _seed_portfolio(conn: Connection) -> None:
    from datetime import datetime, timezone

    ph = placeholder()
    rows = fetchall(conn, "SELECT COUNT(*) AS c FROM portfolios")
    if int(rows[0]["c"]) > 0:
        return
    now = datetime.now(timezone.utc).isoformat()
    if settings.db_backend == "postgres":
        ins = f"INSERT INTO portfolios (name, balance, created_at) VALUES ({ph}, {ph}, {ph}) RETURNING id"
        rid = int(fetchall(conn, ins, ("__pending__", settings.paper_balance, now))[0]["id"])
        execute(conn, f"UPDATE portfolios SET name = {ph} WHERE id = {ph}", (f"portfolio{rid}", rid))
    else:
        execute(conn, f"INSERT INTO portfolios (name, balance, created_at) VALUES ({ph}, {ph}, {ph})", ("__pending__", settings.paper_balance, now))
        rid = int(fetchall(conn, "SELECT last_insert_rowid() AS id")[0]["id"])
        execute(conn, f"UPDATE portfolios SET name = {ph} WHERE id = {ph}", (f"portfolio{rid}", rid))


def _migrate_sqlite(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info('markets')").fetchall()}
    new_columns = {"tags": "TEXT", "event_title": "TEXT", "event_slug": "TEXT"}
    for col, col_type in new_columns.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE markets ADD COLUMN {col} {col_type}")
    for table in ("positions", "trades"):
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info('{table}')").fetchall()}
        if cols and "market_slug" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN market_slug TEXT")
    _migrate_portfolio_id_columns_sqlite(conn)


def _migrate_portfolio_id_columns_sqlite(conn: sqlite3.Connection) -> None:
    for table in ("positions", "trades"):
        cols = {row[1] for row in conn.execute(f"PRAGMA table_info('{table}')").fetchall()}
        if cols and "portfolio_id" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN portfolio_id INTEGER")
            conn.execute(f"UPDATE {table} SET portfolio_id = 1 WHERE portfolio_id IS NULL")


def _migrate_legacy_portfolio_table(conn: Connection) -> None:
    from datetime import datetime, timezone

    ph = placeholder()
    now = datetime.now(timezone.utc).isoformat()
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'portfolio'"
        )
        legacy = cur.fetchone() is not None
        if not legacy:
            cur.close()
            return
        cur.execute("SELECT COUNT(*) AS c FROM portfolios")
        nport = int(cur.fetchone()["c"])
        if nport == 0:
            cur.execute("SELECT balance, created_at FROM portfolio WHERE id = 1 LIMIT 1")
            row = cur.fetchone()
            if row:
                bal = float(row["balance"])
                created = row["created_at"] or now
            else:
                bal = float(settings.paper_balance)
                created = now
            cur.execute(
                "INSERT INTO portfolios (name, balance, created_at) VALUES (%s, %s, %s) RETURNING id",
                ("portfolio1", bal, created),
            )
            pid = int(cur.fetchone()["id"])
            cur.execute(
                "UPDATE positions SET portfolio_id = %s WHERE portfolio_id IS NULL OR portfolio_id = 1",
                (pid,),
            )
            cur.execute(
                "UPDATE trades SET portfolio_id = %s WHERE portfolio_id IS NULL OR portfolio_id = 1",
                (pid,),
            )
        cur.execute("DROP TABLE IF EXISTS portfolio CASCADE")
        cur.close()
        return

    legacy_exists = (
        conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='portfolio'"
        ).fetchone()
        is not None
    )
    if not legacy_exists:
        return
    nport = int(conn.execute("SELECT COUNT(*) FROM portfolios").fetchone()[0])
    if nport == 0:
        row = conn.execute("SELECT balance, created_at FROM portfolio WHERE id = 1").fetchone()
        if row:
            bal = float(row["balance"])
            created = row["created_at"] or now
        else:
            bal = float(settings.paper_balance)
            created = now
        execute(
            conn,
            f"INSERT INTO portfolios (name, balance, created_at) VALUES ({ph}, {ph}, {ph})",
            ("portfolio1", bal, created),
        )
        pid = int(fetchall(conn, "SELECT last_insert_rowid() AS id")[0]["id"])
        execute(
            conn,
            f"UPDATE positions SET portfolio_id = {ph} WHERE portfolio_id IS NULL OR portfolio_id = 1",
            (pid,),
        )
        execute(
            conn,
            f"UPDATE trades SET portfolio_id = {ph} WHERE portfolio_id IS NULL OR portfolio_id = 1",
            (pid,),
        )
    execute(conn, "DROP TABLE IF EXISTS portfolio")


def _migrate_pg(conn: Any) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'markets'"
    )
    existing = {row["column_name"] for row in cur.fetchall()}
    new_columns = {"tags": "TEXT", "event_title": "TEXT", "event_slug": "TEXT"}
    for col, col_type in new_columns.items():
        if col not in existing:
            cur.execute(f"ALTER TABLE markets ADD COLUMN {col} {col_type}")
    for table in ("positions", "trades"):
        cur.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
            (table,),
        )
        cols = {row["column_name"] for row in cur.fetchall()}
        if cols and "market_slug" not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN market_slug TEXT")
        if cols and "portfolio_id" not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN portfolio_id INTEGER")
            cur.execute(f"UPDATE {table} SET portfolio_id = 1 WHERE portfolio_id IS NULL")
    cur.close()



def _serialize(value: object) -> object:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


def _get_columns_sqlite(conn: sqlite3.Connection) -> set[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM pragma_table_info('markets')")
    return {row[0] for row in cur.fetchall()}


def _get_columns_pg(conn: Any) -> set[str]:
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'markets'"
    )
    cols = {row["column_name"] for row in cur.fetchall()}
    cur.close()
    return cols


def placeholder() -> str:
    """Return the correct parameter placeholder for the active backend."""
    return "%s" if settings.db_backend == "postgres" else "?"


def fetchall(conn: Connection, sql: str, params: tuple = ()) -> list:
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    return conn.execute(sql, params).fetchall()


def execute(conn: Connection, sql: str, params: tuple = ()) -> None:
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        cur.execute(sql, params)
        cur.close()
    else:
        conn.execute(sql, params)


def executemany(conn: Connection, sql: str, params_list: list) -> None:
    if settings.db_backend == "postgres":
        cur = conn.cursor()
        cur.executemany(sql, params_list)
        cur.close()
    else:
        conn.executemany(sql, params_list)



def upsert_markets(conn: Connection, markets: list[dict]) -> int:
    if settings.db_backend == "postgres":
        return _upsert_pg(conn, markets)
    return _upsert_sqlite(conn, markets)


def _upsert_sqlite(conn: sqlite3.Connection, markets: list[dict]) -> int:
    columns = _get_columns_sqlite(conn)
    cursor = conn.cursor()
    inserted = 0
    for market in markets:
        row = {k: _serialize(v) for k, v in market.items() if k in columns}
        col_names = ", ".join(row.keys())
        placeholders = ", ".join(f":{k}" for k in row)
        cursor.execute(
            f"INSERT OR REPLACE INTO markets ({col_names}) VALUES ({placeholders})",
            row,
        )
        inserted += 1
    conn.commit()
    return inserted


def _upsert_pg(conn: Any, markets: list[dict]) -> int:
    columns = _get_columns_pg(conn)
    cur = conn.cursor()
    inserted = 0
    for market in markets:
        row = {k.lower(): _serialize(v) for k, v in market.items() if k.lower() in columns}
        col_names = ", ".join(row.keys())
        placeholders = ", ".join(f"%({k})s" for k in row)
        update_set = ", ".join(f"{k} = EXCLUDED.{k}" for k in row if k != "id")
        cur.execute(
            f"""
            INSERT INTO markets ({col_names}) VALUES ({placeholders})
            ON CONFLICT (id) DO UPDATE SET {update_set}
            """,
            row,
        )
        inserted += 1
    conn.commit()
    cur.close()
    return inserted
