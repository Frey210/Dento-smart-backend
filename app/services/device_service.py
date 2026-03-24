from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.security import hash_password
from app.models.device import Device
from app.models.session import Session
from app.schemas.device import DeviceProvision, DeviceRegister, DeviceUpdate


async def provision_device(db: AsyncSession, payload: DeviceProvision) -> Device:
    device_api_key_hash = None
    if payload.device_api_key:
        device_api_key_hash = hash_password(payload.device_api_key)
    device = Device(
        device_uid=payload.device_uid,
        device_name=payload.device_name or "Provisioned Device",
        firmware_version=payload.firmware_version or "unknown",
        status=payload.status or "offline",
        battery_level=payload.battery_level,
        last_seen=payload.last_seen,
        device_api_key_hash=device_api_key_hash,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


async def list_devices(db: AsyncSession, owner_id: uuid.UUID | None = None) -> list[Device]:
    query = select(Device)
    if owner_id:
        query = query.where(Device.owner_id == owner_id)
    result = await db.execute(query.order_by(Device.device_uid))
    devices = list(result.scalars().all())
    settings = get_settings()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=settings.device_offline_minutes)
    updated = False
    for device in devices:
        if device.last_seen and device.last_seen >= cutoff:
            if device.status == "offline":
                device.status = "online"
                updated = True
        else:
            if device.status == "online":
                device.status = "offline"
                updated = True
    if updated:
        await db.commit()
    return devices


async def get_device_by_uid(db: AsyncSession, device_uid: str) -> Device | None:
    result = await db.execute(select(Device).where(Device.device_uid == device_uid))
    return result.scalar_one_or_none()


async def update_device(db: AsyncSession, device: Device, payload: DeviceUpdate) -> Device:
    update_data = payload.model_dump(exclude_unset=True)
    if "device_api_key" in update_data and update_data["device_api_key"]:
        update_data["device_api_key_hash"] = hash_password(update_data.pop("device_api_key"))
    for key, value in update_data.items():
        setattr(device, key, value)
    if update_data:
        device.last_seen = update_data.get("last_seen", device.last_seen)
        device.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(device)
    return device


async def delete_device(db: AsyncSession, device: Device) -> None:
    result = await db.execute(select(Session).where(Session.device_id == device.id).limit(1))
    if result.scalar_one_or_none():
        raise ValueError("Device has existing sessions.")
    await db.delete(device)
    await db.commit()


async def assign_device_to_user(
    db: AsyncSession, device: Device, payload: DeviceRegister, owner_id: uuid.UUID
) -> Device:
    update_data = payload.model_dump(exclude_unset=True, by_alias=False)
    update_data["owner_id"] = owner_id
    for key, value in update_data.items():
        if value is not None:
            setattr(device, key, value)
    device.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(device)
    return device
