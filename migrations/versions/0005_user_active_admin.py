"""add user active flag

Revision ID: 0005_user_active_admin
Revises: 0004_device_provisioning
Create Date: 2026-03-17 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0005_user_active_admin"
down_revision = "0004_device_provisioning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.alter_column("users", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_column("users", "is_active")
