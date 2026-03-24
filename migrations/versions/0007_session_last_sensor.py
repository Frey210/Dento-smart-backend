"""add session last sensor timestamp

Revision ID: 0007_session_last_sensor
Revises: 0006_event_markers
Create Date: 2026-03-20 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0007_session_last_sensor"
down_revision = "0006_event_markers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("last_sensor_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sessions", "last_sensor_at")
