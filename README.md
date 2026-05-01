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

Edit `.env` and set your values. You must choose a database backend. For the HTTP API you should also set **auth-related** variables (see `.env.example`).

**Database**

```
DB_BACKEND=sqlite      # no setup needed, uses a local file
# or
DB_BACKEND=postgres    # fill in POSTGRES_* fields below
```

**Auth and tokens (HTTP API)**

- **`JWT_SECRET`** — Secret used to sign bearer access tokens. Use a long random string in any shared or production deployment (for example `python -c "import secrets; print(secrets.token_urlsafe(48))"`). If you change it, existing tokens stop working until users log in again.
- **`ACCESS_TOKEN_TTL_SECONDS`** — Optional. Lifetime of access tokens in seconds (default one day).
- **`REFRESH_API_KEY`** — Optional. If set, `POST /markets/refresh` accepts header `X-Refresh-Api-Key` with this value without a JWT (rotate or leave empty in production if you rely only on admin Bearer tokens).

**First admin user (bootstrap)**

If the database has **no users** yet, the app creates one admin on first startup. By default (when you do not override these in `.env`) that account is:

- **Email:** `admin@admin123.com`
- **Password:** `admin123`

Set **`ADMIN_BOOTSTRAP_EMAIL`** and **`ADMIN_BOOTSTRAP_PASSWORD`** in `.env`. On **every** app startup, that email is ensured to exist as an **admin**, with the password from env (the account is created if missing; if it already exists, it is promoted to admin and the password is updated to match env). If **both** variables are empty, this sync step does nothing. On a totally empty database, the same pair is also used for the initial bootstrap user when both are non-empty.

Passwords are stored with **PBKDF2-SHA256** and a per-user salt (no extra “hashing secret” in `.env`).

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

For day-to-day updates, fetching only until the newest pages overlap your DB is much faster:

```bash
python scripts/refresh_markets.py --incremental   # or: -i
```

That mode still inserts newly created markets but does not walk the entire catalog, so it does not detect markets that closed; run `refresh_markets.py` without `--incremental` periodically when you need closures synced.

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

## HTTP API (FastAPI)

The same catalog refresh, market lookups, Gamma listing, and paper trading logic exposed by the Python library and CLI scripts is also available over HTTP. The FastAPI app is assembled in `src/polymarket/http/` (routers, dependencies, schemas, lifespan) and re-exported from `src/polymarket/http_app.py` so you can still run `uvicorn polymarket.http_app:app`. Authentication helpers (`Access`, password hashing, JWT-style bearer tokens, user persistence) live in `src/polymarket/auth/`. On startup it runs `create_tables` once (same schema as the rest of the project). Terminal scripts such as `scripts/refresh_markets.py` are unchanged; they call the shared `refresh_catalog` helper used by the API. Over HTTP, **`POST /markets/refresh`** is restricted to **admin** accounts only; the CLI scripts are not.

**Run the server** (from the repo root, with the venv activated):

```bash
export PYTHONPATH=src
uvicorn polymarket.http_app:app --reload --host 0.0.0.0 --port 8000
```

Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive Swagger UI, or call endpoints with `curl` as below (replace the host or port if you changed them). For protected routes, use **Authorize** (lock icon), choose **HTTPBearer**, and paste only the token value (Swagger adds the `Bearer ` prefix). You get a token from **POST /auth/login** or **POST /auth/register** (`access_token` in the JSON body).

Public routes (no bearer token): **`/health`**, **`/markets/{query}/*`** (including **`GET /markets/{query}/detail`** for a full market payload plus per-token **best bid / best ask** when open, or DB-only when closed), **`/db/markets`**, **`/gamma/markets`**, **`/auth/register`**, **`/auth/login`**. **`POST /markets/refresh`** requires an **admin** JWT **or** a matching **`X-Refresh-Api-Key`** when **`REFRESH_API_KEY`** is set in server env. **All `/portfolios` routes** and **`/auth/me`** require an `Authorization: Bearer <token>` header from login or register.

