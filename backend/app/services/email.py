"""Отправка email. Полные HTML-шаблоны — этап 5 (Resend)."""

from __future__ import annotations

import logging
from datetime import date, time

import resend

from app.config import Settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html_body: str, settings: Settings) -> bool:
    """
    Отправить письмо.
    На этапе 2: если нет RESEND_API_KEY — только лог, без ошибки.
    На этапе 5 подключим полноценный Resend + шаблоны.
    """
    if not settings.resend_api_key:
        logger.warning(
            "Email пропущен (нет RESEND_API_KEY): to=%s subject=%s",
            to,
            subject,
        )
        return False

    try:
        resend.api_key = settings.resend_api_key
        resend.Emails.send(
            {
                "from": settings.email_from,
                "to": [to],
                "subject": subject,
                "html": html_body,
            }
        )
        logger.info("Email отправлен: to=%s subject=%s", to, subject)
        return True
    except Exception:
        # Сбой письма не должен ронять создание записи
        logger.exception("Не удалось отправить email: to=%s subject=%s", to, subject)
        return False


def notify_booking_created(
    *,
    settings: Settings,
    client_name: str,
    client_email: str,
    client_phone: str,
    therapist_name: str,
    therapist_email: str,
    service_name: str,
    booking_date: date,
    booking_time: time,
    telegram_deep_link: str,
) -> None:
    """Письма клиенту и терапевту после создания записи."""
    when = f"{booking_date.isoformat()} {booking_time.strftime('%H:%M')}"

    client_html = f"""
    <h2>Din bokning är mottagen</h2>
    <p>Hej {client_name}!</p>
    <p><strong>Behandlare:</strong> {therapist_name}<br>
    <strong>Tjänst:</strong> {service_name}<br>
    <strong>Tid:</strong> {when}</p>
    <p><a href="{telegram_deep_link}">Bekräfta i Telegram</a></p>
    """
    therapist_html = f"""
    <h2>Ny bokning</h2>
    <p><strong>Klient:</strong> {client_name}<br>
    <strong>Telefon:</strong> {client_phone}<br>
    <strong>E-post:</strong> {client_email}<br>
    <strong>Tjänst:</strong> {service_name}<br>
    <strong>Tid:</strong> {when}</p>
    <p>Status: pending (väntar på Telegram-bekräftelse)</p>
    """

    try:
        send_email(
            to=client_email,
            subject=f"Bekräfta din bokning — {service_name}",
            html_body=client_html,
            settings=settings,
        )
    except Exception:
        logger.exception("Ошибка email клиенту")

    try:
        send_email(
            to=therapist_email,
            subject=f"Ny bokning — {client_name}",
            html_body=therapist_html,
            settings=settings,
        )
    except Exception:
        logger.exception("Ошибка email терапевту")
