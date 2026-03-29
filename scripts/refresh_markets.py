import sys

sys.path.insert(0, "src")

from polymarket.api.markets import get_markets
from polymarket.db import create_tables, get_connection, upsert_markets

PAGE_SIZE = 100


def refresh() -> None:
    conn = get_connection()
    create_tables(conn)

    db_ids: set[str] = {
        r[0] for r in conn.execute("SELECT id FROM markets WHERE active=1 AND closed=0").fetchall()
    }
    print(f"active+open markets in db : {len(db_ids)}")

    api_markets: list[dict] = []
    offset = 0
    page = 1

    while True:
        print(f"fetching page {page} (offset={offset})...", end=" ", flush=True)
        batch = get_markets(limit=PAGE_SIZE, offset=offset)
        if not batch:
            print("empty — done")
            break
        api_markets.extend(batch)
        print(f"{len(batch)}")
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        page += 1

    api_ids = {m["id"] for m in api_markets}

    new_markets = [m for m in api_markets if m["id"] not in db_ids]
    closed_ids = db_ids - api_ids

    if new_markets:
        inserted = upsert_markets(conn, new_markets)
    else:
        inserted = 0

    if closed_ids:
        conn.executemany(
            "UPDATE markets SET closed=1, active=0 WHERE id=?",
            [(mid,) for mid in closed_ids],
        )
        conn.commit()

    conn.close()

    print()
    print(f"fetched from API  : {len(api_markets)}")
    print(f"new (inserted)    : {inserted}")
    print(f"unchanged         : {len(api_ids & db_ids)}")
    print(f"marked closed     : {len(closed_ids)}")


if __name__ == "__main__":
    refresh()
