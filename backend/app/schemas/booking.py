"""Схемы бронирования."""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.booking import Booking, BookingStatus


class BookingCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=5, max_length=50)
    email: EmailStr
    therapist_id: int
    service_id: int
    date: date
    time: time


class BookingCreateOut(BaseModel):
    id: int
    status: BookingStatus
    service_name: str
    date: date
    time: time
    therapist_name: str
    telegram_confirm_token: UUID
    telegram_deep_link: str


class TherapistBookingClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    email: EmailStr


class TherapistBookingOut(BaseModel):
    id: int
    service_name: str
    date: date
    time: time
    status: BookingStatus
    created_at: datetime
    client: TherapistBookingClientOut

    @classmethod
    def from_booking(cls, booking: Booking) -> TherapistBookingOut:
        return cls(
            id=booking.id,
            service_name=booking.service_name,
            date=booking.booking_date,
            time=booking.booking_time,
            status=booking.status,
            created_at=booking.created_at,
            client=TherapistBookingClientOut.model_validate(booking.client),
        )
