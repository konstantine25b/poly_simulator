# Poly Simulator

A web platform that lets users practice prediction market trading using real Polymarket data — with no real money at risk. Users can place virtual trades, track portfolio performance, and observe live market price changes.

---

## Introduction

Prediction markets are online platforms where users make forecasts on various real-world events. Participants buy and sell contracts tied to the outcome of specific events, and the market price is often interpreted as the probability of that event occurring.

One of the most well-known platforms of this type is **Polymarket**, where users make predictions on political, economic, and social events using real financial resources. However, studying the mechanics of prediction markets and testing different trading strategies typically involves real financial risk — making it difficult or undesirable for many users to experiment on live markets.

---

## Problem Statement

Despite the widespread use of prediction markets for estimating the probability of events, people interested in this field often lack a safe environment to study market dynamics or test various trading strategies. Testing strategies on real markets carries financial risk, making it hard to run experiments and observe the impact of different decisions — especially for those who are just learning how prediction markets work or are trying to develop their own analytical approaches.

## Setup

**1. Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
pip install -e .
```

**3. Configure environment variables**

```bash
cp .env.example .env
```

Edit `.env` and set your values. The only required choice is the database backend:

```
DB_BACKEND=sqlite      # no setup needed, uses a local file
# or
DB_BACKEND=postgres    # fill in POSTGRES_* fields below
```

**4. Set up the database**

_SQLite_ — nothing to do, the file is created automatically on first run.

_PostgreSQL_ — create the database once:

```bash
psql -U postgres -c "CREATE DATABASE poly_simulator;"
```

**5. Seed market data**

```bash
python scripts/seed_markets.py   # download all active markets (~42k)
python scripts/seed_tags.py      # fetch tags for each market
```

After the initial seed, use `refresh_markets.py` to keep data up to date:

```bash
python scripts/refresh_markets.py
```

---

## Inspecting a Market

Use `inspect_market.py` to view all stored fields for a single market. Pass either a market **id** or **slug**:

```bash
python scripts/inspect_market.py <id or slug>
```

The script first tries the live Polymarket API. If the API is unreachable it falls back to the local DB cache and shows a stale-data warning. Output is grouped into sections: identity, dates, status, prices, volume, outcomes, tags, description, resolution, and rewards.

---

## Full Market View (with Live Order Books)

Use `market_full.py` to get everything `inspect_market.py` shows **plus** the live CLOB order book for every outcome token:

```bash
python scripts/market_full.py <id or slug>
```

For each outcome the order book displays best bid/ask, spread, last trade price, tick size, minimum order size, all ask and bid levels with sizes, and total bid/ask liquidity.

---

## Paper trading (`TradingService`)

Paper balances, positions, and trades live in the same database as markets (`portfolios`, `positions`, `trades` tables). Initialize the schema once (creates tables and a default portfolio when empty):

```python
from polymarket.db import create_tables, get_connection