**Authentication**

```bash
# Register (anyone). Password must be at least 8 characters.
curl -s -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"your-secure-password"}'

# Login
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"your-secure-password"}'

# Current user (pass the access_token from register or login)
curl -s http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer ACCESS_TOKEN_HERE"
```

Each user has a unique email (case-insensitive), their own portfolios, and cannot see another user’s portfolios. **Admin** users (`is_admin` on the account) see **all** portfolios in `GET /portfolios` and may call summary, positions, trades, bet, close, and settle on **any** portfolio id or name.

**Admin HTTP API** (requires an admin bearer token)

```bash
# List users (id, email, is_admin, created_at — no password fields)
curl -s http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# Create a user (optional is_admin, default false)
curl -s -X POST http://127.0.0.1:8000/admin/users \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"email":"newuser@example.com","password":"temporary-password","is_admin":false}'

# Delete a user (cascades portfolios, positions, trades; cannot delete yourself)
curl -s -X DELETE http://127.0.0.1:8000/admin/users/USER_ID \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"

# Reset password
curl -s -X POST http://127.0.0.1:8000/admin/users/USER_ID/password \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"password":"new-password-at-least-8-chars"}'
```

**Health**

```bash
curl -s http://127.0.0.1:8000/health
```

**Catalog refresh** (calls live Gamma APIs; **admin JWT** or optional **API key**; full refresh can take a long time)

Either send an **admin** `Authorization: Bearer <token>` (use **Authorize** in `/docs`), or set **`REFRESH_API_KEY`** in server `.env` and pass **`X-Refresh-Api-Key`** with that value. In Swagger, **`X-Refresh-Api-Key` appears as its own field** under the operation so you do not rely on the Authorize dialog for catalog refresh.

```bash
export TOKEN='admin_access_token_from_login'

curl -s -X POST http://127.0.0.1:8000/markets/refresh \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{}'

curl -s -X POST http://127.0.0.1:8000/markets/refresh \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"incremental":true}'
```

With **`REFRESH_API_KEY`** set:

```bash
curl -s -X POST http://127.0.0.1:8000/markets/refresh \
  -H 'X-Refresh-Api-Key: YOUR_REFRESH_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"incremental":true}'
```

Log in as an admin (e.g. bootstrap `admin@admin123.com` / `admin123` unless you changed `.env`) to obtain `TOKEN` for the Bearer variant.

**Market data** (`QUERY` is a numeric market id or slug)

```bash
curl -s "http://127.0.0.1:8000/markets/QUERY/live"
curl -s "http://127.0.0.1:8000/markets/QUERY/detail"
curl -s "http://127.0.0.1:8000/markets/QUERY/cached"
curl -s "http://127.0.0.1:8000/markets/QUERY/resolved"
curl -s "http://127.0.0.1:8000/markets/QUERY/full"
```

The `resolved` route tries the live API first, then the local database, and sets `stale` when only cached data is available. The `full` route adds one CLOB order book per outcome token (network required).

**List markets from the local database** (paged; optional `active`, `closed`, `q` substring filter on question and slug, and **`sort`**: `created_desc` (default), `created_asc`, `volume_desc`, `volume_asc`, `end_desc`, `end_asc`, `start_desc`, `start_asc`, or aliases `newest` / `oldest`; `limit` capped at 500)

```bash
curl -s "http://127.0.0.1:8000/db/markets?limit=50&offset=0"
curl -s "http://127.0.0.1:8000/db/markets?active=true&closed=false&q=election"
curl -s "http://127.0.0.1:8000/db/markets?limit=50&sort=volume_desc"
```

Response shape: `{"items":[...],"total":N,"limit":L,"offset":O}`.

**Gamma markets listing** (paged proxy to `get_markets`)

