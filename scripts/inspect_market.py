import json
import sqlite3
import sys

sys.path.insert(0, "src")

from polymarket.api.markets import fetch_market
from polymarket.db import DB_PATH


def find_in_db(query: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM markets WHERE id=? OR slug=? LIMIT 1", (query, query)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def print_market(m: dict) -> None:
    def fmt(v: object) -> object:
        if isinstance(v, str):
            try:
                return json.dumps(json.loads(v), indent=6)
            except (ValueError, TypeError):
                pass
        return v

    sections = {
        "IDENTITY": ["id", "question", "slug", "conditionId", "questionID", "marketType"],
        "DATES": ["startDate", "endDate", "createdAt", "updatedAt", "closedTime", "acceptingOrdersTimestamp"],
        "STATUS": ["active", "closed", "acceptingOrders", "enableOrderBook", "restricted", "archived", "featured", "negRisk"],
        "PRICES": ["lastTradePrice", "bestBid", "bestAsk", "spread", "oneDayPriceChange", "oneWeekPriceChange", "oneMonthPriceChange"],
        "VOLUME & LIQUIDITY": ["volumeNum", "liquidityNum", "volume24hr", "volume1wk", "volume1mo", "volume1yr"],
        "OUTCOMES": ["outcomes", "outcomePrices", "clobTokenIds"],
        "EVENT": ["event_title", "event_slug"],
        "TAGS": ["tags"],
        "DESCRIPTION": ["description"],
        "RESOLUTION": ["resolutionSource", "resolvedBy", "umaBond", "umaReward"],
        "REWARDS": ["rewardsMinSize", "rewardsMaxSpread", "orderPriceMinTickSize", "orderMinSize"],
    }

    for section, fields in sections.items():
        print(f"\n{'─' * 60}")
        print(f"  {section}")
        print(f"{'─' * 60}")
        for f in fields:
            val = m.get(f)
            if val is None or val == "" or val == "[]" or val == []:
                continue
            formatted = fmt(val)
            if isinstance(formatted, str) and "\n" in str(formatted):
                print(f"  {f}:")
                for line in str(formatted).splitlines():
                    print(f"    {line}")
            else:
                print(f"  {f:<30} {formatted}")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python scripts/inspect_market.py <id or slug>")
        sys.exit(1)

    query = sys.argv[1]
    stale = False
    market: dict | None = None

    try:
        market = fetch_market(query)
        if not market:
            raise ValueError("not found on API")
    except Exception as e:
        stale = True
        market = find_in_db(query)
        if not market:
            print(f"market not found in API or db: '{query}' ({e})")
            sys.exit(1)

    print(f"\n{'═' * 60}")
    if stale:
        print("  ⚠  STALE DATA — API unavailable, showing cached DB data")
        print(f"{'═' * 60}")
    print(f"  MARKET: {query}")
    print(f"{'═' * 60}")
    print_market(market)
    print(f"\n{'═' * 60}\n")


if __name__ == "__main__":
    main()
