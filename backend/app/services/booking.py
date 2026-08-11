"""Создание записей и deep-link в Telegram."""

from __future__ import annotations

import uuid
from datetime import date, time
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.models import Booking, BookingStatus, Client, Service, Therapist
from app.schemas.booking import BookingCreateIn, BookingCreateOut, TherapistBookingOut
from app.services.availability import generate_time_slots
from app.services.client_email import (
    is_synthetic_client_email,
    synthetic_telegram_client_email,
)
from app.services.email_service import notify_booking_created, notify_telegram_booking_confirmed

BookingChannel = Literal["web", "telegram"]


def build_telegram_deep_link(bot_username: str, token: uuid.UUID) -> str:
    if not bot_username:
        # Пока бот не настроен — всё равно вернём формат
        return f"https://t.me/BOT_USERNAME?start=confirm_{token}"
    return f"https://t.me/{bot_username}?start=confirm_{token}"


def build_email_confirm_link(public_api_base: str, token: uuid.UUID) -> str | None:
    """Ссылка подтверждения без Telegram (открывается в браузере)."""
    base = (public_api_base or "").rstrip("/")
    if not base:
        return None
    return f"{base}/api/bookings/confirm/{token}"


def _upsert_client(
    db: Session,
    *,
    name: str,
    phone: str,
    email: str,
    telegram_id: int | None = None,
) -> Client:
    """Найти или создать клиента; для Telegram — приоритет telegram_id."""
    name_clean = name.strip()
    phone_clean = phone.strip()
    email_normalized = email.lower().strip()

    client: Client | None = None

    if telegram_id is not None:
        client = db.scalar(select(Client).where(Client.telegram_id == telegram_id))

    if client is None and not is_synthetic_client_email(email_normalized):
        client = db.scalar(select(Client).where(Client.email == email_normalized))

    if client is None:
        client = Client(
            name=name_clean,
            phone=phone_clean,
            email=email_normalized,
            telegram_id=telegram_id,
        )
        db.add(client)
        db.flush()
        return client

    client.name = name_clean
    client.phone = phone_clean
    if telegram_id is not None:
        client.telegram_id = telegram_id
    if not is_synthetic_client_email(email_normalized):
        client.email = email_normalized

    return client


def create_booking(
    db: Session,
    payload: BookingCreateIn,
    settings: Settings,
    *,
    channel: BookingChannel = "web",
    client_telegram_id: int | None = None,
) -> BookingCreateOut:
    therapist = db.get(Therapist, payload.therapist_id)
    if therapist is None or not therapist.active:
        raise ValueError("Терапевт не найден или неактивен")

    service = db.get(Service, payload.service_id)
    if service is None:
        raise ValueError("Услуга не найдена")

    # Проверяем, что терапевт оказывает эту услугу
    allowed = db.scalar(
        select(Service.id).where(
            Service.id == service.id,
            Service.therapists.any(Therapist.id == therapist.id),
        )
    )
    if allowed is None:
        raise ValueError("Эта услуга недоступна у выбранного терапевта")

    email_for_db = str(payload.email).lower()
    if channel == "telegram" and client_telegram_id is not None:
        if is_synthetic_client_email(email_for_db):
            email_for_db = synthetic_telegram_client_email(client_telegram_id)

    client = _upsert_client(
        db,
        name=payload.name,
        phone=payload.phone,
        email=email_for_db,
        telegram_id=client_telegram_id if channel == "telegram" else None,
    )

    token = uuid.uuid4()
    status = (
        BookingStatus.confirmed if channel == "telegram" else BookingStatus.pending
    )
    booking = Booking(
        client_id=client.id,
        therapist_id=therapist.id,
        service_name=service.name,
        booking_date=payload.date,
        booking_time=payload.time,
        status=status,
        telegram_confirm_token=token,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    deep_link = build_telegram_deep_link(settings.bot_username, token)
    email_confirm_link = build_email_confirm_link(settings.public_api_base, token)

    # Письма не должны ломать создание записи (ошибки email только в лог)
    if channel == "telegram":
        notify_telegram_booking_confirmed(
            client_name=client.name,
            client_email=client.email,
            client_phone=client.phone,
            therapist_name=therapist.name,
            therapist_email=therapist.email,
            service_name=service.name,
            booking_date=booking.booking_date,
            booking_time=booking.booking_time,
        )
    else:
        notify_booking_created(
            client_name=client.name,
            client_email=client.email,
            client_phone=client.phone,
            therapist_name=therapist.name,
            therapist_email=therapist.email,
            service_name=service.name,
            booking_date=booking.booking_date,
            booking_time=booking.booking_time,
            telegram_deep_link=deep_link,
            email_confirm_link=email_confirm_link,
        )

    return BookingCreateOut(
        id=booking.id,
        status=booking.status,
        service_name=booking.service_name,
        date=booking.booking_date,
        time=booking.booking_time,
        therapist_name=therapist.name,
        telegram_confirm_token=booking.telegram_confirm_token,
        telegram_deep_link=deep_link,
    )


def list_therapist_bookings(
    db: Session,
    therapist_id: int,
    *,
    on_date: date | None = None,
) -> list[TherapistBookingOut]:
    therapist = db.get(Therapist, therapist_id)
    if therapist is None:
        raise ValueError("Терапевт не найден")

    stmt = (
        select(Booking)
        .options(joinedload(Booking.client))
        .where(Booking.therapist_id == therapist_id)
        .order_by(Booking.booking_date.asc(), Booking.booking_time.asc())
    )
    if on_date is not None:
        stmt = stmt.where(Booking.booking_date == on_date)

    bookings = db.scalars(stmt).unique().all()
    return [TherapistBookingOut.from_booking(b) for b in bookings]


def is_valid_slot_time(value: time, on_date: date) -> bool:
    """Проверка: день открыт и время есть в списке слотов."""
    return value.strftime("%H:%M") in generate_time_slots(on_date)
