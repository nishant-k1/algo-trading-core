"""Last strategy run cache (one row per user)."""

from datetime import datetime

from sqlalchemy import Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class StrategyRunCache(Base):
    """Last run summary for dashboard."""

    __tablename__ = "strategy_run_cache"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), primary_key=True, nullable=False
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    signals_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    symbols_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    symbols_filtered_by_gap: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
