from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.device import Device
from app.models.sensor_data import SensorData
from app.models.session import Session
from app.core.security import get_current_user


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/active-sessions")
async def active_sessions(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    result = await db.execute(select(func.count(Session.id)).where(Session.status == "active"))
    count = result.scalar_one()
    return {"active_sessions": int(count)}


@router.get("/device-status")
async def device_status(db: AsyncSession = Depends(get_db)) -> dict[str, dict[str, int]]:
    result = await db.execute(
        select(Device.status, func.count(Device.id)).group_by(Device.status)
    )
    summary = {row[0]: int(row[1]) for row in result.all()}
    return {"device_status": summary}


@router.get("/recent-sessions")
async def recent_sessions(db: AsyncSession = Depends(get_db)) -> dict[str, list[dict[str, str]]]:
    result = await db.execute(select(Session).order_by(Session.started_at.desc()).limit(10))
    sessions = [
        {
            "id": str(item.id),
            "patient_name": item.patient_name,
            "status": item.status,
            "started_at": item.started_at.isoformat() if item.started_at else None,
        }
        for item in result.scalars().all()
    ]
    return {"sessions": sessions}


@router.get("/session-summary/{session_id}")
async def session_summary(session_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, dict[str, float]]:
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    summary = await db.execute(
        select(
            func.avg(SensorData.gsr),
            func.avg(SensorData.heart_rate),
            func.avg(SensorData.temperature),
            func.avg(SensorData.blood_pressure_sys),
            func.avg(SensorData.blood_pressure_dia),
        ).where(SensorData.session_id == session_id)
    )
    row = summary.one()
    return {
        "summary": {
            "gsr_avg": float(row[0]) if row[0] is not None else 0.0,
            "heart_rate_avg": float(row[1]) if row[1] is not None else 0.0,
            "temperature_avg": float(row[2]) if row[2] is not None else 0.0,
            "blood_pressure_sys_avg": float(row[3]) if row[3] is not None else 0.0,
            "blood_pressure_dia_avg": float(row[4]) if row[4] is not None else 0.0,
        }
    }
