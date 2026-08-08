"""Эндпоинты бронирования."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.api.deps import AppSettings, DbSession
from app.schemas.booking import BookingCreateIn, BookingCreateOut, TherapistBookingOut
from app.services.booking import create_booking, is_valid_slot_time, list_therapist_bookings
from app.services.booking_confirm import (
    confirm_booking_by_token,
    render_confirm_html_page,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingCreateOut, status_code=201)
def create_booking_endpoint(
    payload: BookingCreateIn,
    db: DbSession,
    settings: AppSettings,
) -> BookingCreateOut:
    """Создать запись, отправить письма, вернуть Telegram deep-link."""
    if not is_valid_slot_time(payload.time, payload.date):
        raise HTTPException(
            status_code=400,
            detail=(
                "Недопустимое время. Доступны: пн–чт 11:00–18:00, "
                "пт 11:00–17:00 (шаг 30 мин). Сб–вс закрыто."
            ),
        )
    try:
        return create_booking(db, payload, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/confirm/{token}",
    response_class=HTMLResponse,
    summary="Bekräfta bokning via e-postlänk",
)
def confirm_booking_via_email(
    token: uuid.UUID,
    db: DbSession,
) -> HTMLResponse:
    """
    Клиент без Telegram нажимает ссылку в письме —
    статус становится confirmed в БД, открывается HTML-страница.
    """
    result = confirm_booking_by_token(db, token)
    status_code = 200 if result.ok else 400
    if result.booking is None and not result.ok:
        status_code = 404
    return HTMLResponse(
        content=render_confirm_html_page(result),
        status_code=status_code,
    )


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
