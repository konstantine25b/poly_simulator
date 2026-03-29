import json
import sqlite3
import sys

sys.path.insert(0, "src")

from polymarket.api.markets import fetch_market
from polymarket.api.prices import get_order_book
from polymarket.db import DB_PATH

DEPTH = None


def resolve_market(query: str) -> dict | None:
    try:
        m = fetch_market(query)
        if m:
            return m
    except Exception:
        pass

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM markets WHERE id=? OR slug=? LIMIT 1", (query, query)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def parse_tokens(market: dict) -> list[str]:
    tokens = market.get("clobTokenIds")
    if isinstance(tokens, str):
        try:
            tokens = json.loads(tokens)
        except (ValueError, TypeError):
            tokens = []
    return tokens or []


def print_book(book: dict, label: str) -> None:
    bids = sorted(book.get("bids", []), key=lambda x: float(x["price"]), reverse=True)
    asks = sorted(book.get("asks", []), key=lambda x: float(x["price"]))

    best_bid = float(bids[0]["price"]) if bids else None
    best_ask = float(asks[0]["price"]) if asks else None
    last = book.get("last_trade_price")
    tick = book.get("tick_size")
    min_size = book.get("min_order_size")

    print(f"\n{'─' * 52}")
    print(f"  ORDER BOOK — {label}")
    print(f"{'─' * 52}")
    if best_bid is not None:
        print(f"  best bid      {best_bid:.4f}")
    if best_ask is not None:
        print(f"  best ask      {best_ask:.4f}")
    if best_bid and best_ask:
        print(f"  spread        {best_ask - best_bid:.4f}")
    if last:
        print(f"  last trade    {last}")
    print(f"  tick size     {tick}   min order  {min_size}")

    col_w = 10
    print(f"\n  {'ASKS (sell orders)':^{col_w * 2 + 4}}")
    print(f"  {'price':>{col_w}}  {'size':>{col_w}}")
    print(f"  {'─' * col_w}  {'─' * col_w}")
    for lvl in reversed(asks):
        print(f"  {float(lvl['price']):>{col_w}.4f}  {float(lvl['size']):>{col_w}.2f}")

    print(f"\n  {'─' * 24}  mid")

    print(f"\n  {'BIDS (buy orders)':^{col_w * 2 + 4}}")
    print(f"  {'price':>{col_w}}  {'size':>{col_w}}")
    print(f"  {'─' * col_w}  {'─' * col_w}")
    for lvl in bids:
        print(f"  {float(lvl['price']):>{col_w}.4f}  {float(lvl['size']):>{col_w}.2f}")

    total_bid_liq = sum(float(l["price"]) * float(l["size"]) for l in bids)
    total_ask_liq = sum(float(l["price"]) * float(l["size"]) for l in asks)
    print(f"\n  bid liquidity  ${total_bid_liq:,.2f}")
    print(f"  ask liquidity  ${total_ask_liq:,.2f}")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python scripts/order_book.py <id or slug>")
        sys.exit(1)

    query = sys.argv[1]
    market = resolve_market(query)
    if not market:
        print(f"market not found: '{query}'")
        sys.exit(1)

    tokens = parse_tokens(market)
    outcomes = market.get("outcomes") or []
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except (ValueError, TypeError):
            outcomes = []

    print(f"\n{'═' * 52}")
    print(f"  {market.get('question', query)}")
    print(f"  id: {market.get('id')}  |  slug: {market.get('slug', '')[:35]}")
    print(f"{'═' * 52}")

    if not tokens:
        print("no clob token IDs found for this market")
        sys.exit(1)

    for i, token_id in enumerate(tokens):
        label = outcomes[i] if i < len(outcomes) else f"TOKEN {i}"
        book = get_order_book(token_id)
        if book:
            print_book(book, label)
        else:
            print(f"\n  could not fetch order book for {label} (token: {token_id[:20]}...)")

    print(f"\n{'═' * 52}\n")


if __name__ == "__main__":
    main()
