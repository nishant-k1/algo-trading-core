"""Screener API schemas."""

from pydantic import BaseModel


class ScanRowResponse(BaseModel):
    """One row from a screener scan."""

    exchange: str
    symbol: str
    value: float
    extra: dict[str, float | str] | None = None


class ScanResponse(BaseModel):
    """List of scan results."""

    scan: str
    exchange: str
    rows: list[ScanRowResponse]
    message: str | None = None
