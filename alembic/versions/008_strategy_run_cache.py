"""Strategy run cache table.

Revision ID: 008
Revises: 007
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strategy_run_cache",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("signals_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("symbols_scanned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("symbols_filtered_by_gap", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("strategy_run_cache")
