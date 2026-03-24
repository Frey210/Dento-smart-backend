from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_logger import record_event
from app.core.security import get_current_user
from app.db.database import get_db
from app.schemas.session import SessionCreate, SessionDetailOut, SessionOut, SessionStop, SessionSummaryOut
from app.schemas.event_marker import EventMarkerCreate, EventMarkerOut
from app.services.session_service import create_session, delete_session_by_id, get_session, list_sessions, stop_session
from app.services.sensor_data_service import get_session_summary
from app.services.event_marker_service import create_event_marker, list_event_markers
from app.models.device import Device
from sqlalchemy import select


router = APIRouter(dependencies=[Depends(get_current_user)])


def _format_duration(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    minutes = seconds // 60
    return f"{minutes} min"


def _to_session_out(session) -> SessionOut:
    started = session.started_at or datetime.now(tz=timezone.utc)
    date_str = started.date().isoformat()
    return SessionOut(
        id=session.id,
        patient_id=session.patient_id,
        patient_name=session.patient_name,
        device_id=session.device_id,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        date=date_str,
        duration=_format_duration(session.duration_seconds),
        notes=session.notes,
    )


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: SessionCreate, db: AsyncSession = Depends(get_db)
) -> SessionOut:
    try:
        session = await create_session(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await record_event(
        db,
        event_type="session_start",
        actor_type="system",
        actor_id=None,
        session_id=str(session.id),
    )
    return _to_session_out(session)


@router.get("", response_model=list[SessionOut])
async def get_sessions(db: AsyncSession = Depends(get_db)) -> list[SessionOut]:
    sessions = await list_sessions(db)
    return [_to_session_out(item) for item in sessions]


@router.get("/{session_id}", response_model=SessionDetailOut)
async def get_session_detail(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> SessionDetailOut:
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    device_uid = None
    if session.device_id:
        result = await db.execute(select(Device).where(Device.id == session.device_id))
        device = result.scalar_one_or_none()
        if device:
            device_uid = device.device_uid
    return SessionDetailOut(
        id=session.id,
        patient_id=session.patient_id,
        patient_name=session.patient_name,
        device_id=session.device_id,
        device_uid=device_uid,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=session.duration_seconds,
        notes=session.notes,
    )


@router.post("/{session_id}/stop", response_model=SessionOut)
async def stop_session_endpoint(
    session_id: UUID, payload: SessionStop, db: AsyncSession = Depends(get_db)
) -> SessionOut:
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    updated = await stop_session(db, session, payload)
    await record_event(
        db,
        event_type="session_stop",
        actor_type="system",
        actor_id=None,
        session_id=str(updated.id),
    )
    return _to_session_out(updated)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_endpoint(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    deleted = await delete_session_by_id(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found.")


@router.get("/{session_id}/summary", response_model=SessionSummaryOut)
async def get_session_summary_endpoint(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> SessionSummaryOut:
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    summary = await get_session_summary(db, session_id)
    return SessionSummaryOut(**summary)


@router.get("/{session_id}/markers", response_model=list[EventMarkerOut])
async def get_session_markers(
    session_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[EventMarkerOut]:
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    markers = await list_event_markers(db, session_id)
    return [EventMarkerOut.model_validate(item) for item in markers]


@router.post("/{session_id}/markers", response_model=EventMarkerOut, status_code=status.HTTP_201_CREATED)
async def add_session_marker(
    session_id: UUID,
    payload: EventMarkerCreate,
    db: AsyncSession = Depends(get_db),
) -> EventMarkerOut:
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    marker = await create_event_marker(db, session_id, payload)
    return EventMarkerOut.model_validate(marker)
