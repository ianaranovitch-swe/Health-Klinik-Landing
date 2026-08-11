"""Inline-клавиатуры для клиентского бронирования."""

from __future__ import annotations

from datetime import date

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models import Service, Therapist
from app.services.availability import DEFAULT_BOOKING_DAYS_AHEAD, list_open_booking_dates


class BookingCb(CallbackData, prefix="bk"):
    """callback_data для шагов бронирования."""

    step: str
    value: str = "-"


def services_keyboard(services: list[Service]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=s.name,
                callback_data=BookingCb(step="svc", value=str(s.id)).pack(),
            )
        ]
        for s in services
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def therapists_keyboard(therapists: list[Therapist]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t.name,
                callback_data=BookingCb(step="thr", value=str(t.id)).pack(),
            )
        ]
        for t in therapists
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _format_date_label(d: date) -> str:
    """Короткая подпись даты для кнопки."""
    weekday_sv = ("mån", "tis", "ons", "tor", "fre", "lör", "sön")
    return f"{weekday_sv[d.weekday()]} {d.strftime('%d/%m')}"


def dates_keyboard(
    *,
    days_ahead: int = DEFAULT_BOOKING_DAYS_AHEAD,
) -> InlineKeyboardMarkup:
    open_days = list_open_booking_dates(days_ahead=days_ahead)
    rows = [
        [
            InlineKeyboardButton(
                text=_format_date_label(d),
                callback_data=BookingCb(step="date", value=d.isoformat()).pack(),
            )
        ]
        for d in open_days
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def times_keyboard(slots: list[str]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for slot in slots:
        row.append(
            InlineKeyboardButton(
                text=slot,
                callback_data=BookingCb(step="time", value=slot).pack(),
            )
        )
        if len(row) >= 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def skip_email_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Hoppa över",
                    callback_data=BookingCb(step="skip_email").pack(),
                )
            ]
        ]
    )


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Bekräfta bokning ✅",
                    callback_data=BookingCb(step="confirm").pack(),
                ),
                InlineKeyboardButton(
                    text="Avbryt ❌",
                    callback_data=BookingCb(step="cancel").pack(),
                ),
            ]
        ]
    )
