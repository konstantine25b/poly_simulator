from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gamma_api_base_url: str = "https://gamma-api.polymarket.com"
    clob_api_base_url: str = "https://clob.polymarket.com"

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

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
