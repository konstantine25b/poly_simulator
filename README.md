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
