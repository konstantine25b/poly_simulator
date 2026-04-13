from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

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


def refresh_catalog(*, incremental: bool = False, quiet: bool = False) -> dict[str, Any]:
    def log(msg: str, *, end: str | None = "\n", flush: bool = True) -> None:
        if not quiet:
            print(msg, end=end if end is not None else "\n", flush=flush)

    conn = get_connection()
    create_tables(conn)

    ph = placeholder()
    db_ids: set[str] = {
        r["id"]
        for r in fetchall(conn, "SELECT id FROM markets WHERE active=1 AND closed=0")
    }
    log(f"active+open markets in db : {len(db_ids)}")

    api_markets: list[dict] = []
    offset = 0
    page = 1

    with gamma_client() as http:
        while True:
            log(f"fetching page {page} (offset={offset})...", end=" ")
            batch = get_markets(
                client=http,
                limit=PAGE_SIZE,
                offset=offset,
                accepting_orders=False,
                order="createdAt",
                ascending=False,
            )
            if not batch:
                log("empty — done")
                break
            api_markets.extend(batch)
            log(f"{len(batch)}")
            if incremental and all(m["id"] in db_ids for m in batch):
                log("incremental: page all in db — stopping")
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
    skipped = 0
    if closed_ids:
        n_closed = len(closed_ids)
        log(f"\nverifying {n_closed} potentially closed markets...")
        if n_closed > 2000:
            log(
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
                log(f"  verified {done}/{n_closed}")

    if confirmed_closed:
        executemany(
            conn,
            f"UPDATE markets SET closed=1, active=0 WHERE id={ph}",
            [(mid,) for mid in confirmed_closed],
        )
        conn.commit()

    conn.close()

    log("")
    log(f"fetched from API  : {len(api_markets)}")
    log(f"new (inserted)    : {inserted}")
    log(f"unchanged         : {len(api_ids & db_ids)}")
    log(f"skipped (still active, pagination gap) : {skipped}")
    log(f"marked closed     : {len(confirmed_closed)}")
    if incremental:
        log("(incremental: run without --incremental to detect closed markets)")

    return {
        "fetched_from_api": len(api_markets),
        "inserted": inserted,
        "unchanged_overlap": len(api_ids & db_ids),
        "skipped_still_active": skipped,
        "marked_closed": len(confirmed_closed),
        "incremental": incremental,
    }
