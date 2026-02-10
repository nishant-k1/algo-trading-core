"""Watchlist API schemas."""

from pydantic import BaseModel, ConfigDict


class WatchlistSymbolSchema(BaseModel):
    exchange: str = "NSE"
    symbol: str


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    is_auto_for_screener: bool
    symbols: list[WatchlistSymbolSchema]


class WatchlistCreate(BaseModel):
    name: str


class WatchlistUpdate(BaseModel):
    name: str | None = None
    is_auto_for_screener: bool | None = None


class UniverseResponse(BaseModel):
    watchlist_id: int
    symbols: list[WatchlistSymbolSchema]