conn = get_connection()
create_tables(conn)
conn.close()
```

Run Python with `PYTHONPATH=src` (or use `pip install -e .` from the repo root). Import:

```python
from polymarket.trading.service import TradingService
```

### Try it interactively (simplest)

From the repo root, with the venv on, run Python in interactive mode so you can call methods line by line:

```bash
source venv/bin/activate
python -i scripts/try_paper_trading.py
```

That script adds `src` to the path, runs `create_tables` once, and defines **`svc = TradingService(1)`** (the default seeded portfolio). It prints short copy-paste examples; you then type expressions in the REPL (for example `svc.get_portfolio()` or `svc.place_bet("…slug…", "Yes", 1.0)`). Network is required for `place_bet` / `get_positions` / `get_portfolio` when live prices are fetched.

If you prefer a one-off without `-i`, run a small snippet:

```bash
source venv/bin/activate
PYTHONPATH=src python -c "from polymarket.db import create_tables, get_connection; from polymarket.trading.service import TradingService; c=get_connection(); create_tables(c); c.close(); print(TradingService(1).get_portfolio())"
```

### `TradingService.create_portfolio`

```python
TradingService.create_portfolio(
    name: str | None = None,
    balance: float | None = None,
) -> dict[str, Any]
```

Creates a new portfolio row. If `balance` is omitted, it uses `PAPER_BALANCE` from settings (default `1000.0` in `polymarket.config`). If `name` is omitted, the name is set to `portfolio` + the new numeric `id` (e.g. `portfolio2`). If `name` is provided, it must be **unique** (comparison is case-insensitive); otherwise `ValueError` with message `portfolio name already exists`.

**Returns:** `{"id": int, "name": str, "balance": float, "created_at": str}` (ISO timestamp).

### `TradingService.list_portfolios`

```python
TradingService.list_portfolios() -> list[dict[str, Any]]
```

**Returns:** a list of `{"id", "name", "balance", "created_at"}` for every portfolio, ordered by `id`.

### Constructing the service for a portfolio

The portfolio passed to **`TradingService(...)`** is the default for any call. Every mutating and read method can override it with an optional **`portfolio`** argument (id or name): **`get_portfolio`**, **`get_positions`**, **`get_trades`**, **`place_bet`**, **`close_position`**. When omitted, the instance default is used.

```python
TradingService.__init__(self, portfolio: int | str) -> None
```

`portfolio` is either a numeric **id** (existing row) or a **name** string (case-insensitive match to `portfolios.name`). For digit-only strings, **id is tried first** if a row with that id exists; otherwise the string is treated as a name.

Examples: `TradingService(1)`, `TradingService("portfolio1")`, `TradingService("MyBook")`.

### `place_bet` (buy)

```python
TradingService.place_bet(
    self,
    market_id: str,
    outcome: str,
    shares: float,
    portfolio: int | str | None = None,
) -> dict[str, Any]
```

- `market_id`: Polymarket market **numeric id** or **slug** (resolved via `fetch_market`).
- `outcome`: label matching the market, e.g. `"Yes"` / `"No"` or the first/second outcome name.
- `shares`: size of the buy; must be `> 0`.
- `portfolio`: optional; if set, debits that portfolio (id or name) instead of the instance default. If `None`, uses the portfolio passed to `TradingService(...)`.

Buys fill at **best ask** for the first outcome in a two-outcome book, and at **`1 - bestBid`** for the second outcome when bid/ask exist; otherwise a fallback mid from stored prices is used. Repeated buys on the same `(portfolio, market_id, outcome)` **merge** into one position (average cost).

**Returns:**  
`{"trade_id", "position_id", "merged", "portfolio_id", "market_id", "outcome", "shares", "price", "cost", "traded_at"}`  
(`merged` is `True` when an existing position row was updated.)

### `close_position` (sell)

```python
TradingService.close_position(
    self,
    position_id: int,
    shares: float | None = None,
    portfolio: int | str | None = None,
) -> dict[str, Any]
```

- `position_id`: primary key of the `positions` row (returned as `position_id` from `place_bet`).
- `shares`: if `None`, the entire position is sold. If a positive number, only that many shares are sold (partial close); selling more than held raises `ValueError`.
- `portfolio`: optional; must match the row’s `portfolio_id` (id or name). If `None`, uses the instance default. Wrong portfolio → `position not found`.

Sells fill at **best bid** for the first outcome, **`1 - bestAsk`** for the second when the book is present; otherwise the same fallback as buys.

**Returns:**  
`{"trade_id", "position_id", "portfolio_id", "shares_sold", "remaining_shares", "position_closed", "price", "total", "traded_at"}`

### `get_portfolio`

```python
TradingService.get_portfolio(self, portfolio: int | str | None = None) -> dict[str, Any]
```

If `portfolio` is `None`, uses the instance’s portfolio. If set, resolves that **id** or **name** the same way as `__init__`.

**Returns:**  
`{"portfolio_id", "name", "balance", "total_invested", "unrealized_pnl", "positions_market_value", "equity"}`  
Cash `balance` plus open positions marked using bid/ask midpoint (see code: `_mark_price`). Raises `ValueError` if the portfolio does not exist.

### `get_positions`

```python
TradingService.get_positions(self, portfolio: int | str | None = None) -> list[dict[str, Any]]
```

Same optional `portfolio` argument as `get_portfolio`. If `None`, uses the instance’s portfolio.

**Returns:** one dict per open position for that portfolio. Each row includes DB fields (`id`, `portfolio_id`, `market_id`, `market_question`, `market_slug`, `outcome`, `shares`, `avg_price`, `cost`, `opened_at`) and, when live data is available, **`current_price`**, **`market_value`**, **`unrealized_pnl`**.

### `get_trades`

```python
TradingService.get_trades(self, portfolio: int | str | None = None) -> list[dict[str, Any]]
```

Same optional `portfolio` argument.

**Returns:** trade history for that portfolio only, newest first (`id`, `portfolio_id`, `market_id`, `market_question`, `market_slug`, `outcome`, `shares`, `price`, `side`, `total`, `traded_at`).

### Minimal example

```python
from polymarket.db import create_tables, get_connection
from polymarket.trading.service import TradingService

conn = get_connection()
create_tables(conn)
conn.close()

info = TradingService.create_portfolio(name="Practice", balance=500.0)
pid = info["id"]
svc = TradingService(pid)

rows = TradingService.list_portfolios()
portfolio = svc.get_portfolio()
same_by_name = svc.get_portfolio("Practice")

placed = svc.place_bet(
    "will-spain-win-the-2026-fifa-world-cup-963",
    "Yes",
    5.0,
)
positions = svc.get_positions()
closed = svc.close_position(placed["position_id"])
trades = svc.get_trades()
```

---
