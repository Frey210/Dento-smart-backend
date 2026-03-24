from __future__ import annotations

from datetime import datetime

import uuid

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Identity, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(start=1, increment=1), primary_key=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, index=True)
    gsr: Mapped[float] = mapped_column(Float)
    heart_rate: Mapped[int] = mapped_column(Integer)
    temperature: Mapped[float] = mapped_column(Float)
    blood_pressure_sys: Mapped[int] = mapped_column(Integer)
    blood_pressure_dia: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_sensor_data_session_timestamp", "session_id", "timestamp"),
    )
