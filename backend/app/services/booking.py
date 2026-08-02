"""Создание записей и deep-link в Telegram."""

from __future__ import annotations

import uuid
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.models import Booking, BookingStatus, Client, Service, Therapist
from app.schemas.booking import BookingCreateIn, BookingCreateOut, TherapistBookingOut
from app.services.email import notify_booking_created


def build_telegram_deep_link(bot_username: str, token: uuid.UUID) -> str:
    if not bot_username:
        # Пока бот не настроен — всё равно вернём формат
        return f"https://t.me/BOT_USERNAME?start=confirm_{token}"
    return f"https://t.me/{bot_username}?start=confirm_{token}"


def create_booking(
    db: Session,
    payload: BookingCreateIn,
    settings: Settings,
) -> BookingCreateOut:
    therapist = db.get(Therapist, payload.therapist_id)
    if therapist is None or not therapist.active:
        raise ValueError("Терапевт не найден или неактивен")

    service = db.get(Service, payload.service_id)
    if service is None:
        raise ValueError("Услуга не найдена")

    client = db.scalar(select(Client).where(Client.email == str(payload.email)))
    if client is None:
        client = Client(
            name=payload.name.strip(),
            phone=payload.phone.strip(),
            email=str(payload.email).lower(),
        )
        db.add(client)
        db.flush()
    else:
        # Обновим контакты на актуальные
        client.name = payload.name.strip()
        client.phone = payload.phone.strip()

    token = uuid.uuid4()
    booking = Booking(
        client_id=client.id,
        therapist_id=therapist.id,
        service_name=service.name,
        booking_date=payload.date,
        booking_time=payload.time,
        status=BookingStatus.pending,
        telegram_confirm_token=token,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    deep_link = build_telegram_deep_link(settings.bot_username, token)

    # Письма не должны ломать создание записи
    notify_booking_created(
        settings=settings,
        client_name=client.name,
        client_email=client.email,
        client_phone=client.phone,
        therapist_name=therapist.name,
        therapist_email=therapist.email,
        service_name=service.name,
        booking_date=booking.booking_date,
        booking_time=booking.booking_time,
        telegram_deep_link=deep_link,
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


def is_valid_slot_time(value: time) -> bool:
    from app.services.availability import generate_time_slots

    return value.strftime("%H:%M") in generate_time_slots()
