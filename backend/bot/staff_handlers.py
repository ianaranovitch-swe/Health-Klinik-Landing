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
    list_active_bookings,
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
        return "Du är inloggad som administratör och ser alla bokningar."
    if staff.role is StaffRole.therapist:
        return "Du är inloggad som behandlare och ser alla bokningar på kliniken."
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
    """Кнопки связи: Telegram (если есть id) и E-post (mailto)."""
    rows: list[list[InlineKeyboardButton]] = []
    if client_telegram_id is not None and client_telegram_id > 0:
        rows.append(
            [
                InlineKeyboardButton(
                    text="💬 Kontakta via Telegram",
                    url=telegram_user_url(client_telegram_id),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="✉️ Kontakta via e-post",
                url=mailto_url(
                    to_email=client_email,
                    client_name=client_name,
                    booking=booking,
                ),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_staff_welcome(message: Message, staff: StaffMember) -> None:
    """Приветствие для Viktoria / Iwona / Boris / Jan."""
    text = (
        f"Hej {escape(_first_name(staff))}! 👋\n\n"
        f"{escape(_role_line_sv(staff))}\n\n"
        "Tryck på knappen nedan för att se aktuella bokningar "
        "(klient, tid, behandlare och kontakt)."
    )
    await message.answer(text, reply_markup=staff_welcome_keyboard())


@router.callback_query(StaffCb.filter(F.action == "list"))
async def on_list_bookings(callback: CallbackQuery, callback_data: StaffCb) -> None:
    """Показать все актуальные брони клиники."""
    del callback_data  # нужен только фильтр
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

        bookings = list_active_bookings(session)
        cards: list[tuple[str, InlineKeyboardMarkup]] = []
        total = len(bookings)
        for i, booking in enumerate(bookings, start=1):
            text = format_booking_card(booking, index=i, total=total)
            kb = booking_contact_keyboard(
                client_email=booking.client.email,
                client_name=booking.client.name,
                client_telegram_id=booking.client.telegram_id,
                booking=booking,
            )
            cards.append((text, kb))
    finally:
        session.close()

    await callback.answer()

    if callback.message is None:
        return

    if not cards:
        await callback.message.answer(
            "Inga aktuella bokningar just nu.\n"
            "(Visar väntande och bekräftade tider som ännu inte passerat.)"
        )
        return

    await callback.message.answer(
        f"Aktuella bokningar: {len(cards)}\n"
        "Varje bokning skickas som eget meddelande ↓"
    )
    for text, kb in cards:
        try:
            await callback.message.answer(text, reply_markup=kb)
        except Exception:
            logger.exception(
                "Не удалось отправить карточку брони, пробуем без кнопок"
            )
            await callback.message.answer(text)
