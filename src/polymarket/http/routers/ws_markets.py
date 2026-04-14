from __future__ import annotations

import asyncio
import json
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Path, WebSocket, WebSocketDisconnect
from websockets.asyncio.client import ClientConnection, connect as ws_connect
from websockets.exceptions import ConnectionClosed

from polymarket.catalog.order_books import clob_token_ids_for_market
from polymarket.catalog.queries import resolve_market_live_or_db
from polymarket.config import settings
from polymarket.http.schemas import BestBidAskEvent, BestBidAskWsDocs

router = APIRouter(tags=["WebSockets"])


async def _upstream_app_ping(upstream: ClientConnection) -> None:
    while True:
        await asyncio.sleep(10)
        try:
            await upstream.send("PING")
        except Exception:
            return


@router.get(
    "/markets/{query}/best-bid-ask/ws-docs",
    response_model=BestBidAskWsDocs,
    summary="WebSocket: resolve market and stream info",
    description=(
        "Supply your Gamma **market id** (digits) or **slug** as `query` (same as **GET /markets/{query}/resolved**). "
        "The response echoes resolution, lists **subscribed_asset_ids** (CLOB tokens) used for the upstream subscription, "
        "and gives **websocket_path** to open with `ws://` or `wss://` plus this server's host for **live** best bid/ask. "
        "**message_shape** documents one JSON frame (`best_bid_ask`); the stream emits one per outcome token when quotes move."
    ),
)
def get_best_bid_ask_ws_docs(
    query: Annotated[
        str,
        Path(
            description="Market id (numeric string) or slug.",
        ),
    ],
) -> BestBidAskWsDocs:
    market, _ = resolve_market_live_or_db(query)
    if not market:
        raise HTTPException(status_code=404, detail="market not found")
    asset_ids = clob_token_ids_for_market(market)
    if not asset_ids:
        raise HTTPException(status_code=404, detail="no clob tokens for market")
    slug_val = market.get("slug")
    slug_out = str(slug_val) if slug_val is not None else None
    mid = market.get("id")
    path = f"/ws/markets/{quote(query, safe='')}/best-bid-ask"
    shape = BestBidAskEvent(
        event_type="best_bid_ask",
        market="0x0005c0d312de0be897668695bae9f32b624b4a1ae8b140c49f08447fcc74f442",
        asset_id="85354956062430465315924116860125388538595433819574542752031640332592237464430",
        best_bid="0.73",
        best_ask="0.77",
        spread="0.04",
        timestamp="1766789469958",
    )
    return BestBidAskWsDocs(
        query=query,
        market_id=str(mid) if mid is not None else "",
        slug=slug_out,
        subscribed_asset_ids=asset_ids,
        websocket_path=path,
        message_shape=shape,
    )


@router.websocket("/ws/markets/{query}/best-bid-ask")
async def ws_market_best_bid_ask(websocket: WebSocket, query: str) -> None:
    await websocket.accept()
    market, _ = await asyncio.to_thread(resolve_market_live_or_db, query)
    if not market:
        await websocket.send_text(json.dumps({"error": "market not found"}))
        await websocket.close(code=1008)
        return
    asset_ids = clob_token_ids_for_market(market)
    if not asset_ids:
        await websocket.send_text(json.dumps({"error": "no clob tokens for market"}))
        await websocket.close(code=1008)
        return
    sub = {"assets_ids": asset_ids, "type": "market", "custom_feature_enabled": True}
    try:
        async with ws_connect(
            settings.clob_ws_market_url,
            ping_interval=None,
            ping_timeout=None,
        ) as upstream:
            await upstream.send(json.dumps(sub))
            ping_task = asyncio.create_task(_upstream_app_ping(upstream))
            try:
                async for raw in upstream:
                    if isinstance(raw, bytes):
                        raw = raw.decode()
                    if raw == "PONG":
                        continue
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(data, dict) or data.get("event_type") != "best_bid_ask":
                        continue
                    try:
                        await websocket.send_text(raw)
                    except WebSocketDisconnect:
                        break
            except ConnectionClosed:
                pass
            finally:
                ping_task.cancel()
                try:
                    await ping_task
                except asyncio.CancelledError:
                    pass
    except Exception:
        try:
            await websocket.send_text(json.dumps({"error": "upstream unavailable"}))
            await websocket.close(code=1011)
        except Exception:
            pass
