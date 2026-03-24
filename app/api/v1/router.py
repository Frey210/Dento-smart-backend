from fastapi import APIRouter

from app.api.v1 import admin, auth, dashboard, devices, export, patients, sensor_data, sessions


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(sensor_data.router, prefix="/sensor-data", tags=["sensor-data"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
