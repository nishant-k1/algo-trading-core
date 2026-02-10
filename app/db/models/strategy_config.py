"""User strategy config: which strategy, params, watchlist for universe."""

from sqlalchemy import String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin


class StrategyConfig(Base, TimestampMixin):
    """Saved strategy config: strategy key, params, watchlist (universe)."""

    __tablename__ = "strategy_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_key: Mapped[str] = mapped_column(String(64), nullable=False)
    params: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
