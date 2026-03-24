from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_role
from app.db.database import get_db
from app.models.user import User
from app.schemas.device import DeviceOut, DeviceProvision, DeviceRegister, DeviceUpdate
from app.services.device_service import (
    assign_device_to_user,
    delete_device,
    get_device_by_uid,
    list_devices,
    provision_device,
    update_device,
)


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def register_device(
    payload: DeviceRegister,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceOut:
    existing = await get_device_by_uid(db, payload.device_uid)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not provisioned.")
    if existing.owner_id and existing.owner_id != current_user.id:
        raise HTTPException(status_code=409, detail="Device already assigned.")
    device = await assign_device_to_user(db, existing, payload, current_user.id)
    return device


@router.post("/provision", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
async def provision_device_endpoint(
    payload: DeviceProvision,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> DeviceOut:
    existing = await get_device_by_uid(db, payload.device_uid)
    if existing:
        raise HTTPException(status_code=409, detail="Device already provisioned.")
    device = await provision_device(db, payload)
    return device


@router.get("", response_model=list[DeviceOut])
async def get_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DeviceOut]:
    return await list_devices(db, owner_id=current_user.id)


@router.put("/{device_uid}", response_model=DeviceOut)
async def update_device_info(
    device_uid: str,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceOut:
    device = await get_device_by_uid(db, device_uid)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
    if device.owner_id and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Device not assigned to this user.")
    return await update_device(db, device, payload)


@router.delete("/{device_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_endpoint(
    device_uid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    device = await get_device_by_uid(db, device_uid)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
    if device.owner_id and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Device not assigned to this user.")
    try:
        await delete_device(db, device)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
