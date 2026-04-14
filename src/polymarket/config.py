from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gamma_api_base_url: str = "https://gamma-api.polymarket.com"
    clob_api_base_url: str = "https://clob.polymarket.com"
    clob_ws_market_url: str = Field(
        default="wss://ws-subscriptions-clob.polymarket.com/ws/market",
        validation_alias="CLOB_WS_MARKET_URL",
    )

    log_level: str = "INFO"
    request_timeout: int = 10

    # ── Database ──────────────────────────────────────────────
    db_backend: Literal["sqlite", "postgres"] = "sqlite"

    # SQLite (used when db_backend=sqlite)
    sqlite_path: str = "data/markets.db"

    # PostgreSQL (used when db_backend=postgres)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "poly_simulator"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    # Paper trading 
    paper_balance: float = 1000.0

    jwt_secret: str = Field(
        default="dev-only-set-JWT_SECRET-in-env-for-production",
        validation_alias="JWT_SECRET",
    )
    access_token_ttl_seconds: int = Field(
        default=86_400,
        validation_alias="ACCESS_TOKEN_TTL_SECONDS",
    )

    admin_bootstrap_email: str = Field(
        default="admin@admin123.com",
        validation_alias="ADMIN_BOOTSTRAP_EMAIL",
    )
    admin_bootstrap_password: str = Field(
        default="admin123",
        validation_alias="ADMIN_BOOTSTRAP_PASSWORD",
    )

    refresh_api_key: str = Field(default="", validation_alias="REFRESH_API_KEY")

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
