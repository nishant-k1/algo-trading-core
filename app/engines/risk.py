"""Risk engine: pre-trade checks."""

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models.user_settings import UserSettings
from app.db.models.order import Order
from app.db.models.daily_pnl import DailyPnl
from app.engines.opm import get_positions


def _get_today_start_utc() -> datetime:
    """Start of today in UTC (naive for DB compare if needed)."""
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def pre_trade_checks(
    db: Session,
    user_id: int,
    paper_live: str,
    side: str,
    quantity: int,
    price_estimate: float,
    symbol: str,
    exchange: str,
    product: str,
    gateway: Any = None,
) -> tuple[bool, str]:
    """
    Run pre-trade risk checks. Returns (allowed, reason).
    Caller must have already checked kill_switch.
    """
    result = db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    settings = result.scalar_one_or_none()
    if settings is None:
        return True, ""

    # Max orders per day
    if getattr(settings, "max_orders_per_day", None) is not None:
        today_start = _get_today_start_utc()
        count_result = db.execute(
            select(func.count(Order.id)).where(
                Order.user_id == user_id,
                Order.paper_live == paper_live,
                Order.created_at >= today_start,
            )
        )
        count = count_result.scalar() or 0
        if count >= settings.max_orders_per_day:
            return False, f"Max orders per day ({settings.max_orders_per_day}) reached."

    # Max position value
    if getattr(settings, "max_position_value", None) is not None and settings.max_position_value > 0:
        positions = get_positions(db, user_id, paper_live, gateway)
        current_value = sum(
            p["quantity"] * p["average_price"] for p in positions
        )
        order_value = quantity * (price_estimate or 0.0)
        if side == "BUY":
            total_after = current_value + order_value
        else:
            total_after = max(0.0, current_value - order_value)
        if total_after > settings.max_position_value:
            return False, (
                f"Order would exceed max position value (₹{settings.max_position_value:,.0f})."
            )

    # Daily loss limit %
    if getattr(settings, "daily_loss_limit_pct", None) is not None and settings.daily_loss_limit_pct > 0:
        reference = getattr(settings, "max_position_value", None) or 20_00_000.0  # 20L default
        limit_loss = reference * (settings.daily_loss_limit_pct / 100.0)
        pnl_result = db.execute(
            select(DailyPnl).where(
                DailyPnl.user_id == user_id,
                DailyPnl.trade_date == date.today(),
            )
        )
        daily_row = pnl_result.scalar_one_or_none()
        daily_pnl = daily_row.realized_pnl if daily_row else 0.0
        if daily_pnl <= -limit_loss:
            return False, (
                f"Daily loss limit reached (realized P&L: ₹{daily_pnl:,.0f}, "
                f"limit: {settings.daily_loss_limit_pct}% of ₹{reference:,.0f})."
            )

    return True, ""
