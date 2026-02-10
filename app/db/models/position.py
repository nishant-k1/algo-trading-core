"""Position record (paper: from simulated fills; live: optional cache from broker)."""

from sqlalchemy import String, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin


class Position(Base, TimestampMixin):
    """Position (paper: our book; live: can sync from broker)."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    average_price: Mapped[float] = mapped_column(Float, nullable=False)
    product: Mapped[str] = mapped_column(String(16), nullable=False)
    paper_live: Mapped[str] = mapped_column(String(16), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "symbol", "exchange", "side", "product", "paper_live",
            name="uq_positions_user_symbol_exchange_side_product_paper_live",
        ),
    )
