"""Watchlists and watchlist_symbols tables.

Revision ID: 003
Revises: 002
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("is_auto_for_screener", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_watchlists_user_id"), "watchlists", ["user_id"], unique=False)

    op.create_table(
        "watchlist_symbols",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("watchlist_id", sa.Integer(), nullable=False),
        sa.Column("exchange", sa.String(16), nullable=False, server_default="NSE"),
        sa.Column("symbol", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["watchlist_id"], ["watchlists.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("watchlist_id", "exchange", "symbol", name="uq_watchlist_exchange_symbol"),
    )
    op.create_index(op.f("ix_watchlist_symbols_watchlist_id"), "watchlist_symbols", ["watchlist_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_watchlist_symbols_watchlist_id"), table_name="watchlist_symbols")
    op.drop_table("watchlist_symbols")
    op.drop_index(op.f("ix_watchlists_user_id"), table_name="watchlists")
    op.drop_table("watchlists")
