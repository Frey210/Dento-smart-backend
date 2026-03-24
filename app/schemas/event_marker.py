from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EventMarkerCreate(BaseModel):
    marker_type: str
    note: str | None = None


class EventMarkerOut(BaseModel):
    id: UUID
    session_id: UUID
    marker_type: str
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
