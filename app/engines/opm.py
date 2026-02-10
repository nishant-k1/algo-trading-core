"""Order & Position Manager: paper (simulated) and live (broker) execution."""

import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user_settings import UserSettings
from app.db.models.trading_mode import TradingMode
from app.db.models.order import Order
from app.db.models.position import Position
from app.db.models.daily_pnl import DailyPnl
from app.engines.broker.base import BrokerGateway, OrderRequest, Position as BrokerPosition


def get_product_and_paper_live(db: Session, user_id: int) -> tuple[str, str]:
    """Return (product, paper_live) from user settings. Default (CNC, paper)."""
    result = db.execute(
        select(UserSettings, TradingMode)
        .outerjoin(TradingMode, UserSettings.active_trading_mode_id == TradingMode.id)
        .where(UserSettings.user_id == user_id)
    )
    row = result.one_or_none()
    if not row:
        return "CNC", "paper"
    settings, mode = row[0], row[1]
    product = mode.product if mode else "CNC"
    paper_live = settings.paper_live if settings else "paper"
    return product, paper_live


def place_order(
    db: Session,
    user_id: int,
    request: OrderRequest,
    paper_live: str,
    gateway: BrokerGateway | None,
    client_order_id: str | None = None,
) -> Order:
    """
    Place order: paper = persist and simulate fill; live = broker then persist.
    Returns Order. Raises on duplicate client_order_id (idempotency).
    """
    if client_order_id is None:
        client_order_id = str(uuid.uuid4())

    existing = db.execute(
        select(Order).where(
            Order.user_id == user_id,
            Order.client_order_id == client_order_id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    if paper_live == "paper":
        order = Order(
            user_id=user_id,
            client_order_id=client_order_id,
            broker_order_id=None,
            symbol=request.symbol,
            exchange=request.exchange,
            side=request.side,
            quantity=request.quantity,
            product=request.product,
            order_type=request.order_type,
            status="COMPLETE",
            paper_live="paper",
            filled_quantity=request.quantity,
            average_price=request.price if request.order_type == "LIMIT" else 0.0,
        )
        db.add(order)
        db.flush()
        _update_paper_position(db, user_id, request, order.average_price or 0.0)
        db.commit()
        db.refresh(order)
        return order

    if gateway is None:
        raise RuntimeError("Live trading requires broker gateway")
    response = gateway.place_order(request)
    broker_order_id = response.get("order_id") or response.get("order_id_key") or str(response)

    order = Order(
        user_id=user_id,
        client_order_id=client_order_id,
        broker_order_id=broker_order_id,
        symbol=request.symbol,
        exchange=request.exchange,
        side=request.side,
        quantity=request.quantity,
        product=request.product,
        order_type=request.order_type,
        status="PENDING",
        paper_live="live",
        filled_quantity=0,
        average_price=None,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _add_daily_realized_pnl(db: Session, user_id: int, amount: float) -> None:
    """Add amount to today's realized P&L for user."""
    today = date.today()
    result = db.execute(
        select(DailyPnl).where(
            DailyPnl.user_id == user_id,
            DailyPnl.trade_date == today,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = DailyPnl(user_id=user_id, trade_date=today, realized_pnl=amount)
        db.add(row)
    else:
        row.realized_pnl += amount


def _update_paper_position(
    db: Session,
    user_id: int,
    request: OrderRequest,
    fill_price: float,
) -> None:
    result = db.execute(
        select(Position).where(
            Position.user_id == user_id,
            Position.symbol == request.symbol,
            Position.exchange == request.exchange,
            Position.side == request.side,
            Position.product == request.product,
            Position.paper_live == "paper",
        )
    )
    pos = result.scalar_one_or_none()
    qty = request.quantity
    if request.side == "SELL":
        qty = -qty
    if pos is None:
        if qty <= 0:
            return
        pos = Position(
            user_id=user_id,
            symbol=request.symbol,
            exchange=request.exchange,
            side=request.side,
            quantity=request.quantity,
            average_price=fill_price,
            product=request.product,
            paper_live="paper",
        )
        db.add(pos)
    else:
        if request.side == "BUY":
            total_qty = pos.quantity + request.quantity
            total_value = pos.quantity * pos.average_price + request.quantity * fill_price
            pos.quantity = total_qty
            pos.average_price = total_value / total_qty if total_qty else 0.0
        else:
            realized = (fill_price - pos.average_price) * request.quantity
            _add_daily_realized_pnl(db, user_id, realized)
            pos.quantity -= request.quantity
            if pos.quantity <= 0:
                db.delete(pos)


def get_orders(
    db: Session,
    user_id: int,
    paper_live: str,
    gateway: BrokerGateway | None = None,
) -> list[dict[str, Any]]:
    """Orders for user: paper from DB; live from broker (and merge with DB if needed)."""
    if paper_live == "paper":
        result = db.execute(
            select(Order).where(
                Order.user_id == user_id,
                Order.paper_live == "paper",
            ).order_by(Order.created_at.desc())
        )
        rows = result.scalars().unique().all()
        return [
            {
                "id": o.id,
                "client_order_id": o.client_order_id,
                "broker_order_id": o.broker_order_id,
                "symbol": o.symbol,
                "exchange": o.exchange,
                "side": o.side,
                "quantity": o.quantity,
                "product": o.product,
                "order_type": o.order_type,
                "status": o.status,
                "paper_live": o.paper_live,
                "filled_quantity": o.filled_quantity,
                "average_price": o.average_price,
                "created_at": o.created_at,
            }
            for o in rows
        ]
    if gateway is None:
        return []
    broker_orders = gateway.get_orders()
    return [dict(bo) for bo in broker_orders]


def get_positions(
    db: Session,
    user_id: int,
    paper_live: str,
    gateway: BrokerGateway | None = None,
) -> list[dict[str, Any]]:
    """Positions for user: paper from DB; live from broker."""
    if paper_live == "paper":
        result = db.execute(
            select(Position).where(
                Position.user_id == user_id,
                Position.paper_live == "paper",
                Position.quantity > 0,
            )
        )
        rows = result.scalars().unique().all()
        return [
            {
                "symbol": p.symbol,
                "exchange": p.exchange,
                "side": p.side,
                "quantity": p.quantity,
                "average_price": p.average_price,
                "product": p.product,
                "paper_live": p.paper_live,
            }
            for p in rows
        ]
    if gateway is None:
        return []
    broker_positions = gateway.get_positions()
    return [
        {
            "symbol": p.symbol,
            "exchange": p.exchange,
            "side": p.side,
            "quantity": p.quantity,
            "average_price": p.average_price,
            "product": p.product,
            "paper_live": "live",
        }
        for p in broker_positions
    ]
