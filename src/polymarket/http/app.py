from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from polymarket.db import create_tables, get_connection
from polymarket.http.routers import admin, auth, markets, portfolios, ws_markets


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    try:
        create_tables(conn)
        conn.commit()
    finally:
        conn.close()
    yield


_openapi_tags = [
    {"name": "auth"},
    {"name": "admin"},
    {"name": "markets"},
    {"name": "portfolios"},
    {"name": "system"},
    {
        "name": "WebSockets",
        "description": (
            "Live **best bid / best ask** from Polymarket (CLOB market channel), proxied by this API.\n\n"
            "**Endpoint:** `WS /ws/markets/{query}/best-bid-ask`\n\n"
            "`query` is a Gamma **market id** (digits) or **slug**, identical to **GET /markets/{query}/resolved**.\n\n"
            "The server opens `wss://ws-subscriptions-clob.polymarket.com/ws/market`, "
            "subscribes with `custom_feature_enabled: true`, and forwards only `best_bid_ask` JSON objects.\n\n"
            "Resolve your id/slug and get the socket path: **GET /markets/{query}/best-bid-ask/ws-docs**."
        ),
    },
]

app = FastAPI(title="Poly Simulator API", lifespan=lifespan, openapi_tags=_openapi_tags)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(markets.router)
app.include_router(portfolios.router)
app.include_router(ws_markets.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
