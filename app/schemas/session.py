from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    patient_id: UUID | None = Field(default=None, alias="patientId")
    patient_name: str | None = Field(default=None, alias="patientName")
    device_uid: str | None = Field(default=None, alias="deviceId")
    notes: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class SessionStop(BaseModel):
    ended_at: datetime | None = None
    notes: str | None = None


class SessionOut(BaseModel):
    id: UUID
    patient_id: UUID | None = Field(alias="patientId")
    patient_name: str | None = Field(alias="patientName")
    device_id: UUID | None = Field(alias="deviceId")
    status: Literal["active", "completed"]
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    date: str
    duration: str | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SessionDetailOut(BaseModel):
    id: UUID
    patient_id: UUID | None = Field(alias="patientId")
    patient_name: str | None = Field(alias="patientName")
    device_id: UUID | None = Field(alias="deviceId")
    device_uid: str | None = Field(alias="deviceUid")
    status: Literal["active", "completed"]
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SessionSummaryOut(BaseModel):
    session_id: UUID
    total_records: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None
    avg_gsr: float | None
    avg_heart_rate: float | None
    avg_temperature: float | None
    avg_sys: float | None
    avg_dia: float | None

    model_config = ConfigDict(populate_by_name=True)
