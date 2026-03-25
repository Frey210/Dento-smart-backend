from __future__ import annotations

import logging
import time

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.core.logging import configure_logging
from app.db.partitioning import ensure_current_month_partition
from app.websocket.manager import ConnectionManager, get_manager


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("dento.api")

app = FastAPI(title=settings.app_name)

cors_origins = list(settings.cors_origins_list())
if settings.frontend_origin:
    origin = settings.frontend_origin.strip()
    if origin and origin not in cors_origins:
        cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins and cors_origins[0] != "*" else [],
    allow_origin_regex=r"http(s)?://(?:localhost|127\.0\.0\.1)(?::\d+)?", # Allow all local ports for Flutter Edge testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def startup_tasks() -> None:
    if settings.skip_partitioning or settings.environment.lower() == "test":
        return
    await ensure_current_month_partition()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
                "client": request.client.host if request.client else None,
            },
        )
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client": request.client.host if request.client else None,
        },
    )
    return response


@app.websocket("/ws/session/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
    manager: ConnectionManager = Depends(get_manager),
) -> None:
    await manager.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)


@app.websocket("/ws/monitoring/{session_id}")
async def websocket_monitoring(
    websocket: WebSocket,
    session_id: str,
    manager: ConnectionManager = Depends(get_manager),
) -> None:
    await websocket_session(websocket, session_id, manager)
