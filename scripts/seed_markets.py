import sys

sys.path.insert(0, "src")

from polymarket.api.markets import get_markets
from polymarket.db import DB_PATH, create_tables, get_connection, upsert_markets

_PAGE_SIZE = 100


def seed() -> None:
    conn = get_connection()
    create_tables(conn)
    print(f"database: {DB_PATH}")

    total = 0
    offset = 0
    page = 1

    while True:
        print(f"fetching page {page} (offset={offset})...", end=" ", flush=True)
        batch = get_markets(limit=_PAGE_SIZE, offset=offset)
        if not batch:
            print("empty — done")
            break

        inserted = upsert_markets(conn, batch)
        total += inserted
        print(f"{inserted} markets saved")

        if len(batch) < _PAGE_SIZE:
            break

        offset += _PAGE_SIZE
        page += 1

    conn.close()
    print(f"\ntotal saved: {total} markets")


if __name__ == "__main__":
    seed()
