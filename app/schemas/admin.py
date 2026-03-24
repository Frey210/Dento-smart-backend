from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminDeviceOut(BaseModel):
    id: UUID
    device_uid: str = Field(alias="deviceId")
    device_name: str = Field(alias="deviceName")
    firmware_version: str = Field(alias="firmware")
    status: str
    battery_level: int | None = Field(default=None, alias="batteryLevel")
    last_seen: datetime | None = Field(default=None, alias="lastConnectionTime")
    owner_id: UUID | None = Field(default=None, alias="ownerId")
    owner_email: EmailStr | None = Field(default=None, alias="ownerEmail")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AdminUserOut(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserRoleUpdate(BaseModel):
    role: Literal["admin", "doctor", "researcher"]


class AdminUserStatusUpdate(BaseModel):
    is_active: bool = Field(alias="isActive")

    model_config = ConfigDict(populate_by_name=True)
