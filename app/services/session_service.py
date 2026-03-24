from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.event_marker import EventMarker
from app.models.sensor_data import SensorData
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionStop
from app.config.settings import get_settings


async def list_sessions(db: AsyncSession) -> list[Session]:
    await close_stale_sessions(db)
    result = await db.execute(select(Session).order_by(Session.started_at.desc()))
    return list(result.scalars().all())


async def create_session(db: AsyncSession, payload: SessionCreate) -> Session:
    await close_stale_sessions(db)
    device_id = None
    if payload.device_uid:
        device_result = await db.execute(
            select(Device).where(Device.device_uid == payload.device_uid)
        )
        device = device_result.scalar_one_or_none()
        if not device:
            raise ValueError("Device not found.")
        device_id = device.id

    session = Session(
        patient_id=payload.patient_id,
        patient_name=payload.patient_name,
        device_id=device_id,
        status="active",
        notes=payload.notes,
        started_at=datetime.now(tz=timezone.utc),
        last_sensor_at=datetime.now(tz=timezone.utc),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID) -> Session | None:
    await close_stale_sessions(db)
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def stop_session(db: AsyncSession, session: Session, payload: SessionStop) -> Session:
    ended_at = payload.ended_at or datetime.now(tz=timezone.utc)
    session.ended_at = ended_at
    session.status = "completed"
    if session.started_at:
        session.duration_seconds = int((ended_at - session.started_at).total_seconds())
    if payload.notes is not None:
        session.notes = payload.notes
    await db.commit()
    await db.refresh(session)
    return session


async def delete_session_by_id(db: AsyncSession, session_id: UUID) -> bool:
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return False
    await db.execute(delete(SensorData).where(SensorData.session_id == session_id))
    await db.execute(delete(EventMarker).where(EventMarker.session_id == session_id))
    await db.delete(session)
    await db.commit()
    return True


async def close_stale_sessions(db: AsyncSession) -> None:
    settings = get_settings()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=settings.session_inactivity_minutes)
    result = await db.execute(select(Session).where(Session.status == "active"))
    sessions = list(result.scalars().all())
    updated = False
    for session in sessions:
        last_seen = session.last_sensor_at or session.started_at
        if last_seen and last_seen < cutoff:
            session.status = "completed"
            session.ended_at = last_seen
            if session.started_at:
                session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
            updated = True
    if updated:
        await db.commit()