```bash
curl -s "http://127.0.0.1:8000/gamma/markets?limit=5&offset=0&active=true&closed=false&accepting_orders=true"
```

**Paper trading** (`PORTFOLIO` is a portfolio id or name, for example `1` or `portfolio1`). Every request below needs the same bearer token you obtained from `/auth/login` or `/auth/register`.

```bash
export TOKEN='paste_access_token_here'

curl -s http://127.0.0.1:8000/portfolios \
  -H "Authorization: Bearer $TOKEN"

curl -s -X POST http://127.0.0.1:8000/portfolios \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo","balance":1000}'

curl -s "http://127.0.0.1:8000/portfolios/PORTFOLIO/summary" \
  -H "Authorization: Bearer $TOKEN"
curl -s "http://127.0.0.1:8000/portfolios/PORTFOLIO/positions" \
  -H "Authorization: Bearer $TOKEN"
curl -s "http://127.0.0.1:8000/portfolios/PORTFOLIO/trades" \
  -H "Authorization: Bearer $TOKEN"

curl -s -X POST "http://127.0.0.1:8000/portfolios/PORTFOLIO/bet" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"market_id":"MARKET_ID_OR_SLUG","outcome":"Yes","shares":10}'

curl -s -X POST "http://127.0.0.1:8000/portfolios/PORTFOLIO/close" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"position_id":1,"shares":5}'

curl -s -X POST "http://127.0.0.1:8000/portfolios/PORTFOLIO/settle" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"position_id":1,"won":true}'

curl -s -X DELETE "http://127.0.0.1:8000/portfolios/PORTFOLIO" \
  -H "Authorization: Bearer $TOKEN"
```

Portfolio **names** are unique per user (two different users may both use `demo`). Requests without a token return **401**. Accessing another user’s portfolio without admin privileges returns **400** with `portfolio not found` (same message as a missing id, to avoid leaking existence). Invalid input or other business-rule failures return **400** with a JSON `detail` string; missing markets return **404**. Bets, closes, and portfolio summaries need live market data where applicable, so run these with network access and valid ids from your seeded database or from Polymarket. **`DELETE /portfolios/{portfolio}`** removes the portfolio together with its positions and trades; non-admins can only delete their own portfolios, admins can delete any.

---

## WebSocket — live best bid / ask

The API proxies the Polymarket CLOB **market** channel and forwards only `best_bid_ask` frames, so the UI (and your own clients) can stream best bid / best ask per outcome token without talking to Polymarket directly.

**Discover the socket path** (resolves the id/slug, lists subscribed CLOB token ids, and returns the WS path plus an example message shape):

```bash
curl -s "http://127.0.0.1:8000/markets/QUERY/best-bid-ask/ws-docs"
```

`QUERY` is a Gamma **market id** (digits) or **slug**, the same value accepted by `GET /markets/{query}/resolved`. The response includes `websocket_path` (always `/ws/markets/{query}/best-bid-ask`) and `subscribed_asset_ids` (the CLOB token ids the upstream subscription will use).

**Connect to the stream**:

```
ws://127.0.0.1:8000/ws/markets/QUERY/best-bid-ask
```

(Use `wss://` behind TLS.) The server opens `wss://ws-subscriptions-clob.polymarket.com/ws/market`, subscribes with `custom_feature_enabled: true`, sends an application-level `PING` every 10 seconds, and forwards each `best_bid_ask` JSON object as-is. Frames look like:

```json
{
  "event_type": "best_bid_ask",
  "market": "0x0005c0d3…",
  "asset_id": "85354956062430465315924116860125388538595433819574542752031640332592237464430",
  "best_bid": "0.73",
  "best_ask": "0.77",
  "spread": "0.04",
  "timestamp": "1766789469958"
}
```

