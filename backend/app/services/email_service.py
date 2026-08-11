"""Отправка email через Resend (этап 5)."""

from __future__ import annotations

import logging
import os
from datetime import date, time
from html import escape

import resend

from app.services.client_email import is_synthetic_client_email

logger = logging.getLogger(__name__)

# Отправитель после верификации домена в Resend
SENDER_EMAIL = "info@mrboka.com"
SENDER_NAME = "Människans Resurser"


def send_email(to: str, subject: str, html: str) -> bool:
    """
    Отправить одно письмо через Resend.
    API-ключ — из RESEND_API_KEY. Ошибка отправки не пробрасывается наверх.
    """
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.warning(
            "Email пропущен (нет RESEND_API_KEY): to=%s subject=%s",
            to,
            subject,
        )
        return False

    try:
        resend.api_key = api_key
        resend.Emails.send(
            {
                "from": f"{SENDER_NAME} <{SENDER_EMAIL}>",
                "to": [to],
                "subject": subject,
                "html": html,
            }
        )
        logger.info("Email отправлен: to=%s subject=%s", to, subject)
        return True
    except Exception:
        # Сбой письма не должен ронять создание записи
        logger.exception("Не удалось отправить email: to=%s subject=%s", to, subject)
        return False


def render_client_booking_email(
    *,
    client_name: str,
    therapist_name: str,
    service_name: str,
    booking_date: date,
    booking_time: time,
    telegram_deep_link: str,
    email_confirm_link: str | None = None,
) -> str:
    """HTML-шаблон клиенту: детали + Telegram и/или e-post-подтверждение."""
    when = f"{booking_date.isoformat()} kl. {booking_time.strftime('%H:%M')}"
    name = escape(client_name)
    therapist = escape(therapist_name)
    service = escape(service_name)
    tg_link = escape(telegram_deep_link, quote=True)
    tg_text = escape(telegram_deep_link)

    email_block = ""
    if email_confirm_link:
        em_link = escape(email_confirm_link, quote=True)
        em_text = escape(email_confirm_link)
        email_block = f"""
            <p style="text-align:center;margin:0 0 12px;">
              <a href="{em_link}"
                 style="display:inline-block;background:#1a5f4a;color:#ffffff;text-decoration:none;font-weight:700;padding:14px 28px;border-radius:999px;">
                Bekräfta via e-post
              </a>
            </p>
            <p style="margin:0 0 20px;font-size:13px;line-height:1.5;color:#7a7a8a;text-align:center;">
              Har du inte Telegram? Använd knappen ovan.<br>
              <a href="{em_link}" style="color:#1a5f4a;word-break:break-all;">{em_text}</a>
            </p>
"""

    return f"""<!DOCTYPE html>
<html lang="sv">
<head><meta charset="UTF-8"><title>Bekräfta din bokning</title></head>
<body style="margin:0;padding:0;background:#f7f5f1;font-family:Arial,Helvetica,sans-serif;color:#1a1a2e;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f7f5f1;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e4e2dc;">
        <tr>
          <td style="background:#1a5f4a;padding:24px 28px;">
            <p style="margin:0;font-size:14px;letter-spacing:0.08em;text-transform:uppercase;color:#e0c040;">Människans Resurser</p>
            <h1 style="margin:8px 0 0;font-size:24px;line-height:1.3;color:#ffffff;">Din bokning är mottagen</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <p style="margin:0 0 16px;font-size:16px;line-height:1.6;">Hej {name}!</p>
            <p style="margin:0 0 20px;font-size:16px;line-height:1.6;">
              Tack för din bokning. Bekräfta tiden via Telegram eller e-post så att vi kan reservera platsen.
            </p>
            <table role="presentation" width="100%" style="background:#eef6f2;border-radius:12px;margin-bottom:24px;">
              <tr><td style="padding:18px 20px;font-size:15px;line-height:1.7;">
                <strong>Behandlare:</strong> {therapist}<br>
                <strong>Tjänst:</strong> {service}<br>
                <strong>Tid:</strong> {when}
              </td></tr>
            </table>
            <p style="text-align:center;margin:0 0 12px;">
              <a href="{tg_link}"
                 style="display:inline-block;background:#c9a227;color:#1a1a2e;text-decoration:none;font-weight:700;padding:14px 28px;border-radius:999px;">
                Bekräfta i Telegram
              </a>
            </p>
            <p style="margin:0 0 16px;font-size:13px;line-height:1.5;color:#7a7a8a;text-align:center;">
              Om knappen inte fungerar, öppna länken:<br>
              <a href="{tg_link}" style="color:#1a5f4a;word-break:break-all;">{tg_text}</a>
            </p>
            {email_block}
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 24px;font-size:12px;color:#7a7a8a;border-top:1px solid #e4e2dc;">
            Människans Resurser · mrboka.com · mail@mr-ab.se · 08-33 49 08
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def render_therapist_booking_email(
    *,
    client_name: str,
    client_phone: str,
    client_email: str,
    therapist_name: str,
    service_name: str,
    booking_date: date,
    booking_time: time,
) -> str:
    """HTML-шаблон терапевту: новая запись + контакты клиента."""
    when = f"{booking_date.isoformat()} kl. {booking_time.strftime('%H:%M')}"
    name = escape(client_name)
    phone = escape(client_phone)
    email = escape(client_email)
    therapist = escape(therapist_name)
    service = escape(service_name)

    return f"""<!DOCTYPE html>
