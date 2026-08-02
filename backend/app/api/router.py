"""Корневой API-роутер."""

from __future__ import annotations

from fastapi import APIRouter

from app.api import availability, bookings, services, therapists

api_router = APIRouter(prefix="/api")
api_router.include_router(therapists.router)
api_router.include_router(services.router)
api_router.include_router(availability.router)
api_router.include_router(bookings.router)
