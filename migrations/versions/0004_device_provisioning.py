"""add device owner and seed provisioned devices

Revision ID: 0004_device_provisioning
Revises: 0003_partition_sensor_data
Create Date: 2026-03-17 00:00:00
"""
from __future__ import annotations

from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004_device_provisioning"
down_revision = "0003_partition_sensor_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "devices",
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_devices_owner_id", "devices", ["owner_id"])

    now = datetime.utcnow()
    conn = op.get_bind()
    for idx in range(1, 21):
        device_uid = f"ESP32-C3-{idx:03d}"
        conn.execute(
            sa.text(
                """
                INSERT INTO devices (
                    id,
                    owner_id,
                    device_uid,
                    device_name,
                    firmware_version,
                    status,
                    battery_level,
                    last_seen,
                    device_api_key_hash,
                    created_at,
                    updated_at
                )
                VALUES (
                    :id,
                    NULL,
                    :device_uid,
                    :device_name,
                    :firmware_version,
                    :status,
                    NULL,
                    NULL,
                    NULL,
                    :created_at,
                    :updated_at
                )
                ON CONFLICT (device_uid) DO NOTHING
                """
            ),
            {
                "id": uuid.uuid4(),
                "device_uid": device_uid,
                "device_name": f"Provisioned Device {idx:03d}",
                "firmware_version": "1.0.0",
                "status": "offline",
                "created_at": now,
                "updated_at": now,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_devices_owner_id", table_name="devices")
    op.drop_column("devices", "owner_id")
