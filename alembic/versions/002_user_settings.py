"""User settings table.

Revision ID: 002
Revises: 001
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("active_broker_id", sa.String(32), nullable=False, server_default="zerodha"),
        sa.Column("paper_live", sa.String(16), nullable=False, server_default="paper"),
        sa.Column("zerodha_access_token", sa.String(512), nullable=True),
        sa.Column("groww_access_token", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_settings_user_id"), "user_settings", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_settings_user_id"), table_name="user_settings")
    op.drop_table("user_settings")
