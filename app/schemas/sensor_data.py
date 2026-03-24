from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SensorDataIn(BaseModel):
    device_uid: str = Field(
        validation_alias=AliasChoices("device_uid", "deviceId")
    )
    session_id: UUID | None = Field(default=None, validation_alias=AliasChoices("session_id", "sessionId"))
    timestamp: datetime
    gsr: float
    heart_rate: int = Field(validation_alias=AliasChoices("heart_rate", "heartRate"))
    temperature: float
    systolic: int = Field(validation_alias=AliasChoices("systolic", "blood_pressure_sys"))
    diastolic: int = Field(validation_alias=AliasChoices("diastolic", "blood_pressure_dia"))
    battery_level: int | None = Field(
        default=None, validation_alias=AliasChoices("battery_level", "batteryLevel")
    )

    model_config = ConfigDict(populate_by_name=True)


class SensorDataOut(BaseModel):
    id: int
    session_id: UUID
    timestamp: datetime
    gsr: float
    heart_rate: int
    temperature: float
    systolic: int = Field(validation_alias=AliasChoices("systolic", "blood_pressure_sys"))
    diastolic: int = Field(validation_alias=AliasChoices("diastolic", "blood_pressure_dia"))

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
