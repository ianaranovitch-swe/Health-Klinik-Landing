"""Схемы терапевта."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr


class TherapistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    specialization: str
    active: bool
