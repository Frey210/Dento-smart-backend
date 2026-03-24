from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_role
from app.db.database import get_db
from app.models.device import Device
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.admin import (
    AdminDeviceOut,
    AdminUserOut,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
)
from app.schemas.device import DeviceProvision
from app.services.device_service import get_device_by_uid, provision_device


router = APIRouter(dependencies=[Depends(require_role("admin"))])


@router.get("/devices", response_model=list[AdminDeviceOut])
async def list_all_devices(db: AsyncSession = Depends(get_db)) -> list[AdminDeviceOut]:
    result = await db.execute(
        select(Device, User).outerjoin(User, Device.owner_id == User.id).order_by(Device.device_uid)
    )
    devices = []
    for device, owner in result.all():
        devices.append(
            AdminDeviceOut(
                id=device.id,
                deviceId=device.device_uid,
                deviceName=device.device_name,
                firmware=device.firmware_version,
                status=device.status,
                batteryLevel=device.battery_level,
                lastConnectionTime=device.last_seen,
                ownerId=owner.id if owner else None,
                ownerEmail=owner.email if owner else None,
            )
        )
    return devices


@router.post("/devices/provision", response_model=AdminDeviceOut)
async def provision_device_admin(
    payload: DeviceProvision, db: AsyncSession = Depends(get_db)
) -> AdminDeviceOut:
    existing = await get_device_by_uid(db, payload.device_uid)
    if existing:
        raise HTTPException(status_code=409, detail="Device already provisioned.")
    device = await provision_device(db, payload)
    return AdminDeviceOut(
        id=device.id,
        deviceId=device.device_uid,
        deviceName=device.device_name,
        firmware=device.firmware_version,
        status=device.status,
        batteryLevel=device.battery_level,
        lastConnectionTime=device.last_seen,
        ownerId=None,
        ownerEmail=None,
    )


@router.post("/devices/{device_uid}/unassign", response_model=AdminDeviceOut)
async def unassign_device(device_uid: str, db: AsyncSession = Depends(get_db)) -> AdminDeviceOut:
    device = await get_device_by_uid(db, device_uid)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
    device.owner_id = None
    device.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(device)
    return AdminDeviceOut(
        id=device.id,
        deviceId=device.device_uid,
        deviceName=device.device_name,
        firmware=device.firmware_version,
        status=device.status,
        batteryLevel=device.battery_level,
        lastConnectionTime=device.last_seen,
        ownerId=None,
        ownerEmail=None,
    )


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[AdminUserOut]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return [AdminUserOut.model_validate(user) for user in result.scalars().all()]


@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
async def update_user_role(
    user_id: UUID, payload: AdminUserRoleUpdate, db: AsyncSession = Depends(get_db)
) -> AdminUserOut:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return AdminUserOut.model_validate(user)


@router.patch("/users/{user_id}/status", response_model=AdminUserOut)
async def update_user_status(
    user_id: UUID, payload: AdminUserStatusUpdate, db: AsyncSession = Depends(get_db)
) -> AdminUserOut:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = payload.is_active
    await db.commit()
    if not payload.is_active:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(tz=timezone.utc))
        )
        await db.commit()
    await db.refresh(user)
    return AdminUserOut.model_validate(user)
