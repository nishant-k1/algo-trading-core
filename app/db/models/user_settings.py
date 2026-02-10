"""User settings (active broker, paper/live, risk, etc.)."""

from sqlalchemy import String, Boolean, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    """Per-user app settings."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    active_broker_id: Mapped[str] = mapped_column(String(32), nullable=False, default="zerodha")
    paper_live: Mapped[str] = mapped_column(String(16), nullable=False, default="paper")  # paper | live
    active_trading_mode_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("trading_modes.id"), nullable=True
    )
    zerodha_access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True, default=None)
    groww_access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True, default=None)
    # Risk
    kill_switch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_position_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_orders_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_loss_limit_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
