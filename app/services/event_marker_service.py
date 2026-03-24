from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_marker import EventMarker
from app.schemas.event_marker import EventMarkerCreate


async def list_event_markers(db: AsyncSession, session_id) -> list[EventMarker]:
    result = await db.execute(
        select(EventMarker).where(EventMarker.session_id == session_id).order_by(EventMarker.created_at)
    )
    return list(result.scalars().all())


async def create_event_marker(
    db: AsyncSession, session_id, payload: EventMarkerCreate
) -> EventMarker:
    marker = EventMarker(
        session_id=session_id,
        marker_type=payload.marker_type,
        note=payload.note,
    )
    db.add(marker)
    await db.commit()
    await db.refresh(marker)
    return marker
