"""Daily realized P&L (for risk limit)."""

from datetime import date
from sqlalchemy import Float, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class DailyPnl(Base):
    """Realized P&L per user per calendar day (paper trading)."""

    __tablename__ = "daily_pnl"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint("user_id", "trade_date", name="uq_daily_pnl_user_date"),
    )
