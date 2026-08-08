"""Хендлеры staff: приветствие и список актуальных броней."""

from __future__ import annotations

import logging
from html import escape
from typing import assert_never

from aiogram import F, Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.db import get_session_factory
from app.models.booking import Booking
from app.models.staff import StaffMember, StaffRole
from app.services.staff_access import get_active_staff_by_telegram_id
from app.services.staff_bookings import (
    format_booking_card,
    format_therapist_group_header,
    group_bookings_by_therapist,
    list_active_bookings_for_staff,
    mailto_url,
    telegram_user_url,
)

logger = logging.getLogger(__name__)

router = Router(name="staff")


class StaffCb(CallbackData, prefix="staff"):
    """callback_data для кнопок staff-меню."""

    action: str


def _first_name(staff: StaffMember) -> str:
    return staff.name.split()[0] if staff.name.strip() else staff.name


def _role_line_sv(staff: StaffMember) -> str:
    if staff.role is StaffRole.superuser:
        return (
            "Du är inloggad som administratör och ser alla bokningar "
            "(grupperade per behandlare)."
        )
    if staff.role is StaffRole.therapist:
        return "Du är inloggad som behandlare och ser dina egna bokningar."
    assert_never(staff.role)


def staff_welcome_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Visa aktuella bokningar",
                    callback_data=StaffCb(action="list").pack(),
                )
            ]
        ]
    )


def booking_contact_keyboard(
    *,
    client_email: str,
    client_name: str,
    client_telegram_id: int | None,
    booking: Booking,
) -> InlineKeyboardMarkup:
    """Всегда обе кнопки: Telegram + E-post (mailto)."""
    if client_telegram_id is not None and client_telegram_id > 0:
        tg_button = InlineKeyboardButton(
            text="💬 Kontakta via Telegram",
            url=telegram_user_url(client_telegram_id),
        )
    else:
        # Не скрываем кнопку — объясняем, что клиент ещё не в Telegram
        tg_button = InlineKeyboardButton(
            text="💬 Kontakta via Telegram",
            callback_data=StaffCb(action="no_tg").pack(),
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [tg_button],
            [
                InlineKeyboardButton(
                    text="✉️ Kontakta via e-post",
                    url=mailto_url(
                        to_email=client_email,
                        client_name=client_name,
                        booking=booking,
                    ),
                )
            ],
        ]
    )


async def send_staff_welcome(message: Message, staff: StaffMember) -> None:
    """Приветствие для Viktoria / Iwona / Boris / Jan."""
    text = (
        f"Hej {escape(_first_name(staff))}! 👋\n\n"
        f"{escape(_role_line_sv(staff))}\n\n"
        "Tryck på knappen nedan för att se aktuella bokningar "
        "(pending och bekräftade — status syns tydligt)."
    )
    await message.answer(text, reply_markup=staff_welcome_keyboard())


@router.callback_query(StaffCb.filter(F.action == "no_tg"))
async def on_no_telegram(callback: CallbackQuery, callback_data: StaffCb) -> None:
    """Клиент ещё не подтвердил через Telegram — нет telegram_id."""
    del callback_data
    await callback.answer(
        "Klienten har inte bekräftat via Telegram ännu "
        "(ingen Telegram-kontakt). Använd e-post-knappen.",
        show_alert=True,
    )


@router.callback_query(StaffCb.filter(F.action == "list"))
async def on_list_bookings(callback: CallbackQuery, callback_data: StaffCb) -> None:
    """Список броней: свои (therapist) или все с группами (superuser)."""
    del callback_data
    user = callback.from_user
    if user is None:
        await callback.answer()
        return

    session = get_session_factory()()
    try:
        staff = get_active_staff_by_telegram_id(session, user.id)
        if staff is None:
            await callback.answer("Ingen behörighet.", show_alert=True)
            return

        role = staff.role
        bookings = list_active_bookings_for_staff(session, staff)
        is_super = role is StaffRole.superuser

        # Собираем исходящие сообщения до close()
        outgoing: list[tuple[str, InlineKeyboardMarkup | None]] = []

        if not bookings:
            pass
        elif is_super:
            groups = group_bookings_by_therapist(bookings)
            global_i = 0
            total = len(bookings)
            for therapist_name, group in groups:
                outgoing.append(
                    (format_therapist_group_header(therapist_name, len(group)), None)
                )
                for booking in group:
                    global_i += 1
                    text = format_booking_card(
                        booking,
                        index=global_i,
                        total=total,
                        show_therapist=True,
                    )
                    kb = booking_contact_keyboard(
                        client_email=booking.client.email,
                        client_name=booking.client.name,
                        client_telegram_id=booking.client.telegram_id,
                        booking=booking,
                    )
                    outgoing.append((text, kb))
        else:
            total = len(bookings)
            for i, booking in enumerate(bookings, start=1):
                text = format_booking_card(
                    booking,
                    index=i,
                    total=total,
                    show_therapist=False,
                )
                kb = booking_contact_keyboard(
                    client_email=booking.client.email,
                    client_name=booking.client.name,
                    client_telegram_id=booking.client.telegram_id,
                    booking=booking,
                )
                outgoing.append((text, kb))
    finally:
        session.close()

    await callback.answer()

    if callback.message is None:
        return

    if not outgoing:
        await callback.message.answer(
            "Inga aktuella bokningar just nu.\n"
            "(Visar pending och bekräftade tider som ännu inte passerat.)"
        )
        return

    await callback.message.answer(
        f"Aktuella bokningar: {sum(1 for _, kb in outgoing if kb is not None)}\n"
        "Status: ⏳ pending · ✅ bekräftad"
    )
    for text, kb in outgoing:
        try:
            if kb is None:
                await callback.message.answer(text)
            else:
                await callback.message.answer(text, reply_markup=kb)
        except Exception:
            logger.exception(
                "Не удалось отправить карточку брони, пробуем без кнопок"
            )
            await callback.message.answer(text)
