"""Dashboard summary: status, positions, orders, daily P&L, last run, PnL history."""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserId, get_db, get_user_gateway
from app.db.models.user_settings import UserSettings
from app.db.models.daily_pnl import DailyPnl
from app.db.models.strategy_run_cache import StrategyRunCache
from app.engines.opm import get_product_and_paper_live, get_orders, get_positions
from app.schemas.dashboard import (
    DashboardSummary,
    DashboardPosition,
    DashboardOrder,
    DashboardLastRun,
    PnlHistoryEntry,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

ORDERS_LIMIT = 20


@router.get("", response_model=DashboardSummary)
def get_summary(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> DashboardSummary:
    """Summary for dashboard: paper_live, kill_switch, positions, recent orders, today's realized P&L."""
    settings_row = db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    ).scalar_one_or_none()
    paper_live = getattr(settings_row, "paper_live", "paper") if settings_row else "paper"
    kill_switch = getattr(settings_row, "kill_switch", False) if settings_row else False

    gateway = get_user_gateway(db, user_id)
    positions = get_positions(db, user_id, paper_live, gateway)
    orders_raw = get_orders(db, user_id, paper_live, gateway)
    orders_slice = orders_raw[:ORDERS_LIMIT]

    daily_pnl_row = db.execute(
        select(DailyPnl).where(
            DailyPnl.user_id == user_id,
            DailyPnl.trade_date == date.today(),
        )
    ).scalar_one_or_none()
    daily_realized_pnl = daily_pnl_row.realized_pnl if daily_pnl_row else None

    run_cache = db.execute(
        select(StrategyRunCache).where(StrategyRunCache.user_id == user_id)
    ).scalar_one_or_none()
    last_run = (
        DashboardLastRun(
            run_at=run_cache.run_at,
            signals_count=run_cache.signals_count,
            symbols_scanned=run_cache.symbols_scanned,
            symbols_filtered_by_gap=run_cache.symbols_filtered_by_gap,
        )
        if run_cache else None
    )

    return DashboardSummary(
        paper_live=paper_live,
        kill_switch=kill_switch,
        positions=[
            DashboardPosition(
                symbol=p["symbol"],
                exchange=p["exchange"],
                side=p["side"],
                quantity=p["quantity"],
                average_price=p["average_price"],
                product=p["product"],
                paper_live=p["paper_live"],
            )
            for p in positions
        ],
        orders=[
            DashboardOrder(
                id=o.get("id", 0),
                client_order_id=o.get("client_order_id", o.get("order_id", "")),
                broker_order_id=o.get("broker_order_id", o.get("order_id")),
                symbol=o.get("symbol", ""),
                exchange=o.get("exchange", "NSE"),
                side=o.get("side", ""),
                quantity=o.get("quantity", 0),
                product=o.get("product", ""),
                order_type=o.get("order_type", "MARKET"),
                status=o.get("status", "PENDING"),
                paper_live=o.get("paper_live", paper_live),
                filled_quantity=o.get("filled_quantity", 0),
                average_price=o.get("average_price"),
                created_at=o.get("created_at"),
            )
            for o in orders_slice
        ],
        daily_realized_pnl=daily_realized_pnl,
        last_run=last_run,
    )


@router.get("/pnl-history", response_model=list[PnlHistoryEntry])
def get_pnl_history(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=90),
) -> list[PnlHistoryEntry]:
    """Last N days of realized P&L (for chart)."""
    end = date.today()
    start = end - timedelta(days=days - 1)
    result = db.execute(
        select(DailyPnl)
        .where(
            DailyPnl.user_id == user_id,
            DailyPnl.trade_date >= start,
            DailyPnl.trade_date <= end,
        )
        .order_by(DailyPnl.trade_date.asc())
    )
    rows = result.scalars().unique().all()
    by_date = {r.trade_date: r.realized_pnl for r in rows}
    out = []
    d = start
    while d <= end:
        out.append(PnlHistoryEntry(date=d, realized_pnl=by_date.get(d, 0.0)))
        d += timedelta(days=1)
    return out
