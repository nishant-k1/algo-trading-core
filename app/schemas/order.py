"""Order and position API schemas."""

from datetime import datetime
from pydantic import BaseModel


class OrderPlaceRequest(BaseModel):
    """Place order request."""

    symbol: str
    exchange: str = "NSE"
    side: str  # BUY | SELL
    quantity: int
    product: str | None = None  # default from trading mode
    order_type: str = "MARKET"  # MARKET | LIMIT
    price: float | None = None
    client_order_id: str | None = None  # idempotency; generated if omitted


class OrderResponse(BaseModel):
    """Order record."""

    id: int
    client_order_id: str
    broker_order_id: str | None
    symbol: str
    exchange: str
    side: str
    quantity: int
    product: str
    order_type: str
    status: str
    paper_live: str
    filled_quantity: int
    average_price: float | None
    created_at: datetime | None = None


class OrderCancelRequest(BaseModel):
    """Cancel order: provide our order id (paper) or broker_order_id (live)."""

    order_id: int | None = None
    broker_order_id: str | None = None


class PositionResponse(BaseModel):
    """Position record."""

    symbol: str
    exchange: str
    side: str
    quantity: int
    average_price: float
    product: str
    paper_live: str
