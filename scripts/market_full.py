import json
import sqlite3
import sys

sys.path.insert(0, "src")

from polymarket.api.markets import fetch_market
from polymarket.api.prices import get_order_book
from polymarket.db import DB_PATH


def resolve_market(query: str) -> tuple[dict | None, bool]:
    stale = False
    try:
        m = fetch_market(query)
        if m:
            return m, False
    except Exception:
        pass

    stale = True
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM markets WHERE id=? OR slug=? LIMIT 1", (query, query)
    ).fetchone()
    conn.close()
    return (dict(row) if row else None), stale


def parse_list(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            pass
    return []


def print_info(m: dict) -> None:
    def fmt(v: object) -> str:
        if isinstance(v, (list, dict)):
            return json.dumps(v, indent=4)
        return str(v) if v is not None else "—"

    sections: dict[str, list[str]] = {
        "IDENTITY": ["id", "question", "slug", "conditionId", "questionID", "marketType"],
        "DATES": ["startDate", "endDate", "endDateIso", "createdAt", "updatedAt", "acceptingOrdersTimestamp"],
        "STATUS": ["active", "closed", "acceptingOrders", "enableOrderBook", "restricted", "archived", "negRisk", "featured"],
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
        any_val = any(
            m.get(f) not in (None, "", "[]", [], {})
            for f in fields
        )
        if not any_val:
            continue
        print(f"\n{'─' * 60}")
        print(f"  {section}")
        print(f"{'─' * 60}")
        for f in fields:
            val = m.get(f)
            if val in (None, "", "[]", [], {}):
                continue
            formatted = fmt(val)
            if "\n" in formatted:
                print(f"  {f}:")
                for line in formatted.splitlines():
                    print(f"    {line}")
            else:
                print(f"  {f:<32} {formatted}")


def print_order_book(book: dict, label: str) -> None:
    bids = sorted(book.get("bids", []), key=lambda x: float(x["price"]), reverse=True)
    asks = sorted(book.get("asks", []), key=lambda x: float(x["price"]))

    best_bid = float(bids[0]["price"]) if bids else None
    best_ask = float(asks[0]["price"]) if asks else None
    last = book.get("last_trade_price") or "—"
    tick = book.get("tick_size", "—")
    min_size = book.get("min_order_size", "—")

    print(f"\n{'─' * 60}")
    print(f"  ORDER BOOK — {label}")
    print(f"{'─' * 60}")
    if best_bid is not None:
        print(f"  best bid      {best_bid:.4f}")
    if best_ask is not None:
        print(f"  best ask      {best_ask:.4f}")
    if best_bid and best_ask:
        print(f"  spread        {best_ask - best_bid:.4f}")
    print(f"  last trade    {last}")
    print(f"  tick size     {tick}   min order  {min_size}")

    col = 10
    print(f"\n  {'ASKS':^{col * 2 + 4}}")
    print(f"  {'price':>{col}}  {'size':>{col}}")
    print(f"  {'─' * col}  {'─' * col}")
    for lvl in reversed(asks):
        print(f"  {float(lvl['price']):>{col}.4f}  {float(lvl['size']):>{col}.2f}")

    print(f"\n  {'─' * 26} spread")

    print(f"\n  {'BIDS':^{col * 2 + 4}}")
    print(f"  {'price':>{col}}  {'size':>{col}}")
    print(f"  {'─' * col}  {'─' * col}")
    for lvl in bids:
        print(f"  {float(lvl['price']):>{col}.4f}  {float(lvl['size']):>{col}.2f}")

    bid_liq = sum(float(lvl["price"]) * float(lvl["size"]) for lvl in bids)
    ask_liq = sum(float(lvl["price"]) * float(lvl["size"]) for lvl in asks)
    print(f"\n  bid liquidity  ${bid_liq:,.2f}")
    print(f"  ask liquidity  ${ask_liq:,.2f}")
    print(f"  total levels   {len(bids)} bids / {len(asks)} asks")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python scripts/market_full.py <id or slug>")
        sys.exit(1)

    query = sys.argv[1]
    market, stale = resolve_market(query)

    if not market:
        print(f"market not found: '{query}'")
        sys.exit(1)

    print(f"\n{'═' * 60}")
    if stale:
        print("  ⚠  STALE DATA — API unavailable, market info from DB cache")
        print(f"{'═' * 60}")
    print(f"  FULL MARKET VIEW: {market.get('question', query)}")
    print(f"{'═' * 60}")

    print_info(market)

    tokens = parse_list(market.get("clobTokenIds"))
    outcomes = parse_list(market.get("outcomes"))

    if not tokens:
        print("\n  no clob token IDs — order book unavailable")
    else:
        print(f"\n\n{'═' * 60}")
        print("  LIVE ORDER BOOKS  (from CLOB API)")
        print(f"{'═' * 60}")

        for i, token_id in enumerate(tokens):
            label = outcomes[i] if i < len(outcomes) else f"TOKEN {i}"
            book = get_order_book(token_id)
            if book:
                print_order_book(book, label)
            else:
                print(f"\n  could not fetch order book for {label}")

    print(f"\n{'═' * 60}\n")


if __name__ == "__main__":
    main()
