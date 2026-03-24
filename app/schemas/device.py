from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    device_uid: str = Field(alias="deviceId")
    device_name: str = Field(alias="deviceName")
    firmware_version: str = Field(alias="firmware")
    status: Literal["online", "offline", "calibrating"] = "offline"
    battery_level: int | None = Field(default=None, alias="batteryLevel")
    last_seen: datetime | None = Field(default=None, alias="lastConnectionTime")

    model_config = ConfigDict(populate_by_name=True)


class DeviceCreate(DeviceBase):
    device_api_key: str | None = Field(default=None, alias="deviceApiKey")

    model_config = ConfigDict(populate_by_name=True)


class DeviceProvision(BaseModel):
    device_uid: str = Field(alias="deviceId")
    device_name: str | None = Field(default=None, alias="deviceName")
    firmware_version: str | None = Field(default=None, alias="firmware")
    status: Literal["online", "offline", "calibrating"] | None = None
    battery_level: int | None = Field(default=None, alias="batteryLevel")
    last_seen: datetime | None = Field(default=None, alias="lastConnectionTime")
    device_api_key: str | None = Field(default=None, alias="deviceApiKey")

    model_config = ConfigDict(populate_by_name=True)


class DeviceRegister(BaseModel):
    device_uid: str = Field(alias="deviceId")
    device_name: str | None = Field(default=None, alias="deviceName")
    firmware_version: str | None = Field(default=None, alias="firmware")

    model_config = ConfigDict(populate_by_name=True)


class DeviceUpdate(BaseModel):
    device_name: str | None = Field(default=None, alias="deviceName")
    firmware_version: str | None = Field(default=None, alias="firmware")
    status: Literal["online", "offline", "calibrating"] | None = None
    battery_level: int | None = Field(default=None, alias="batteryLevel")
    last_seen: datetime | None = Field(default=None, alias="lastConnectionTime")
    device_api_key: str | None = Field(default=None, alias="deviceApiKey")

    model_config = ConfigDict(populate_by_name=True)


class DeviceOut(DeviceBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
