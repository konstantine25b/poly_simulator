from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from polymarket.db import create_tables, get_connection
from polymarket.http.routers import admin, auth, markets, portfolios


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    try:
        create_tables(conn)
        conn.commit()
    finally:
        conn.close()
    yield


app = FastAPI(title="Poly Simulator API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(markets.router)
app.include_router(portfolios.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
