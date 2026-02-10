"""Orders and positions API (OPM)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserId, get_db, get_user_gateway
from app.db.models.order import Order
from app.db.models.user_settings import UserSettings
from app.engines.broker.base import OrderRequest
from app.engines.risk import pre_trade_checks
from app.engines.opm import (
    get_product_and_paper_live,
    place_order as opm_place_order,
    get_orders as opm_get_orders,
    get_positions as opm_get_positions,
)
from app.schemas.order import OrderCancelRequest, OrderPlaceRequest, OrderResponse, PositionResponse
from app.core.alerts import notify_order_placed

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
def place_order(
    body: OrderPlaceRequest,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """
    Place order. Paper/live and product come from Settings.
    Idempotent when client_order_id is supplied.
    """
    settings_row = db.execute(select(UserSettings).where(UserSettings.user_id == user_id)).scalar_one_or_none()
    if settings_row and getattr(settings_row, "kill_switch", False):
        raise HTTPException(status_code=400, detail="Kill switch is ON. Turn it off in Settings to place orders.")
    product, paper_live = get_product_and_paper_live(db, user_id)
    if body.product is not None:
        product = body.product
    req = OrderRequest(
        symbol=body.symbol,
        exchange=body.exchange,
        side=body.side,
        quantity=body.quantity,
        product=product,
        order_type=body.order_type,
        price=body.price,
        client_order_id=body.client_order_id,
    )
    gateway = get_user_gateway(db, user_id) if paper_live == "live" else None
    if paper_live == "live" and gateway is None:
        raise HTTPException(status_code=400, detail="Broker not configured for live trading.")
    price_estimate = body.price if body.order_type == "LIMIT" and body.price is not None else 0.0
    allowed, reason = pre_trade_checks(
        db, user_id, paper_live, body.side, body.quantity, price_estimate,
        body.symbol, body.exchange, product, gateway,
    )
    if not allowed:
        raise HTTPException(status_code=400, detail=reason)
    try:
        order = opm_place_order(db, user_id, req, paper_live, gateway, body.client_order_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        notify_order_placed(
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side,
            quantity=order.quantity,
            paper_live=order.paper_live,
            order_id=order.client_order_id or str(order.id),
        )
    except Exception:
        pass
    return OrderResponse(
        id=order.id,
        client_order_id=order.client_order_id,
        broker_order_id=order.broker_order_id,
        symbol=order.symbol,
        exchange=order.exchange,
        side=order.side,
        quantity=order.quantity,
        product=order.product,
        order_type=order.order_type,
        status=order.status,
        paper_live=order.paper_live,
        filled_quantity=order.filled_quantity,
        average_price=order.average_price,
        created_at=order.created_at,
    )


@router.get("", response_model=list[OrderResponse])
def list_orders(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> list[OrderResponse]:
    """List orders for current user (paper from DB; live from broker)."""
    product, paper_live = get_product_and_paper_live(db, user_id)
    gateway = get_user_gateway(db, user_id)
    rows = opm_get_orders(db, user_id, paper_live, gateway)
    return [
        OrderResponse(
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
        for o in rows
    ]


@router.post("/cancel", response_model=dict)
def cancel_order(
    body: OrderCancelRequest,
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> dict:
    """Cancel an open order. Paper: use order_id (our DB id). Live: use broker_order_id."""
    if body.order_id is not None:
        order = db.execute(
            select(Order).where(Order.id == body.order_id, Order.user_id == user_id)
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        if order.paper_live != "paper":
            raise HTTPException(status_code=400, detail="Use broker_order_id to cancel live orders")
        if order.status not in ("PENDING", "OPEN", "TRIGGER PENDING"):
            raise HTTPException(status_code=400, detail=f"Order status is {order.status}, cannot cancel")
        order.status = "CANCELLED"
        db.commit()
        return {"ok": True, "message": "Order cancelled"}
    if body.broker_order_id:
        _, paper_live = get_product_and_paper_live(db, user_id)
        if paper_live != "live":
            raise HTTPException(status_code=400, detail="broker_order_id is for live orders only")
        gateway = get_user_gateway(db, user_id)
        if gateway is None:
            raise HTTPException(status_code=400, detail="Broker not configured")
        try:
            gateway.cancel_order(body.broker_order_id)
            return {"ok": True, "message": "Cancel sent to broker"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    raise HTTPException(status_code=400, detail="Provide order_id (paper) or broker_order_id (live)")


@router.get("/positions", response_model=list[PositionResponse])
def list_positions(
    user_id: CurrentUserId,
    db: Session = Depends(get_db),
) -> list[PositionResponse]:
    """List positions for current user (paper from DB; live from broker)."""
    _, paper_live = get_product_and_paper_live(db, user_id)
    gateway = get_user_gateway(db, user_id)
    rows = opm_get_positions(db, user_id, paper_live, gateway)
    return [
        PositionResponse(
            symbol=p["symbol"],
            exchange=p["exchange"],
            side=p["side"],
            quantity=p["quantity"],
            average_price=p["average_price"],
            product=p["product"],
            paper_live=p["paper_live"],
        )
        for p in rows
    ]
