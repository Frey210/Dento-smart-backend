from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.analytics.dataset_builder import build_dataset_rows, dataset_to_csv
from app.core.security import get_current_user
from app.export.service import annotate_rows, build_csv, build_pdf, build_xlsx
from app.models.session import Session
from app.models.patient import Patient
from app.services.event_marker_service import list_event_markers
from app.schemas.sensor_data import SensorDataOut
from uuid import UUID

from app.services.sensor_data_service import get_session_data


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/{session_id}")
async def export_session_data(
    session_id: UUID,
    format: str = "csv",
    include_patient: bool = False,
    db: AsyncSession = Depends(get_db),
):
    rows = await get_session_data(db, session_id)
    if not rows:
        raise HTTPException(status_code=404, detail="No data for session.")

    markers = await list_event_markers(db, session_id)
    patient = None
    if include_patient:
        session_result = await db.execute(select(Session).where(Session.id == session_id))
        session = session_result.scalar_one_or_none()
        if session and session.patient_id:
            patient_result = await db.execute(
                select(Patient).where(Patient.id == session.patient_id)
            )
            patient = patient_result.scalar_one_or_none()

    annotated_rows = annotate_rows(rows, markers, patient)

    fmt = format.lower()
    if fmt == "json":
        return JSONResponse(content=jsonable_encoder(annotated_rows))

    if fmt in {"xlsx", "excel"}:
        xlsx_data = build_xlsx(annotated_rows)
        return StreamingResponse(
            iter([xlsx_data]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=session-{session_id}.xlsx"},
        )

    if fmt == "pdf":
        pdf_data = build_pdf(annotated_rows)
        return StreamingResponse(
            iter([pdf_data]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=session-{session_id}.pdf"},
        )

    if fmt == "csv":
        csv_data = build_csv(annotated_rows)
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=session-{session_id}.csv"},
        )

    raise HTTPException(status_code=400, detail="Unsupported export format.")


@router.get("/dataset/{session_id}")
async def export_dataset(
    session_id: UUID,
    format: str = "csv",
    db: AsyncSession = Depends(get_db),
):
    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    rows = await get_session_data(db, session_id)
    dataset = build_dataset_rows(rows, session)

    if format.lower() == "json":
        return JSONResponse(content=jsonable_encoder(dataset))

    if format.lower() == "csv":
        csv_data = dataset_to_csv(dataset)
        return StreamingResponse(
            iter([csv_data]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=dataset-{session_id}.csv"},
        )

    raise HTTPException(status_code=400, detail="Unsupported export format.")
