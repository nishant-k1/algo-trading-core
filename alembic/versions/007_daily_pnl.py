"""Daily P&L table for risk limit.

Revision ID: 007
Revises: 006
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_pnl",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("realized_pnl", sa.Float(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "trade_date", name="uq_daily_pnl_user_date"),
    )
    op.create_index(op.f("ix_daily_pnl_user_id"), "daily_pnl", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_daily_pnl_user_id"), table_name="daily_pnl")
    op.drop_table("daily_pnl")
