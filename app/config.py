"""Application configuration from environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load from env; all optional have defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required (database_url can be empty for health-only runs; set for DB features)
    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"

    # Optional
    environment: str = "development"
    frontend_url: str = "http://localhost:5173"

    # Broker (optional until live)
    zerodha_api_key: str = ""
    zerodha_api_secret: str = ""
    groww_api_key: str = ""
    groww_api_secret: str = ""

    # Alerts (optional)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    def is_live_configured(self) -> bool:
        """True if at least one broker has credentials."""
        return bool(
            (self.zerodha_api_key and self.zerodha_api_secret)
            or (self.groww_api_key and self.groww_api_secret)
        )


settings = Settings()
