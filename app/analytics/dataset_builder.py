from __future__ import annotations

import csv
import io
from typing import Iterable

from app.models.sensor_data import SensorData
from app.models.session import Session


def build_dataset_rows(
    rows: Iterable[SensorData],
    session: Session,
    label: str | None = None,
) -> list[dict[str, object]]:
    dataset = []
    for row in rows:
        dataset.append(
            {
                "session_id": str(session.id),
                "timestamp": row.timestamp.isoformat(),
                "gsr": row.gsr,
                "heart_rate": row.heart_rate,
                "temperature": row.temperature,
                "blood_pressure_sys": row.blood_pressure_sys,
                "blood_pressure_dia": row.blood_pressure_dia,
                "label": label,
            }
        )
    return dataset


def dataset_to_csv(rows: list[dict[str, object]]) -> str:
    output = io.StringIO()
    if not rows:
        return ""
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
