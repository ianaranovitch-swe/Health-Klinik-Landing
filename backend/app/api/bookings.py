"""Эндпоинты бронирования."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import AppSettings, DbSession
from app.schemas.booking import BookingCreateIn, BookingCreateOut, TherapistBookingOut
from app.services.booking import create_booking, is_valid_slot_time, list_therapist_bookings

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingCreateOut, status_code=201)
def create_booking_endpoint(
    payload: BookingCreateIn,
    db: DbSession,
    settings: AppSettings,
) -> BookingCreateOut:
    """Создать запись, отправить письма, вернуть Telegram deep-link."""
    if not is_valid_slot_time(payload.time):
        raise HTTPException(
            status_code=400,
            detail="Недопустимое время. Доступны слоты 09:00–17:00 с шагом 1.5 часа.",
        )
    try:
        return create_booking(db, payload, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/therapist/{therapist_id}",
    response_model=list[TherapistBookingOut],
)
def get_therapist_bookings(
    therapist_id: int,
    db: DbSession,
) -> list[TherapistBookingOut]:
    """Список записей терапевта (для бота)."""
    try:
        return list_therapist_bookings(db, therapist_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
