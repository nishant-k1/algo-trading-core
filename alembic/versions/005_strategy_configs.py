"""Strategy configs table.

Revision ID: 005
Revises: 004
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strategy_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("strategy_key", sa.String(64), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("watchlist_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["watchlist_id"], ["watchlists.id"]),
    )
    op.create_index(op.f("ix_strategy_configs_user_id"), "strategy_configs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_strategy_configs_user_id"), table_name="strategy_configs")
    op.drop_table("strategy_configs")
