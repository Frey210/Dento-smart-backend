from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    name: str
    date_of_birth: date = Field(alias="dateOfBirth")
    age: int
    gender: str
    guardian_name: str = Field(alias="guardianName")
    medical_notes: str = Field(default="", alias="medicalNotes")

    model_config = ConfigDict(populate_by_name=True)


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    name: str | None = None
    date_of_birth: date | None = Field(default=None, alias="dateOfBirth")
    age: int | None = None
    gender: str | None = None
    guardian_name: str | None = Field(default=None, alias="guardianName")
    medical_notes: str | None = Field(default=None, alias="medicalNotes")

    model_config = ConfigDict(populate_by_name=True)


class PatientOut(PatientBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
