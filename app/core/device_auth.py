from __future__ import annotations

import hmac
import logging

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.security import verify_password
from app.db.database import get_db
from app.models.device import Device
from app.services.device_service import get_device_by_uid


logger = logging.getLogger("dento.device_auth")


async def verify_device_key(
    device_uid: str,
    x_device_key: str | None = Header(default=None, alias="X-DEVICE-KEY"),
    db: AsyncSession = Depends(get_db),
) -> Device:
    device = await get_device_by_uid(db, device_uid)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    settings = get_settings()
    if device.device_api_key_hash:
        if not x_device_key or not verify_password(x_device_key, device.device_api_key_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device key.")
        return device

    if settings.device_api_key and settings.device_api_key != "change-me":
        if not x_device_key or not hmac.compare_digest(x_device_key, settings.device_api_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid device key.")
        return device

    logger.warning("device_key_not_configured", extra={"device_uid": device_uid})
    return device
