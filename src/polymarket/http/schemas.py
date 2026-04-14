from __future__ import annotations

from pydantic import BaseModel, Field


class RefreshBody(BaseModel):
    incremental: bool = False


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
