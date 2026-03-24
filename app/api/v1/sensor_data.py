from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from fastapi.responses import JSONResponse

from app.core.device_auth import verify_device_key
from app.core.audit_logger import record_event
from app.core.rate_limiter import rate_limit_device
from app.db.database import get_db
from app.schemas.sensor_data import SensorDataIn, SensorDataOut
from app.services.sensor_data_service import ingest_sensor_data
from app.websocket.manager import ConnectionManager, get_manager


router = APIRouter()
logger = logging.getLogger("dento.sensor")


@router.post("", response_model=SensorDataOut, status_code=status.HTTP_201_CREATED)
async def ingest_data(
    payload: SensorDataIn,
    x_device_key: str | None = Header(default=None, alias="X-DEVICE-KEY"),
    db: AsyncSession = Depends(get_db),
    manager: ConnectionManager = Depends(get_manager),
    _rate_limit: None = Depends(rate_limit_device),
) -> SensorDataOut:
    try:
        device = await verify_device_key(payload.device_uid, x_device_key=x_device_key, db=db)
        sensor_data = await ingest_sensor_data(db, payload, device=device)
    except ValueError as exc:
        if payload.session_id is None and str(exc) == "Session not found or not active.":
            device.last_seen = datetime.now(tz=timezone.utc)
            device.status = "online"
            if payload.battery_level is not None:
                device.battery_level = payload.battery_level
            await db.commit()
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={"status": "device_online", "session_active": False},
            )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    message = jsonable_encoder(SensorDataOut.model_validate(sensor_data))
    await manager.broadcast(str(sensor_data.session_id), message)
    await record_event(
        db,
        event_type="sensor_ingestion",
        actor_type="device",
        actor_id=payload.device_uid,
        session_id=str(sensor_data.session_id),
    )
    logger.info(
        "sensor_ingestion",
        extra={
            "session_id": str(sensor_data.session_id),
            "device_uid": payload.device_uid,
            "timestamp": payload.timestamp.isoformat(),
        },
    )
    return sensor_data
