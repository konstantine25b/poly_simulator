import sys

sys.path.insert(0, "src")

from polymarket.api.markets import get_market_by_id, get_markets
from polymarket.db import (
    create_tables,
    executemany,
    fetchall,
    get_connection,
    placeholder,
    upsert_markets,
)

PAGE_SIZE = 100


def refresh() -> None:
    conn = get_connection()
    create_tables(conn)

    ph = placeholder()
    db_ids: set[str] = {
        r["id"]
        for r in fetchall(conn, "SELECT id FROM markets WHERE active=1 AND closed=0")
    }
    print(f"active+open markets in db : {len(db_ids)}")

    api_markets: list[dict] = []
    offset = 0
    page = 1

    while True:
        print(f"fetching page {page} (offset={offset})...", end=" ", flush=True)
        batch = get_markets(limit=PAGE_SIZE, offset=offset, accepting_orders=False)
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

    inserted = upsert_markets(conn, new_markets) if new_markets else 0

    confirmed_closed: list[str] = []
    skipped: int = 0
    if closed_ids:
        print(f"\nverifying {len(closed_ids)} potentially closed markets...")
        for mid in closed_ids:
            live = get_market_by_id(mid)
            if live and live.get("active") and not live.get("closed"):
                skipped += 1
            else:
                confirmed_closed.append(mid)

    if confirmed_closed:
        executemany(
            conn,
            f"UPDATE markets SET closed=1, active=0 WHERE id={ph}",
            [(mid,) for mid in confirmed_closed],
        )
        conn.commit()

    conn.close()

    print()
    print(f"fetched from API  : {len(api_markets)}")
    print(f"new (inserted)    : {inserted}")
    print(f"unchanged         : {len(api_ids & db_ids)}")
    print(f"skipped (still active, pagination gap) : {skipped}")
    print(f"marked closed     : {len(confirmed_closed)}")


if __name__ == "__main__":
    refresh()
