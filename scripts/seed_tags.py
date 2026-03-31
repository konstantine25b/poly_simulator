import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, "src")

import httpx

from polymarket.db import create_tables, executemany, fetchall, get_connection, placeholder

WORKERS = 20


def fetch_tags(market_id: str) -> tuple[str, list]:
    try:
        r = httpx.get(
            f"https://gamma-api.polymarket.com/markets/{market_id}/tags",
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return market_id, data if isinstance(data, list) else []
    except Exception:
        return market_id, []


def seed_tags() -> None:
    conn = get_connection()
    create_tables(conn)

    market_ids = [r["id"] for r in fetchall(conn, "SELECT id FROM markets")]
    total = len(market_ids)
    print(f"fetching tags for {total} markets with {WORKERS} workers...\n")

    done = 0
    updated = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(fetch_tags, mid): mid for mid in market_ids}
        batch: list[tuple[str, str]] = []

        for future in as_completed(futures):
            market_id, tags = future.result()
            batch.append((json.dumps(tags), market_id))
            done += 1

            if len(batch) >= 200:
                ph = placeholder()
                executemany(conn, f"UPDATE markets SET tags={ph} WHERE id={ph}", batch)
                conn.commit()
                updated += len(batch)
                batch = []

            if done % 1000 == 0 or done == total:
                pct = round(done / total * 100, 1)
                print(f"  {done}/{total} ({pct}%) — saved {updated}")

        if batch:
            ph = placeholder()
            executemany(conn, f"UPDATE markets SET tags={ph} WHERE id={ph}", batch)
            conn.commit()
            updated += len(batch)

    conn.close()
    print(f"\ndone — tags saved for {updated} markets")


if __name__ == "__main__":
    seed_tags()
