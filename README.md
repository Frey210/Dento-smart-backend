# Dento Smart Backend (FastAPI)

Production-grade IoT telemetry backend for Dento Smart.

## Features

- Device management
- Monitoring session lifecycle
- Sensor data ingestion
- Real-time WebSocket streaming
- CSV/JSON export
- PostgreSQL persistence with Alembic migrations

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment variables (copy and edit `.env.example`):

```bash
copy .env.example .env
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Start the API:

```bash
uvicorn app.main:app --reload
```

## Docker (Local)

Build and run the stack with PostgreSQL:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

## Render Deployment

Create a Render Web Service pointing to this backend directory and use:

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required environment variables:

- `DATABASE_URL` (Render provides this)
- `SECRET_KEY`
- `DEVICE_API_KEY`
- `ENVIRONMENT`
- `FRONTEND_ORIGIN` (production frontend URL)

## Environment Variables

All configuration is loaded from environment variables. See `.env.example`.

- `APP_NAME`
- `API_PREFIX`
- `DATABASE_URL`
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `CORS_ORIGINS`
- `FRONTEND_ORIGIN`
- `LOG_LEVEL`
- `ENVIRONMENT`
- `SECRET_KEY`
- `DEVICE_API_KEY`
- `ACCESS_TOKEN_MINUTES`
- `REFRESH_TOKEN_DAYS`
- `DEVICE_RATE_LIMIT_PER_MINUTE`

## API Overview

Base URL: `http://localhost:8000`

API prefix: `/api`

Core endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/auth/me`
- `POST /api/devices`
- `GET /api/devices`
- `PUT /api/devices/{device_uid}`
- `POST /api/sessions`
- `GET /api/sessions`
- `POST /api/sessions/{session_id}/stop`
- `POST /api/sensor-data`
- `GET /api/export/{session_id}?format=csv|json`
- `GET /api/export/dataset/{session_id}?format=csv|json`
- `GET /api/dashboard/active-sessions`
- `GET /api/dashboard/device-status`
- `GET /api/dashboard/recent-sessions`
- `GET /api/dashboard/session-summary/{session_id}`

WebSocket endpoints:

- `/ws/session/{session_id}`
- `/ws/monitoring/{session_id}`

## Sensor Data Payload

```json
{
  "device_uid": "ESP32-C3-001",
  "session_id": "uuid",
  "timestamp": "2026-04-10T10:10:10Z",
  "gsr": 0.45,
  "heart_rate": 92,
  "temperature": 36.5,
  "blood_pressure_sys": 110,
  "blood_pressure_dia": 70
}
```

## Alembic

Generate a revision:

```bash
alembic revision --autogenerate -m "init"
```

Apply migrations:

```bash
alembic upgrade head
```
