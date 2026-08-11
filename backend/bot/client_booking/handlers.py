"""Хендлеры guidad klientbokning (FSM)."""

from __future__ import annotations

import logging
from datetime import date

from aiogram import Bot, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.db import get_session_factory
from app.models import Booking, Client, Service, Therapist
from app.schemas.booking import BookingCreateIn
from app.services.availability import generate_time_slots
from app.services.booking import (
    create_booking,
    is_valid_slot_time,
    synthetic_telegram_client_email,
)
from bot.client_booking.flow import (
    format_summary,
    is_valid_email,
    is_valid_name,
    normalize_phone,
    parse_booking_time,
    send_step,
)
from bot.client_booking.keyboards import (
    BookingCb,
    confirm_keyboard,
    dates_keyboard,
    services_keyboard,
    skip_email_keyboard,
    therapists_keyboard,
    times_keyboard,
)
from bot.client_booking.queries import list_bookable_services, list_therapists_for_service
from bot.client_booking.texts import (
    BOOKING_ERROR,
    CANCELLED_TEXT,
    INVALID_EMAIL,
    INVALID_NAME,
    INVALID_PHONE,
)
from bot.states.client_booking import ClientBooking
from bot.therapist_notify import notify_therapist_confirmed_booking

logger = logging.getLogger(__name__)

router = Router(name="client_booking")


async def cancel_booking_flow(message: Message, state: FSMContext) -> None:
    """Сброс FSM и сообщение об отмене."""
    await state.clear()
    await message.answer(CANCELLED_TEXT)


async def start_client_booking(message: Message, state: FSMContext) -> None:
    """Начать guidad bokning (только для klienter, не staff)."""
    await state.clear()
    await state.set_state(ClientBooking.name)
    await send_step(message, "name")


async def _go_to_date_step(message: Message, state: FSMContext) -> None:
    await state.set_state(ClientBooking.date)
    await send_step(message, "date", reply_markup=dates_keyboard())


async def _go_to_therapist_step(
    message: Message,
    state: FSMContext,
    *,
    service_id: int,
) -> None:
    session = get_session_factory()()
    try:
        therapists = list_therapists_for_service(session, service_id)
    finally:
        session.close()

    if not therapists:
        await message.answer(
            "Ingen behandlare erbjuder denna tjänst just nu. "
            "Välj en annan tjänst eller kontakta kliniken."
        )
        await state.set_state(ClientBooking.service)
        session = get_session_factory()()
        try:
            services = list_bookable_services(session)
        finally:
            session.close()
        await send_step(message, "service", reply_markup=services_keyboard(services))
        return

    if len(therapists) == 1:
        only = therapists[0]
        await state.update_data(
            therapist_id=only.id,
            therapist_name=only.name,
        )
        await message.answer(f"Du bokar hos {only.name}.")
        await _go_to_date_step(message, state)
        return

    await state.set_state(ClientBooking.therapist)
    await send_step(message, "therapist", reply_markup=therapists_keyboard(therapists))


