"""Нормализованные модели Росреестра."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

__all__ = ['RosreestrHouseNormalized']


@dataclass(slots=True)
class RosreestrHouseNormalized:
    """Нормализованное представление объекта из Росреестра."""

    cad_number: str | None = None
    readable_address: str | None = None
    object_type: str | None = None
    purpose: str | None = None
    is_actual: bool | None = None
    status: str | None = None
    area_total: float | None = None
    level: int | None = None
    underground_floors: int | None = None
    wall_material: str | None = None
    commissioning_year: int | None = None
    year_build: int | None = None
    cadastral_value: float | None = None
    cadastral_value_date: date | None = None
    info_update_date: date | None = None
    reg_date: date | None = None
    encumbrances_count: int | None = None
    rights_count: int | None = None
    inquiry_price: float | None = None
    inquiry_balance: float | None = None
    inquiry_speed: int | None = None
    inquiry_attempts: int | None = None
