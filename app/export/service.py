from __future__ import annotations

import csv
import io
from typing import Iterable

from app.models.sensor_data import SensorData
from app.models.event_marker import EventMarker
from app.models.patient import Patient


def _compute_anxiety_score(gsr: float, heart_rate: int) -> float:
    gsr_score = max(0.0, min(1.0, gsr / 5.0))
    hr_score = max(0.0, min(1.0, (heart_rate - 60) / 60))
    score = (gsr_score * 0.6 + hr_score * 0.4) * 4
    return round(score, 1)


def annotate_rows(
    rows: Iterable[SensorData],
    markers: list[EventMarker],
    patient: Patient | None = None,
) -> list[dict]:
    sorted_markers = sorted(markers, key=lambda item: item.created_at)
    marker_index = 0
    current_marker = None
    annotated = []
    for row in rows:
        while marker_index < len(sorted_markers) and sorted_markers[marker_index].created_at <= row.timestamp:
            current_marker = sorted_markers[marker_index].marker_type
            marker_index += 1
        annotated_row = {
            "timestamp": row.timestamp.isoformat(),
            "gsr": row.gsr,
            "heart_rate": row.heart_rate,
            "temperature": row.temperature,
            "blood_pressure_sys": row.blood_pressure_sys,
            "blood_pressure_dia": row.blood_pressure_dia,
            "session_id": str(row.session_id),
            "anxiety_score": _compute_anxiety_score(row.gsr, row.heart_rate),
            "event_marker": current_marker,
        }
        if patient:
            annotated_row["patient_id"] = str(patient.id)
            annotated_row["patient_name"] = patient.name
        annotated.append(annotated_row)
    return annotated


def build_csv(rows: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    headers = list(rows[0].keys()) if rows else []
    if headers:
        writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(key) for key in headers])
    return output.getvalue()


def build_xlsx(rows: list[dict]) -> bytes:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sensor Data"
    headers = list(rows[0].keys()) if rows else []
    if headers:
        sheet.append(headers)
    for row in rows:
        sheet.append([row.get(key) for key in headers])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def build_pdf(rows: list[dict]) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    width, height = letter
    y = height - 40
    pdf.setFont("Helvetica-Bold", 10)
    header = " | ".join(list(rows[0].keys())) if rows else "session export"
    pdf.drawString(40, y, header[:120])
    pdf.setFont("Helvetica", 9)
    y -= 20
    for row in rows:
        line = " | ".join([str(row.get(key)) for key in row.keys()])
        pdf.drawString(40, y, line[:120])
        y -= 14
        if y < 40:
            pdf.showPage()
            pdf.setFont("Helvetica", 9)
            y = height - 40
    pdf.save()
    return output.getvalue()
