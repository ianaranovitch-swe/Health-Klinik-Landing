"""Шведские тексты шагов бронирования (image_url — заготовка под картинки)."""

from __future__ import annotations

from typing import TypedDict


class StepContent(TypedDict):
    text: str
    image_url: str | None


STEPS: dict[str, StepContent] = {
    "name": {
        "text": "Vad heter du?",
        "image_url": None,
    },
    "name_staff": {
        "text": "Vad heter klienten?",
        "image_url": None,
    },
    "service": {
        "text": "Vilken undersökning vill du boka?",
        "image_url": None,
    },
    "therapist": {
        "text": "Vilken behandlare vill du boka hos?",
        "image_url": None,
    },
    "date": {
        "text": "Välj datum:",
        "image_url": None,
    },
    "time": {
        "text": "Välj tid:",
        "image_url": None,
    },
    "phone": {
        "text": "Ange ditt telefonnummer:",
        "image_url": None,
    },
    "phone_staff": {
        "text": "Ange klientens telefonnummer:",
        "image_url": None,
    },
    "optional_email": {
        "text": (
            "Vill du också ange e-post för bekräftelse?\n"
            "Skriv din e-post eller tryck «Hoppa över»."
        ),
        "image_url": None,
    },
    "email_staff": {
        "text": (
            "Ange klientens e-post.\n"
            "Bekräftelselänk (Telegram + e-post) skickas dit."
        ),
        "image_url": None,
    },
}

CANCELLED_TEXT = "Bokningen avbruten. Skriv /start om du vill boka igen."
INVALID_NAME = "Ange ditt namn (minst 2 tecken)."
INVALID_NAME_STAFF = "Ange klientens namn (minst 2 tecken)."
INVALID_PHONE = (
    "Ogiltigt telefonnummer. Ange svenskt nummer, t.ex. 0701234567 eller +46701234567."
)
INVALID_EMAIL = "Ogiltig e-post. Försök igen eller tryck «Hoppa över»."
INVALID_EMAIL_STAFF = "Ogiltig e-post. Ange en giltig adress för klienten."
BOOKING_ERROR = (
    "Något gick fel när bokningen skulle sparas. "
    "Försök igen om en stund eller kontakta kliniken."
)
STAFF_BOOKING_INTRO = (
    "Du bokar tid åt en klient.\n"
    "Klienten får e-post med bekräftelselänk (Telegram + e-post) "
    "och måste bekräfta själv."
)