If the market or its CLOB tokens cannot be resolved, the server sends `{"error": "..."}` and closes with code `1008`. If the upstream Polymarket socket cannot be reached, it sends `{"error": "upstream unavailable"}` and closes with code `1011`. The route is **public** (no bearer token required).

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
from polymarket.auth import Access
from polymarket.trading.service import TradingService
```

### Try it interactively (simplest)

From the repo root, with the venv on, run Python in interactive mode so you can call methods line by line:

```bash
source venv/bin/activate
python -i scripts/try_paper_trading.py
```

That script adds `src` to the path, runs `create_tables` once, and defines **`RELAX = Access(1, True)`** and **`svc = TradingService(1, RELAX)`**. The `Access` object carries your user id and whether you are treated as an admin; `RELAX` is a local convenience so the REPL can resolve any portfolio id or name like the HTTP admin user. It prints short copy-paste examples; you then type expressions in the REPL (for example `svc.get_portfolio()` or `svc.place_bet("…slug…", "Yes", 1.0)`). Network is required for `place_bet` / `get_positions` / `get_portfolio` when live prices are fetched.

If you prefer a one-off without `-i`, run a small snippet:

```bash
source venv/bin/activate
PYTHONPATH=src python -c "from polymarket.auth import Access; from polymarket.db import create_tables, get_connection; from polymarket.trading.service import TradingService; c=get_connection(); create_tables(c); c.close(); a=Access(1, True); print(TradingService(1, a).get_portfolio())"
```

### `TradingService.create_portfolio`

```python
TradingService.create_portfolio(
    access: Access,
    name: str | None = None,
    balance: float | None = None,
) -> dict[str, Any]
```

Creates a new portfolio row **owned by** `access.user_id`. If `balance` is omitted, it uses `PAPER_BALANCE` from settings (default `1000.0` in `polymarket.config`). If `name` is omitted, the name is set to `portfolio` + the new numeric `id` (e.g. `portfolio2`). If `name` is provided, it must be **unique for that user** (comparison is case-insensitive); otherwise `ValueError` with message `portfolio name already exists`.

**Returns:** `{"id", "name", "balance", "created_at", "user_id"}` (ISO timestamp on `created_at`).

### `TradingService.list_portfolios`

```python
TradingService.list_portfolios(access: Access) -> list[dict[str, Any]]
```

**Returns:** portfolios the caller may see: only rows with matching `user_id`, unless `access.is_admin` is true (then every portfolio, each row includes `user_id`), ordered by `id`.

### Constructing the service for a portfolio

The portfolio passed to **`TradingService(...)`** is the default for any call. Every mutating and read method can override it with an optional **`portfolio`** argument (id or name): **`get_portfolio`**, **`get_positions`**, **`get_trades`**, **`place_bet`**, **`close_position`**. When omitted, the instance default is used.

```python
TradingService.__init__(self, portfolio: int | str, access: Access) -> None
```

`portfolio` is either a numeric **id** (existing row) or a **name** string. For non-admins, names are resolved **within that user’s portfolios only**. For admins, name resolution is global (first match by id order). For digit-only strings, **id is tried first** if a row with that id exists; otherwise the string is treated as a name. If the portfolio does not exist or is owned by another user and you are not an admin, you get `ValueError` with message `portfolio not found`.

Examples: `TradingService(1, Access(1, False))`, `TradingService("portfolio1", Access(1, False))`, `TradingService("MyBook", Access(42, False))`.

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
from polymarket.auth import Access
from polymarket.db import create_tables, get_connection
from polymarket.trading.service import TradingService

conn = get_connection()
create_tables(conn)
conn.close()

me = Access(1, False)
info = TradingService.create_portfolio(me, name="Practice", balance=500.0)
pid = info["id"]
svc = TradingService(pid, me)

rows = TradingService.list_portfolios(me)
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


# Web UI (React)

A small **JavaScript** React app in **`frontend/`** talks to the same HTTP API. In development, **Vite** serves the UI and proxies **`/api`** to **`http://127.0.0.1:8000`**, so the API must be listening on port **8000** (or change both `frontend/vite.config.js` and your `uvicorn` port to match).

