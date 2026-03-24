from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.session import Session
from app.schemas.sensor_data import SensorDataIn


async def ingest_sensor_data(
    db: AsyncSession, payload: SensorDataIn, device: Device | None = None
) -> SensorData:
    if not device:
        device_result = await db.execute(select(Device).where(Device.device_uid == payload.device_uid))
        device = device_result.scalar_one_or_none()
        if not device:
            raise ValueError("Device not found.")

    session = None
    if payload.session_id:
        session_result = await db.execute(select(Session).where(Session.id == payload.session_id))
        session = session_result.scalar_one_or_none()
    else:
        session_result = await db.execute(
            select(Session)
            .where(Session.device_id == device.id, Session.status == "active")
            .order_by(Session.started_at.desc())
            .limit(1)
        )
        session = session_result.scalar_one_or_none()

    if not session or session.status != "active":
        raise ValueError("Session not found or not active.")
    if session.device_id and session.device_id != device.id:
        raise ValueError("Device does not match active session.")

    sensor_data = SensorData(
        session_id=session.id,
        timestamp=payload.timestamp,
        gsr=payload.gsr,
        heart_rate=payload.heart_rate,
        temperature=payload.temperature,
        blood_pressure_sys=payload.systolic,
        blood_pressure_dia=payload.diastolic,
    )
    device.last_seen = datetime.now(tz=timezone.utc)
    device.status = "online"
    if payload.battery_level is not None:
        device.battery_level = payload.battery_level
    session.last_sensor_at = payload.timestamp

    db.add(sensor_data)
    await db.commit()
    await db.refresh(sensor_data)
    return sensor_data


async def get_session_data(db: AsyncSession, session_id: UUID) -> list[SensorData]:
    result = await db.execute(
        select(SensorData).where(SensorData.session_id == session_id).order_by(SensorData.timestamp)
    )
    return list(result.scalars().all())


async def get_session_summary(db: AsyncSession, session_id: UUID) -> dict[str, object]:
    result = await db.execute(
        select(
            func.count(SensorData.id),
            func.min(SensorData.timestamp),
            func.max(SensorData.timestamp),
            func.avg(SensorData.gsr),
            func.avg(SensorData.heart_rate),
            func.avg(SensorData.temperature),
            func.avg(SensorData.blood_pressure_sys),
            func.avg(SensorData.blood_pressure_dia),
        ).where(SensorData.session_id == session_id)
    )
    row = result.one()
    return {
        "session_id": session_id,
        "total_records": int(row[0] or 0),
        "first_timestamp": row[1],
        "last_timestamp": row[2],
        "avg_gsr": float(row[3]) if row[3] is not None else None,
        "avg_heart_rate": float(row[4]) if row[4] is not None else None,
        "avg_temperature": float(row[5]) if row[5] is not None else None,
        "avg_sys": float(row[6]) if row[6] is not None else None,
        "avg_dia": float(row[7]) if row[7] is not None else None,
    }
