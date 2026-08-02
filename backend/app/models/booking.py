"""Таблица bookings — записи на приём."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.therapist import Therapist


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    therapist_id: Mapped[int] = mapped_column(ForeignKey("therapists.id"), index=True)
    # Имя услуги на момент записи (снимок), как в ТЗ
    service_name: Mapped[str] = mapped_column(String(200))
    # Колонки в БД называются date / time (как в ТЗ); в Python — без тени builtins
    booking_date: Mapped[date] = mapped_column("date", Date, index=True)
    booking_time: Mapped[time] = mapped_column("time", Time)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus,
            name="booking_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=BookingStatus.pending,
        server_default=BookingStatus.pending.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    telegram_confirm_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        index=True,
        default=uuid.uuid4,
    )

    client: Mapped[Client] = relationship(back_populates="bookings")
    therapist: Mapped[Therapist] = relationship(back_populates="bookings")

    def __repr__(self) -> str:
        return (
            f"Booking(id={self.id!r}, date={self.booking_date!r}, "
            f"time={self.booking_time!r}, status={self.status!r})"
        )
