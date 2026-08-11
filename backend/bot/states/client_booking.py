"""FSM для клиентского бронирования через Telegram."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ClientBooking(StatesGroup):
    """Guidad bokning steg-för-steg."""

    name = State()
    service = State()
    therapist = State()
    date = State()
    time = State()
    phone = State()
    optional_email = State()
    confirm = State()
