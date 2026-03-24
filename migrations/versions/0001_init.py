"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-03-17 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("device_uid", sa.String(length=64), nullable=False),
        sa.Column("device_name", sa.String(length=128), nullable=False),
        sa.Column("firmware_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="offline"),
        sa.Column("battery_level", sa.Integer(), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("device_uid"),
    )
    op.create_index("ix_devices_device_uid", "devices", ["device_uid"])
    op.create_index("ix_devices_status", "devices", ["status"])

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=32), nullable=False),
        sa.Column("guardian_name", sa.String(length=128), nullable=False),
        sa.Column("medical_notes", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_name", sa.String(length=128), nullable=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
    )
    op.create_index("ix_sessions_status", "sessions", ["status"])

    op.create_table(
        "sensor_data",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gsr", sa.Float(), nullable=False),
        sa.Column("heart_rate", sa.Integer(), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("blood_pressure_sys", sa.Integer(), nullable=False),
        sa.Column("blood_pressure_dia", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
    )
    op.create_index("ix_sensor_data_session_id", "sensor_data", ["session_id"])
    op.create_index("ix_sensor_data_timestamp", "sensor_data", ["timestamp"])
    op.create_index("ix_sensor_data_session_timestamp", "sensor_data", ["session_id", "timestamp"])

    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("anxiety_score", sa.Float(), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
    )


def downgrade() -> None:
    op.drop_table("analysis_results")
    op.drop_index("ix_sensor_data_session_timestamp", table_name="sensor_data")
    op.drop_index("ix_sensor_data_timestamp", table_name="sensor_data")
    op.drop_index("ix_sensor_data_session_id", table_name="sensor_data")
    op.drop_table("sensor_data")
    op.drop_index("ix_sessions_status", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("patients")
    op.drop_index("ix_devices_status", table_name="devices")
    op.drop_index("ix_devices_device_uid", table_name="devices")
    op.drop_table("devices")
