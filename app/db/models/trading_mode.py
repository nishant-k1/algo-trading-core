"""Trading mode (intraday, swing, F&O, etc.)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin


class TradingMode(Base, TimestampMixin):
    """Predefined trading mode: segment, product, exchange."""

    __tablename__ = "trading_modes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    segment: Mapped[str] = mapped_column(String(32), nullable=False)  # NSE_EQ, NSE_FNO, MCX, etc.
    product: Mapped[str] = mapped_column(String(16), nullable=False)  # MIS, CNC, NRML
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)  # NSE, BSE, NSE FNO, MCX
