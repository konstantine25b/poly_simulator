import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "markets.db"

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


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_MARKETS_TABLE)
    _migrate(conn)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info('markets')").fetchall()}
    new_columns = {
        "tags": "TEXT",
        "event_title": "TEXT",
        "event_slug": "TEXT",
    }
    for col, col_type in new_columns.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE markets ADD COLUMN {col} {col_type}")


def _serialize(value: object) -> object:
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value


def upsert_markets(conn: sqlite3.Connection, markets: list[dict]) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM pragma_table_info('markets')")
    columns = {row[0] for row in cursor.fetchall()}

    inserted = 0
    for market in markets:
        row = {k: _serialize(v) for k, v in market.items() if k in columns}
        placeholders = ", ".join(f":{k}" for k in row)
        col_names = ", ".join(row.keys())
        cursor.execute(
            f"INSERT OR REPLACE INTO markets ({col_names}) VALUES ({placeholders})",
            row,
        )
        inserted += 1

    conn.commit()
    return inserted