<html lang="sv">
<head><meta charset="UTF-8"><title>Ny bokning</title></head>
<body style="margin:0;padding:0;background:#f7f5f1;font-family:Arial,Helvetica,sans-serif;color:#1a1a2e;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f7f5f1;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e4e2dc;">
        <tr>
          <td style="background:#0d3d2f;padding:24px 28px;">
            <p style="margin:0;font-size:14px;letter-spacing:0.08em;text-transform:uppercase;color:#e0c040;">Ny bokning</p>
            <h1 style="margin:8px 0 0;font-size:24px;line-height:1.3;color:#ffffff;">Väntar på Telegram-bekräftelse</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <p style="margin:0 0 16px;font-size:16px;line-height:1.6;">
              Hej {therapist}! En ny bokning har skapats.
            </p>
            <table role="presentation" width="100%" style="background:#eef6f2;border-radius:12px;margin-bottom:20px;">
              <tr><td style="padding:18px 20px;font-size:15px;line-height:1.7;">
                <strong>Klient:</strong> {name}<br>
                <strong>Telefon:</strong> {phone}<br>
                <strong>E-post:</strong> {email}<br>
                <strong>Tjänst:</strong> {service}<br>
                <strong>Tid:</strong> {when}<br>
                <strong>Status:</strong> pending
              </td></tr>
            </table>
            <p style="margin:0;font-size:14px;line-height:1.6;color:#4a4a5a;">
              Du får ett nytt meddelande i Telegram när klienten bekräftat bokningen.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 24px;font-size:12px;color:#7a7a8a;border-top:1px solid #e4e2dc;">
            Automatiskt meddelande från mrboka.com
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def notify_booking_created(
    *,
    client_name: str,
    client_email: str,
    client_phone: str,
    therapist_name: str,
    therapist_email: str,
    service_name: str,
    booking_date: date,
    booking_time: time,
    telegram_deep_link: str,
    email_confirm_link: str | None = None,
) -> None:
    """Письма клиенту и терапевту после сохранения записи в БД."""
    if not email_confirm_link:
        logger.warning(
            "Письмо без ссылки e-post-подтверждения: задай PUBLIC_API_BASE"
        )
    client_html = render_client_booking_email(
        client_name=client_name,
        therapist_name=therapist_name,
        service_name=service_name,
        booking_date=booking_date,
        booking_time=booking_time,
        telegram_deep_link=telegram_deep_link,
        email_confirm_link=email_confirm_link,
    )
    therapist_html = render_therapist_booking_email(
        client_name=client_name,
        client_phone=client_phone,
        client_email=client_email,
        therapist_name=therapist_name,
        service_name=service_name,
        booking_date=booking_date,
        booking_time=booking_time,
    )

    send_email(
        to=client_email,
        subject=f"Bekräfta din bokning — {service_name}",
        html=client_html,
    )
    send_email(
        to=therapist_email,
        subject=f"Ny bokning — {client_name}",
        html=therapist_html,
    )


