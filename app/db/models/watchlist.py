"""Watchlist and watchlist symbols."""

from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base, TimestampMixin


class Watchlist(Base, TimestampMixin):
    """User watchlist (named list of symbols)."""

    __tablename__ = "watchlists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_auto_for_screener: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    symbols: Mapped[list["WatchlistSymbol"]] = relationship(
        "WatchlistSymbol",
        back_populates="watchlist",
        cascade="all, delete-orphan",
    )


class WatchlistSymbol(Base):
    """One symbol in a watchlist."""

    __tablename__ = "watchlist_symbols"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id"), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False, default="NSE")
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)

    watchlist: Mapped["Watchlist"] = relationship("Watchlist", back_populates="symbols")

    __table_args__ = (UniqueConstraint("watchlist_id", "exchange", "symbol", name="uq_watchlist_exchange_symbol"),)
