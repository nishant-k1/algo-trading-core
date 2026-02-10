"""Dashboard API schemas."""

from datetime import datetime, date
from pydantic import BaseModel


class DashboardLastRun(BaseModel):
    run_at: datetime
    signals_count: int
    symbols_scanned: int
    symbols_filtered_by_gap: int


class DashboardPosition(BaseModel):
    symbol: str
    exchange: str
    side: str
    quantity: int
    average_price: float
    product: str
    paper_live: str


class DashboardOrder(BaseModel):
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


class DashboardSummary(BaseModel):
    paper_live: str
    kill_switch: bool
    positions: list[DashboardPosition]
    orders: list[DashboardOrder]
    daily_realized_pnl: float | None
    last_run: DashboardLastRun | None = None


class PnlHistoryEntry(BaseModel):
    date: date
    realized_pnl: float
