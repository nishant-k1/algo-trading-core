"""Strategy API schemas."""

from pydantic import BaseModel


class StrategyOption(BaseModel):
    """Available strategy (key + display name)."""

    key: str
    name: str


class StrategyConfigResponse(BaseModel):
    """One strategy config."""

    id: int
    name: str
    strategy_key: str
    params: dict
    watchlist_id: int
    is_active: bool


class StrategyConfigCreate(BaseModel):
    """Create strategy config."""

    name: str
    strategy_key: str
    params: dict = {}
    watchlist_id: int


class StrategyConfigUpdate(BaseModel):
    """Update strategy config."""

    name: str | None = None
    params: dict | None = None
    watchlist_id: int | None = None
    is_active: bool | None = None


class SignalResponse(BaseModel):
    """One signal from strategy run."""

    exchange: str
    symbol: str
    side: str
    reason: str
    score: float = 0.0
    meta: dict | None = None


class StrategyRunResponse(BaseModel):
    """Result of running a strategy."""

    signals: list[SignalResponse]
    symbols_scanned: int
    symbols_filtered_by_gap: int
