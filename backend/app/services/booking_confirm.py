"""Подтверждение брони по telegram_confirm_token (бот или e-mail-ссылка)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Booking, BookingStatus, Client, Therapist


@dataclass(frozen=True)
class ConfirmResult:
    """Результат подтверждения для ответа бота / HTML-страницы."""

    ok: bool
    message_sv: str
    booking: Booking | None = None
    therapist: Therapist | None = None
    client: Client | None = None


def _parse_confirm_token(payload: str) -> uuid.UUID | None:
    raw = (payload or "").strip()
    if raw.startswith("confirm_"):
        raw = raw[len("confirm_") :]
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def confirm_booking_by_token(
    db: Session,
    token: uuid.UUID,
    *,
    client_telegram_id: int | None = None,
) -> ConfirmResult:
    """Подтверждает бронь по UUID-токену (общий путь для бота и e-mail)."""
    booking = db.scalar(
        select(Booking)
        .options(
            joinedload(Booking.client),
            joinedload(Booking.therapist),
        )
        .where(Booking.telegram_confirm_token == token)
    )
    if booking is None:
        return ConfirmResult(
            ok=False,
            message_sv="Bokningen hittades inte. Kontakta kliniken om problemet kvarstår.",
        )

    if booking.status == BookingStatus.cancelled:
        return ConfirmResult(
            ok=False,
            message_sv="Den här bokningen är avbokad och kan inte bekräftas.",
            booking=booking,
            therapist=booking.therapist,
            client=booking.client,
        )

    if booking.status == BookingStatus.completed:
        return ConfirmResult(
            ok=False,
            message_sv="Besöket är redan markerat som genomfört.",
            booking=booking,
            therapist=booking.therapist,
            client=booking.client,
        )

    if client_telegram_id is not None and booking.client is not None:
        # Привязываем Telegram-аккаунт клиента (если слот свободен)
        other = db.scalar(
            select(Client).where(
                Client.telegram_id == client_telegram_id,
                Client.id != booking.client_id,
            )
        )
        if other is None:
            booking.client.telegram_id = client_telegram_id

    if booking.status == BookingStatus.confirmed:
        db.commit()
        time_label = booking.booking_time.strftime("%H:%M")
        return ConfirmResult(
            ok=True,
            message_sv=(
                f"Bokningen är redan bekräftad ✅\n\n"
                f"{booking.service_name}\n"
                f"{booking.booking_date.isoformat()} kl. {time_label}\n"
                f"Behandlare: {booking.therapist.name}"
            ),
            booking=booking,
            therapist=booking.therapist,
            client=booking.client,
        )

    booking.status = BookingStatus.confirmed
    db.commit()
    db.refresh(booking)

    time_label = booking.booking_time.strftime("%H:%M")
    return ConfirmResult(
        ok=True,
        message_sv=(
            f"Tack! Din bokning är bekräftad ✅\n\n"
            f"{booking.service_name}\n"
            f"{booking.booking_date.isoformat()} kl. {time_label}\n"
            f"Behandlare: {booking.therapist.name}\n\n"
            f"Vi ses på kliniken!"
        ),
        booking=booking,
        therapist=booking.therapist,
        client=booking.client,
    )


def confirm_booking_by_payload(
    db: Session,
    payload: str,
    *,
    client_telegram_id: int | None = None,
) -> ConfirmResult:
    """
    Подтверждает бронь по deep-link payload (confirm_<uuid>).
    Сохраняет telegram_id клиента, если передан.
    """
    token = _parse_confirm_token(payload)
    if token is None:
        return ConfirmResult(
            ok=False,
            message_sv=(
                "Länken är ogiltig. Öppna knappen «Bekräfta i Telegram» "
                "eller «Bekräfta via e-post» från bokningsbekräftelsen."
            ),
        )
    return confirm_booking_by_token(
        db,
        token,
        client_telegram_id=client_telegram_id,
    )


def render_confirm_html_page(result: ConfirmResult) -> str:
    """Простая HTML-страница после клика по ссылке в письме."""
    title = "Bokning bekräftad" if result.ok else "Kunde inte bekräfta"
    body = escape(result.message_sv).replace("\n", "<br>")
    accent = "#1a5f4a" if result.ok else "#8b3a3a"
    return f"""<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} — Människans Resurser</title>
</head>
<body style="margin:0;padding:0;background:#f7f5f1;font-family:Arial,Helvetica,sans-serif;color:#1a1a2e;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="padding:40px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:520px;background:#fff;border-radius:16px;border:1px solid #e4e2dc;overflow:hidden;">
        <tr>
          <td style="background:{accent};padding:22px 28px;color:#fff;">
            <p style="margin:0;font-size:13px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.9;">Människans Resurser</p>
            <h1 style="margin:8px 0 0;font-size:22px;">{escape(title)}</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;font-size:16px;line-height:1.6;">{body}</td>
        </tr>
        <tr>
          <td style="padding:16px 28px 24px;font-size:13px;color:#7a7a8a;border-top:1px solid #e4e2dc;">
            <a href="https://mrboka.com" style="color:#1a5f4a;">mrboka.com</a>
            · mail@mr-ab.se · 08-33 49 08
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
