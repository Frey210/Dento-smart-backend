"""add event markers

Revision ID: 0006_event_markers
Revises: 0005_user_active_admin
Create Date: 2026-03-20 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0006_event_markers"
down_revision = "0005_user_active_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_markers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id"),
            nullable=False,
        ),
        sa.Column("marker_type", sa.String(length=64), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_event_markers_session_id", "event_markers", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_event_markers_session_id", table_name="event_markers")
    op.drop_table("event_markers")
