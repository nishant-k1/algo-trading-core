"""Widen access token columns for long JWTs (e.g. Groww).

Revision ID: 009
Revises: 008
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "user_settings",
        "zerodha_access_token",
        existing_type=sa.String(512),
        type_=sa.String(2048),
        existing_nullable=True,
    )
    op.alter_column(
        "user_settings",
        "groww_access_token",
        existing_type=sa.String(512),
        type_=sa.String(2048),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "user_settings",
        "zerodha_access_token",
        existing_type=sa.String(2048),
        type_=sa.String(512),
        existing_nullable=True,
    )
    op.alter_column(
        "user_settings",
        "groww_access_token",
        existing_type=sa.String(2048),
        type_=sa.String(512),
        existing_nullable=True,
    )
