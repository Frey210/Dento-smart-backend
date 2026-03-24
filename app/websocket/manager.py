from __future__ import annotations

from collections import defaultdict
import logging
from typing import Any, DefaultDict, Set

from fastapi import WebSocket

from app.core.audit_logger import fire_and_forget_event

class ConnectionManager:
    def __init__(self) -> None:
        self._sessions: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self._logger = logging.getLogger("dento.websocket")

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sessions[session_id].add(websocket)
        self._logger.info(
            "ws_connect",
            extra={"session_id": session_id, "client": websocket.client.host if websocket.client else None},
        )
        fire_and_forget_event("device_connection", "websocket", session_id=session_id)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        self._sessions[session_id].discard(websocket)
        if not self._sessions[session_id]:
            self._sessions.pop(session_id, None)
        self._logger.info(
            "ws_disconnect",
            extra={"session_id": session_id, "client": websocket.client.host if websocket.client else None},
        )

    async def broadcast(self, session_id: str, message: dict[str, Any]) -> None:
        for websocket in list(self._sessions.get(session_id, set())):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(session_id, websocket)


manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    return manager
