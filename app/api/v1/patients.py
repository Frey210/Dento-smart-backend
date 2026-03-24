from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.schemas.patient import PatientCreate, PatientOut, PatientUpdate
from app.services.patient_service import create_patient, delete_patient, get_patient, list_patients, update_patient


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[PatientOut])
async def get_patients(db: AsyncSession = Depends(get_db)) -> list[PatientOut]:
    return await list_patients(db)


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient_endpoint(
    payload: PatientCreate, db: AsyncSession = Depends(get_db)
) -> PatientOut:
    return await create_patient(db, payload)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient_endpoint(
    patient_id: UUID, db: AsyncSession = Depends(get_db)
) -> PatientOut:
    patient = await get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient_endpoint(
    patient_id: UUID, payload: PatientUpdate, db: AsyncSession = Depends(get_db)
) -> PatientOut:
    patient = await get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return await update_patient(db, patient, payload)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient_endpoint(
    patient_id: UUID, db: AsyncSession = Depends(get_db)
) -> None:
    patient = await get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    try:
        await delete_patient(db, patient)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
