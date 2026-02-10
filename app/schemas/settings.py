"""Settings API schemas."""

from pydantic import BaseModel, Field


class TradingModeResponse(BaseModel):
    """Trading mode option."""

    id: int
    name: str
    segment: str
    product: str
    exchange: str


class SettingsResponse(BaseModel):
    """Current user settings."""

    active_broker_id: str = "zerodha"
    paper_live: str = "paper"
    brokers_available: list[str] = Field(default_factory=list)
    active_trading_mode_id: int | None = None
    kill_switch: bool = False
    max_position_value: float | None = None
    max_orders_per_day: int | None = None
    daily_loss_limit_pct: float | None = None


class SettingsUpdate(BaseModel):
    """Update settings request."""

    active_broker_id: str | None = None
    paper_live: str | None = None
    active_trading_mode_id: int | None = None
    kill_switch: bool | None = None
    max_position_value: float | None = None
    max_orders_per_day: int | None = None
    daily_loss_limit_pct: float | None = None
    zerodha_access_token: str | None = None
    groww_access_token: str | None = None


class TestConnectionResponse(BaseModel):
    """Test broker connection result."""

    broker_id: str
    connected: bool
    message: str = ""
