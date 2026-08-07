"""Таблица therapists — терапевты клиники."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.associations import therapist_services
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.service import Service


class Therapist(Base):
    __tablename__ = "therapists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    specialization: Mapped[str] = mapped_column(String(300))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    bookings: Mapped[list[Booking]] = relationship(back_populates="therapist")
    services: Mapped[list[Service]] = relationship(
        secondary=therapist_services,
        back_populates="therapists",
    )

    def __repr__(self) -> str:
        return f"Therapist(id={self.id!r}, name={self.name!r}, active={self.active!r})"
