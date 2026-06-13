import sys
import time

import httpx

sys.path.insert(0, "src")

from polymarket.api.markets import get_markets_keyset
from polymarket.db import create_tables, get_connection, upsert_markets
from polymarket.config import settings

_PAGE_SIZE = 100
_TIMEOUT_PAUSE = 10


def seed() -> None:
    conn = get_connection()
    create_tables(conn)
    backend = settings.db_backend
    label = settings.postgres_label if backend == "postgres" else str(settings.sqlite_path)
    print(f"database ({backend}): {label}")

    total = 0
    after_cursor: str | None = None
    page = 1

    while True:
        cursor_for_page = after_cursor
        print(f"fetching page {page}...", end=" ", flush=True)
        try:
            batch, after_cursor = get_markets_keyset(
                limit=_PAGE_SIZE,
                after_cursor=cursor_for_page,
            )
        except httpx.ReadTimeout:
            print(f"timeout — waiting {_TIMEOUT_PAUSE}s then continuing")
            time.sleep(_TIMEOUT_PAUSE)
            after_cursor = cursor_for_page
            continue

        if not batch:
            print("empty — done")
            break

        inserted = upsert_markets(conn, batch)
        total += inserted
        print(f"{inserted} markets saved")

        if len(batch) < _PAGE_SIZE or not after_cursor:
            break

        page += 1

    conn.close()
    print(f"\ntotal saved: {total} markets")


if __name__ == "__main__":
    seed()
