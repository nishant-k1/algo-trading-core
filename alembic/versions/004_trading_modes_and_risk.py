"""Trading modes table and risk columns on user_settings.

Revision ID: 004
Revises: 003
Create Date: 2025-02-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trading_modes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("segment", sa.String(32), nullable=False),
        sa.Column("product", sa.String(16), nullable=False),
        sa.Column("exchange", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_trading_modes_name"), "trading_modes", ["name"], unique=True)

    op.execute(
        sa.text("""
        INSERT INTO trading_modes (name, segment, product, exchange) VALUES
        ('intraday_equity', 'NSE_EQ', 'MIS', 'NSE'),
        ('swing_equity', 'NSE_EQ', 'CNC', 'NSE'),
        ('positional_equity', 'NSE_EQ', 'CNC', 'NSE'),
        ('fno', 'NSE_FNO', 'NRML', 'NSE'),
        ('commodities', 'MCX', 'NRML', 'MCX')
        """)
    )

    op.add_column("user_settings", sa.Column("active_trading_mode_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_user_settings_trading_mode",
        "user_settings",
        "trading_modes",
        ["active_trading_mode_id"],
        ["id"],
    )
    op.add_column("user_settings", sa.Column("kill_switch", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("user_settings", sa.Column("max_position_value", sa.Float(), nullable=True))
    op.add_column("user_settings", sa.Column("max_orders_per_day", sa.Integer(), nullable=True))
    op.add_column("user_settings", sa.Column("daily_loss_limit_pct", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_settings", "daily_loss_limit_pct")
    op.drop_column("user_settings", "max_orders_per_day")
    op.drop_column("user_settings", "max_position_value")
    op.drop_column("user_settings", "kill_switch")
    op.drop_constraint("fk_user_settings_trading_mode", "user_settings", type_="foreignkey")
    op.drop_column("user_settings", "active_trading_mode_id")
    op.drop_index(op.f("ix_trading_modes_name"), table_name="trading_modes")
    op.drop_table("trading_modes")
