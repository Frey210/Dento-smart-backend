from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.models.session import Session
from app.schemas.patient import PatientCreate, PatientUpdate


async def list_patients(db: AsyncSession) -> list[Patient]:
    result = await db.execute(select(Patient).order_by(Patient.name))
    return list(result.scalars().all())


async def create_patient(db: AsyncSession, payload: PatientCreate) -> Patient:
    patient = Patient(**payload.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_patient(db: AsyncSession, patient_id: UUID) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()


async def update_patient(db: AsyncSession, patient: Patient, payload: PatientUpdate) -> Patient:
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return patient


async def delete_patient(db: AsyncSession, patient: Patient) -> None:
    result = await db.execute(select(Session).where(Session.patient_id == patient.id).limit(1))
    if result.scalar_one_or_none():
        raise ValueError("Patient has existing sessions.")
    await db.delete(patient)
    await db.commit()
