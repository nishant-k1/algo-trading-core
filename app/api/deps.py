"""Shared API dependencies: re-export for routes."""

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.session import get_db
from app.core.security import get_current_user_id, CurrentUserId
from app.db.models.user_settings import UserSettings
from app.engines.broker.registry import get_gateway

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.engines.broker.base import BrokerGateway


def get_user_gateway(db: "Session", user_id: int) -> "BrokerGateway | None":
    """Return broker gateway for the user's active broker and stored tokens."""
    result = db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    row = result.scalar_one_or_none()
    if row is None:
        return get_gateway("zerodha")
    return get_gateway(
        row.active_broker_id,
        zerodha_access_token=row.zerodha_access_token or "",
        groww_access_token=row.groww_access_token or "",
    )


__all__ = ["get_db", "get_current_user_id", "CurrentUserId", "get_user_gateway"]
