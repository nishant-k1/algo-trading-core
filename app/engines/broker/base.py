"""Abstract broker gateway interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Candle:
    """OHLCV candle."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Instrument:
    """Instrument (symbol) info."""

    exchange: str
    symbol: str
    token: str | int
    name: str = ""


@dataclass
class OrderRequest:
    """Order placement request."""

    symbol: str
    exchange: str
    side: str  # BUY | SELL
    quantity: int
    product: str  # MIS | CNC | NRML
    order_type: str  # MARKET | LIMIT | SL | SL-M
    price: float | None = None
    trigger_price: float | None = None
    validity: str = "DAY"
    client_order_id: str | None = None


@dataclass
class Position:
    """Position from broker."""

    symbol: str
    exchange: str
    side: str
    quantity: int
    average_price: float
    product: str = ""


class BrokerGateway(ABC):
    """Abstract interface for broker API (Zerodha, Groww, etc.)."""

    @abstractmethod
    def get_historical_candles(
        self,
        exchange: str,
        symbol: str,
        interval: str,  # "minute" | "3minute" | "5minute" | "day" etc.
        from_date: datetime,
        to_date: datetime,
    ) -> list[Candle]:
        """Fetch historical OHLCV candles."""
        ...

    @abstractmethod
    def get_instruments(self, exchange: str | None = None) -> list[Instrument]:
        """Fetch instrument list (symbol ↔ token)."""
        ...

    def place_order(self, req: OrderRequest) -> dict[str, Any]:
        """Place order; returns broker response with order_id."""
        raise NotImplementedError("place_order not implemented for this broker")

    def cancel_order(self, order_id: str, variety: str = "regular") -> dict[str, Any]:
        """Cancel an order."""
        raise NotImplementedError("cancel_order not implemented for this broker")

    def get_orders(self) -> list[dict[str, Any]]:
        """Get today's orders."""
        raise NotImplementedError("get_orders not implemented for this broker")

    def get_positions(self) -> list[Position]:
        """Get current positions."""
        raise NotImplementedError("get_positions not implemented for this broker")

    def test_connection(self) -> bool:
        """Verify credentials/connection; return True if ok."""
        raise NotImplementedError("test_connection not implemented for this broker")
