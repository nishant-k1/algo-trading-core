"""Order record (paper and live)."""

from sqlalchemy import String, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    """Placed order (paper: simulated; live: broker)."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    client_order_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    broker_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange: Mapped[str] = mapped_column(String(16), nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    product: Mapped[str] = mapped_column(String(16), nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    paper_live: Mapped[str] = mapped_column(String(16), nullable=False)
    filled_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "client_order_id", name="uq_orders_user_client_order_id"),
    )
