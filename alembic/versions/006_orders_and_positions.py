"""Orders and positions tables (OPM).

Revision ID: 006
Revises: 005
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("client_order_id", sa.String(128), nullable=False),
        sa.Column("broker_order_id", sa.String(128), nullable=True),
        sa.Column("symbol", sa.String(64), nullable=False),
        sa.Column("exchange", sa.String(16), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("product", sa.String(16), nullable=False),
        sa.Column("order_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("paper_live", sa.String(16), nullable=False),
        sa.Column("filled_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_price", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "client_order_id", name="uq_orders_user_client_order_id"),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_orders_client_order_id"), "orders", ["client_order_id"], unique=False)

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(64), nullable=False),
        sa.Column("exchange", sa.String(16), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("average_price", sa.Float(), nullable=False),
        sa.Column("product", sa.String(16), nullable=False),
        sa.Column("paper_live", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint(
            "user_id", "symbol", "exchange", "side", "product", "paper_live",
            name="uq_positions_user_symbol_exchange_side_product_paper_live",
        ),
    )
    op.create_index(op.f("ix_positions_user_id"), "positions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_positions_user_id"), table_name="positions")
    op.drop_table("positions")
    op.drop_index(op.f("ix_orders_client_order_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")
