from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from polymarket.auth import Access
from polymarket.http.common import svc_exc
from polymarket.http.deps import get_access
from polymarket.http.schemas import BetBody, CloseBody, PortfolioCreateBody, SettleBody
from polymarket.trading.service import TradingService

router = APIRouter(tags=["portfolios"])


@router.get("/portfolios")
def list_portfolios(access: Access = Depends(get_access)) -> list[dict[str, Any]]:
    return TradingService.list_portfolios(access)


@router.post("/portfolios")
def create_portfolio(body: PortfolioCreateBody, access: Access = Depends(get_access)) -> dict[str, Any]:
    return svc_exc(
        lambda: TradingService.create_portfolio(access=access, name=body.name, balance=body.balance)
    )


@router.get("/portfolios/{portfolio}/summary")
def get_portfolio_summary(portfolio: str, access: Access = Depends(get_access)) -> dict[str, Any]:
    return svc_exc(lambda: TradingService(portfolio, access).get_portfolio())


@router.get("/portfolios/{portfolio}/positions")
def get_portfolio_positions(portfolio: str, access: Access = Depends(get_access)) -> list[dict[str, Any]]:
    return svc_exc(lambda: TradingService(portfolio, access).get_positions())


@router.get("/portfolios/{portfolio}/trades")
def get_portfolio_trades(portfolio: str, access: Access = Depends(get_access)) -> list[dict[str, Any]]:
    return svc_exc(lambda: TradingService(portfolio, access).get_trades())


@router.post("/portfolios/{portfolio}/bet")
def post_portfolio_bet(portfolio: str, body: BetBody, access: Access = Depends(get_access)) -> dict[str, Any]:
    return svc_exc(
        lambda: TradingService(portfolio, access).place_bet(
            market_id=body.market_id,
            outcome=body.outcome,
            shares=body.shares,
        )
    )


@router.post("/portfolios/{portfolio}/close")
def post_portfolio_close(portfolio: str, body: CloseBody, access: Access = Depends(get_access)) -> dict[str, Any]:
    return svc_exc(
        lambda: TradingService(portfolio, access).close_position(
            position_id=body.position_id, shares=body.shares
        )
    )


@router.post("/portfolios/{portfolio}/settle")
def post_portfolio_settle(portfolio: str, body: SettleBody, access: Access = Depends(get_access)) -> dict[str, Any]:
    return svc_exc(
        lambda: TradingService(portfolio, access).close_position_settled(
            position_id=body.position_id, won=body.won
        )
    )
