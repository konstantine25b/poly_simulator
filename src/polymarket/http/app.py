from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from polymarket.config import settings
from polymarket.db import create_tables, get_connection
from polymarket.http.routers import admin, auth, markets, portfolios, ws_markets
from polymarket.refresh_catalog import refresh_catalog

_log = logging.getLogger("uvicorn.error")

_FULL_REFRESH_INTERVAL_S = 30 * 60
_INCREMENTAL_REFRESH_INTERVAL_S = 5 * 60


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    try:
        create_tables(conn)
        conn.commit()
    finally:
        conn.close()

    stop = asyncio.Event()
    lock = asyncio.Lock()
    schedule_tasks: list[asyncio.Task[None]] = []

    async def full_schedule_loop() -> None:
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=_FULL_REFRESH_INTERVAL_S)
                return
            except asyncio.TimeoutError:
                pass
            async with lock:
                _log.info("catalog scheduled refresh started (full)")
                result = await asyncio.to_thread(refresh_catalog, incremental=False, quiet=True)
                _log.info(
                    "catalog scheduled refresh finished (full): fetched=%s inserted=%s "
                    "marked_closed=%s",
                    result["fetched_from_api"],
                    result["inserted"],
                    result["marked_closed"],
                )

    async def incremental_schedule_loop() -> None:
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=_INCREMENTAL_REFRESH_INTERVAL_S)
                return
            except asyncio.TimeoutError:
                pass
            if lock.locked():
                _log.info("catalog scheduled refresh skipped (incremental): busy")
                continue
            async with lock:
                _log.info("catalog scheduled refresh started (incremental)")
                result = await asyncio.to_thread(refresh_catalog, incremental=True, quiet=True)
                _log.info(
                    "catalog scheduled refresh finished (incremental): fetched=%s inserted=%s",
                    result["fetched_from_api"],
                    result["inserted"],
                )

    if settings.catalog_schedule_enabled:
        schedule_tasks.append(asyncio.create_task(full_schedule_loop()))
        schedule_tasks.append(asyncio.create_task(incremental_schedule_loop()))

    try:
        yield
    finally:
        stop.set()
        for t in schedule_tasks:
            t.cancel()
            with suppress(asyncio.CancelledError):
                await t


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

app = FastAPI(title="PolyPTrade API", lifespan=lifespan, openapi_tags=_openapi_tags)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(markets.router)
app.include_router(portfolios.router)
app.include_router(ws_markets.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
