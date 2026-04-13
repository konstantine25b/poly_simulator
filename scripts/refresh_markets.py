import argparse
import math
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "src")

from polymarket.api.client import gamma_client
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
_VERIFY_WORKERS = 24


def _verify_closed_chunk(ids: list[str]) -> tuple[list[str], int]:
    confirmed: list[str] = []
    skipped = 0
    with gamma_client() as c:
        for mid in ids:
            live = get_market_by_id(mid, c)
            if live and live.get("active") and not live.get("closed"):
                skipped += 1
            else:
                confirmed.append(mid)
    return confirmed, skipped


def refresh(*, incremental: bool = False) -> None:
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

    with gamma_client() as http:
        while True:
            print(f"fetching page {page} (offset={offset})...", end=" ", flush=True)
            batch = get_markets(
                client=http,
                limit=PAGE_SIZE,
                offset=offset,
                accepting_orders=False,
                order="createdAt",
                ascending=False,
            )
            if not batch:
                print("empty — done")
                break
            api_markets.extend(batch)
            print(f"{len(batch)}")
            if incremental and all(m["id"] in db_ids for m in batch):
                print("incremental: page all in db — stopping")
                break
            if len(batch) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            page += 1

    api_ids = {m["id"] for m in api_markets}

    new_markets = [m for m in api_markets if m["id"] not in db_ids]
    closed_ids = set() if incremental else (db_ids - api_ids)

    inserted = upsert_markets(conn, new_markets) if new_markets else 0

    confirmed_closed: list[str] = []
    skipped: int = 0
    if closed_ids:
        n_closed = len(closed_ids)
        print(f"\nverifying {n_closed} potentially closed markets...")
        if n_closed > 2000:
            print(
                f"(ids in db as active+open but not in this listing: {n_closed}; "
                f"listing size {len(api_ids)} — each id is checked via API)"
            )
        ids_list = list(closed_ids)
        n_workers = min(_VERIFY_WORKERS, max(1, len(ids_list)))
        chunk_sz = math.ceil(len(ids_list) / n_workers)
        chunks = [ids_list[i : i + chunk_sz] for i in range(0, len(ids_list), chunk_sz)]
        with ThreadPoolExecutor(max_workers=len(chunks)) as pool:
            submitted = {pool.submit(_verify_closed_chunk, ch): len(ch) for ch in chunks}
            done = 0
            for fut in as_completed(submitted):
                conf, sk = fut.result()
                confirmed_closed.extend(conf)
                skipped += sk
                done += submitted[fut]
                print(f"  verified {done}/{n_closed}", flush=True)

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
    if incremental:
        print("(incremental: run without --incremental to detect closed markets)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--incremental",
        "-i",
        action="store_true",
        help="newest-first pages only until a full page is already in the db (skips closed detection)",
    )
    args = p.parse_args()
    refresh(incremental=args.incremental)
