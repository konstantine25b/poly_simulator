from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RefreshBody(BaseModel):
    incremental: bool = False


class BestBidAskEvent(BaseModel):
    event_type: Literal["best_bid_ask"]
    market: str
    asset_id: str
    best_bid: str
    best_ask: str
    spread: str
    timestamp: str


class BestBidAskWsDocs(BaseModel):
    query: str
    market_id: str
    slug: str | None = None
    subscribed_asset_ids: list[str]
    websocket_path: str
    message_shape: BestBidAskEvent


class PortfolioCreateBody(BaseModel):
    name: str | None = None
    balance: float | None = None


class BetBody(BaseModel):
    market_id: str
    outcome: str
    shares: float = Field(gt=0)


class CloseBody(BaseModel):
    position_id: int
    shares: float | None = None


class SettleBody(BaseModel):
    position_id: int
    won: bool


class RegisterBody(BaseModel):
    email: str
    password: str = Field(min_length=8)


class LoginBody(BaseModel):
    email: str
    password: str


class AdminUserCreateBody(BaseModel):
    email: str
    password: str = Field(min_length=8)
    is_admin: bool = False


class AdminResetPasswordBody(BaseModel):
    password: str = Field(min_length=8)


def email_ok(email: str) -> bool:
    if len(email) < 5 or "@" not in email:
        return False
    left, _, right = email.partition("@")
    if not left or not right or "." not in right:
        return False
    return True