**Start the frontend** (from the repo root; [Node.js](https://nodejs.org/) 18 or newer matches the pinned Vite 6 toolchain):

```bash
cd frontend
npm install
npm run dev
```

(`npm start` is the same command: it runs the Vite dev server.)

Open the URL Vite prints in the terminal, usually [http://127.0.0.1:5173](http://127.0.0.1:5173). The app uses **`react-router-dom`** and exposes the following routes:

- **`/`** — markets browse (public).
- **`/m/:marketRef`** — market detail (public).
- **`/login`**, **`/register`** — sign in / sign up (public, no top navbar).
- **`/profile`** — your profile and portfolio list (auth required).
- **`/portfolios/:portfolioId`** — single-portfolio dashboard with live quotes (auth required).

`/profile` and `/portfolios/:portfolioId` are wrapped in `RequireAuth`; if there is no token in `localStorage`, the user is bounced to `/login`. UI code is split into **`frontend/src/features/markets/`** (browse + detail) and **`frontend/src/features/auth/`** (login, register, profile, portfolio detail, components, hooks, API client). The Polymarket mark in **`frontend/assets/`** is the favicon and fallback image.

**Markets browse (`/`)** — loads **`GET /db/markets`** (via the dev proxy as **`/api/db/markets`**) for a **catalog** substring search (question and slug in your DB), plus **All / Active / Closed** filters, optional **`sort`**, and pagination (**50** or **100** per page). A second field calls **`GET /markets/{query}/live`** as **`/api/markets/.../live`** for an **exact Gamma lookup** by numeric **id** or **slug** (live Polymarket data, not the local DB). Each catalog card links to **`/m/{id-or-slug}`** and the grid uses **3-column** compact cards (hover, **Live** when `active`, not `closed`, not past **end** time, **volumeNum**, **outcomes** + **outcomePrices**).

**Market detail (`/m/:marketRef`)** — loads **`GET /markets/{query}/detail`** (`closed` → full row from the **database**; open → **live** Gamma market plus **best bid / best ask** per outcome token from the CLOB book, no full order book).

**Auth (`/login`, `/register`)** — POST to **`/auth/login`** / **`/auth/register`**, store the returned `access_token` and the user payload in `localStorage` via the `AuthProvider` (`frontend/src/features/auth/context/`), then redirect to `/profile`. The navbar is hidden on these two routes.

**Profile (`/profile`)** — lists the current user's portfolios (admins see every user's portfolios) using **`GET /portfolios`**, with totals (equity, cash, invested, P/L) computed in the browser. **New portfolio** opens a dialog that POSTs to **`/portfolios`**; each card has a **Delete** action that calls **`DELETE /portfolios/{id}`** (non-admins can only delete their own).

**Portfolio detail (`/portfolios/:portfolioId`)** — pulls **summary**, **positions**, and **trades** in parallel (**`GET /portfolios/{id}/summary|positions|trades`**) and then opens **one WebSocket per distinct market** to **`WS /ws/markets/{query}/best-bid-ask`** (see the WebSocket section above). Live `best_bid` / `best_ask` updates re-mark every open position in real time, so `current_price`, `market_value`, and `unrealized_pnl` recompute on each tick without a re-fetch. A **Live / Live · partial / Connecting… / Live unavailable** pill in the top bar reflects how many of the underlying sockets are connected. The page also exposes per-position **Sell** and **Settle** dialogs that POST to **`/portfolios/{id}/close`** and **`/portfolios/{id}/settle`** respectively.

**Building and deploying** — use **`npm run build`** to produce `frontend/dist/`, and set **`VITE_API_URL`** when you are not using the Vite dev proxy (the WS URL helper at `frontend/src/features/markets/query/marketBestBidAskWsUrl.js` rewrites the same base to `ws://` / `wss://` automatically). Configure **CORS** on the FastAPI side if UI and API are served from different origins.