async def _go_to_optional_email(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    summary = format_summary(data)
    await state.set_state(ClientBooking.optional_email)
    await message.answer(summary)
    await send_step(message, "optional_email", reply_markup=skip_email_keyboard())


async def _go_to_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    summary = format_summary(data)
    await state.set_state(ClientBooking.confirm)
    await message.answer(summary, reply_markup=confirm_keyboard())


@router.message(Command("avbryt"))
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Avbryt bokning när som helst."""
    if await state.get_state() is None:
        await message.answer(CANCELLED_TEXT)
        return
    await cancel_booking_flow(message, state)


@router.message(StateFilter(ClientBooking.name), F.text)
async def on_name(message: Message, state: FSMContext) -> None:
    if not is_valid_name(message.text or ""):
        await message.answer(INVALID_NAME)
        return

    await state.update_data(name=(message.text or "").strip())
    session = get_session_factory()()
    try:
        services = list_bookable_services(session)
    finally:
        session.close()

    if not services:
        await message.answer(
            "Inga tjänster är tillgängliga just nu. Kontakta kliniken."
        )
        await state.clear()
        return

    await state.set_state(ClientBooking.service)
    await send_step(message, "service", reply_markup=services_keyboard(services))


@router.callback_query(
    StateFilter(ClientBooking.service),
    BookingCb.filter(F.step == "svc"),
)
async def on_service(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return

    service_id = int(callback_data.value)
    session = get_session_factory()()
    try:
        service = session.get(Service, service_id)
        if service is None:
            await callback.message.answer("Tjänsten finns inte längre. Välj igen.")
            return
        await state.update_data(service_id=service.id, service_name=service.name)
    finally:
        session.close()

    await _go_to_therapist_step(callback.message, state, service_id=service_id)


@router.callback_query(
    StateFilter(ClientBooking.therapist),
    BookingCb.filter(F.step == "thr"),
)
async def on_therapist(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return

    therapist_id = int(callback_data.value)
    session = get_session_factory()()
    try:
        therapist = session.get(Therapist, therapist_id)
        if therapist is None or not therapist.active:
            await callback.message.answer("Behandlaren är inte tillgänglig. Välj igen.")
            return
        await state.update_data(
            therapist_id=therapist.id,
            therapist_name=therapist.name,
        )
    finally:
        session.close()

    await _go_to_date_step(callback.message, state)


@router.callback_query(
    StateFilter(ClientBooking.date),
    BookingCb.filter(F.step == "date"),
)
async def on_date(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return

    booking_date = date.fromisoformat(callback_data.value)
    slots = generate_time_slots(booking_date)
    if not slots:
        await callback.message.answer("Detta datum är stängt. Välj ett annat datum.")
        return

    await state.update_data(date=booking_date.isoformat())
    await state.set_state(ClientBooking.time)
    await send_step(callback.message, "time", reply_markup=times_keyboard(slots))


@router.callback_query(
    StateFilter(ClientBooking.time),
    BookingCb.filter(F.step == "time"),
)
async def on_time(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return

    await state.update_data(time=callback_data.value)
    await state.set_state(ClientBooking.phone)
    await send_step(callback.message, "phone")


@router.message(StateFilter(ClientBooking.phone), F.text)
async def on_phone(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text or "")
    if phone is None:
        await message.answer(INVALID_PHONE)
        return

    await state.update_data(phone=phone)
    await _go_to_optional_email(message, state)


@router.callback_query(
    StateFilter(ClientBooking.optional_email),
    BookingCb.filter(F.step == "skip_email"),
)
async def on_skip_email(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return

    user = callback.from_user
    if user is None:
        return

    await state.update_data(email=synthetic_telegram_client_email(user.id))
    await _go_to_confirm(callback.message, state)


@router.message(StateFilter(ClientBooking.optional_email), F.text)
async def on_email(message: Message, state: FSMContext) -> None:
    if not is_valid_email(message.text or ""):
        await message.answer(INVALID_EMAIL, reply_markup=skip_email_keyboard())
        return

    await state.update_data(email=(message.text or "").strip().lower())
    await _go_to_confirm(message, state)


@router.callback_query(
    StateFilter(ClientBooking.confirm),
    BookingCb.filter(F.step == "cancel"),
)
async def on_confirm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message is None:
        return
    await cancel_booking_flow(callback.message, state)


@router.callback_query(
    StateFilter(ClientBooking.confirm),
    BookingCb.filter(F.step == "confirm"),
)
async def on_confirm_booking(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    await callback.answer()
    if callback.message is None:
        return

    user = callback.from_user
    if user is None:
        return

    data = await state.get_data()
    required = (
        "name",
        "service_id",
        "therapist_id",
        "date",
        "time",
        "phone",
        "email",
    )
    if any(key not in data for key in required):
        await callback.message.answer(BOOKING_ERROR)
        await state.clear()
        return

    booking_date = date.fromisoformat(data["date"])
    booking_time = parse_booking_time(data["time"])

    if not is_valid_slot_time(booking_time, booking_date):
        await callback.message.answer(
            "Tiden är inte längre tillgänglig. Skriv /start för att börja om."
        )
        await state.clear()
        return

    payload = BookingCreateIn(
        name=data["name"],
        phone=data["phone"],
        email=data["email"],
        therapist_id=int(data["therapist_id"]),
        service_id=int(data["service_id"]),
        date=booking_date,
        time=booking_time,
    )

    session = get_session_factory()()
    try:
        settings = get_settings()
        result = create_booking(
            session,
            payload,
            settings,
            channel="telegram",
            client_telegram_id=user.id,
        )

        booking = session.get(Booking, result.id)
        client = session.get(Client, booking.client_id) if booking else None
        therapist = session.get(Therapist, int(data["therapist_id"]))

        if booking is not None and client is not None and therapist is not None:
            await notify_therapist_confirmed_booking(
                bot,
                booking=booking,
                client=client,
                therapist=therapist,
            )
    except ValueError as exc:
        logger.warning("Telegram-bokning misslyckades: %s", exc)
        await callback.message.answer(str(exc))
        return
    except Exception:
        logger.exception("Telegram-bokning: oväntat fel")
        await callback.message.answer(BOOKING_ERROR)
        return
    finally:
        session.close()

    await state.clear()
    time_label = data["time"]
    await callback.message.answer(
        "Din bokning är bekräftad ✅\n\n"
        f"{data['service_name']} med {data['therapist_name']}\n"
        f"{data['date']} kl. {time_label}\n\n"
        "Vi ser fram emot att träffa dig!"
    )