def render_client_confirmed_booking_email(
    *,
    client_name: str,
    therapist_name: str,
    service_name: str,
    booking_date: date,
    booking_time: time,
) -> str:
    """HTML клиенту: бронь уже подтверждена (Telegram-flow)."""
    when = f"{booking_date.isoformat()} kl. {booking_time.strftime('%H:%M')}"
    name = escape(client_name)
    therapist = escape(therapist_name)
    service = escape(service_name)

    return f"""<!DOCTYPE html>
<html lang="sv">
<head><meta charset="UTF-8"><title>Din bokning är bekräftad</title></head>
<body style="margin:0;padding:0;background:#f7f5f1;font-family:Arial,Helvetica,sans-serif;color:#1a1a2e;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f7f5f1;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e4e2dc;">
        <tr>
          <td style="background:#1a5f4a;padding:24px 28px;">
            <p style="margin:0;font-size:14px;letter-spacing:0.08em;text-transform:uppercase;color:#e0c040;">Människans Resurser</p>
            <h1 style="margin:8px 0 0;font-size:24px;line-height:1.3;color:#ffffff;">Din bokning är bekräftad ✅</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <p style="margin:0 0 16px;font-size:16px;line-height:1.6;">Hej {name}!</p>
            <p style="margin:0 0 20px;font-size:16px;line-height:1.6;">
              Tack! Din tid är bekräftad. Vi ser fram emot att träffa dig.
            </p>
            <table role="presentation" width="100%" style="background:#eef6f2;border-radius:12px;margin-bottom:24px;">
              <tr><td style="padding:18px 20px;font-size:15px;line-height:1.7;">
                <strong>Behandlare:</strong> {therapist}<br>
                <strong>Tjänst:</strong> {service}<br>
                <strong>Tid:</strong> {when}
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 24px;font-size:12px;color:#7a7a8a;border-top:1px solid #e4e2dc;">
            Människans Resurser · mrboka.com · mail@mr-ab.se · 08-33 49 08
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def render_therapist_confirmed_booking_email(
    *,
    client_name: str,
    client_phone: str,
    client_email: str,
    therapist_name: str,
    service_name: str,
    booking_date: date,
    booking_time: time,
) -> str:
    """HTML терапевту: бронь уже подтверждена (Telegram-flow)."""
    when = f"{booking_date.isoformat()} kl. {booking_time.strftime('%H:%M')}"
    name = escape(client_name)
    phone = escape(client_phone)
    email = escape(client_email)
    therapist = escape(therapist_name)
    service = escape(service_name)

    return f"""<!DOCTYPE html>
<html lang="sv">
<head><meta charset="UTF-8"><title>Ny bekräftad bokning</title></head>
<body style="margin:0;padding:0;background:#f7f5f1;font-family:Arial,Helvetica,sans-serif;color:#1a1a2e;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f7f5f1;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #e4e2dc;">
        <tr>
          <td style="background:#0d3d2f;padding:24px 28px;">
            <p style="margin:0;font-size:14px;letter-spacing:0.08em;text-transform:uppercase;color:#e0c040;">Ny bokning</p>
            <h1 style="margin:8px 0 0;font-size:24px;line-height:1.3;color:#ffffff;">Bekräftad via Telegram ✅</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <p style="margin:0 0 16px;font-size:16px;line-height:1.6;">
              Hej {therapist}! En ny bokning har bekräftats.
            </p>
            <table role="presentation" width="100%" style="background:#eef6f2;border-radius:12px;margin-bottom:20px;">
              <tr><td style="padding:18px 20px;font-size:15px;line-height:1.7;">
                <strong>Klient:</strong> {name}<br>
                <strong>Telefon:</strong> {phone}<br>
                <strong>E-post:</strong> {email}<br>
                <strong>Tjänst:</strong> {service}<br>
                <strong>Tid:</strong> {when}<br>
                <strong>Status:</strong> confirmed
              </td></tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px 24px;font-size:12px;color:#7a7a8a;border-top:1px solid #e4e2dc;">
            Automatiskt meddelande från mrboka.com
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def notify_telegram_booking_confirmed(
    *,
    client_name: str,
    client_email: str,
    client_phone: str,
    therapist_name: str,
    therapist_email: str,
    service_name: str,
    booking_date: date,
    booking_time: time,
) -> None:
    """Письма после брони через Telegram (статус уже confirmed)."""
    therapist_html = render_therapist_confirmed_booking_email(
        client_name=client_name,
        client_phone=client_phone,
        client_email=client_email,
        therapist_name=therapist_name,
        service_name=service_name,
        booking_date=booking_date,
        booking_time=booking_time,
    )
    send_email(
        to=therapist_email,
        subject=f"Ny bekräftad bokning — {client_name}",
        html=therapist_html,
    )

    if is_synthetic_client_email(client_email):
        return

    client_html = render_client_confirmed_booking_email(
        client_name=client_name,
        therapist_name=therapist_name,
        service_name=service_name,
        booking_date=booking_date,
        booking_time=booking_time,
    )
    send_email(
        to=client_email,
        subject=f"Din bokning är bekräftad — {service_name}",
        html=client_html,
    )
