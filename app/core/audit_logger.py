from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.models.audit_log import AuditLog


async def record_event(
    db: AsyncSession,
    event_type: str,
    actor_type: str,
    actor_id: str | None = None,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            session_id=session_id,
            event_metadata=metadata,
        )
    )
    await db.commit()


async def record_event_async(
    event_type: str,
    actor_type: str,
    actor_id: str | None = None,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        await record_event(session, event_type, actor_type, actor_id, session_id, metadata)


def fire_and_forget_event(
    event_type: str,
    actor_type: str,
    actor_id: str | None = None,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    asyncio.create_task(record_event_async(event_type, actor_type, actor_id, session_id, metadata))
