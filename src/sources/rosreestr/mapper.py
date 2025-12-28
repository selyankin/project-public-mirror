"""Маппинг DTO Росреестра в нормализованную модель."""

from __future__ import annotations

from datetime import date, datetime

from sources.rosreestr.dto import RosreestrInquiryDto, RosreestrObjectDto
from sources.rosreestr.models import RosreestrHouseNormalized

__all__ = ['map_object_to_normalized']


def map_object_to_normalized(
    obj: RosreestrObjectDto | None,
) -> RosreestrHouseNormalized | None:
    """Преобразовать DTO объекта Росреестра в доменную модель."""

    if obj is None:
        return None

    inquiry = obj.inquiry or RosreestrInquiryDto()
    return RosreestrHouseNormalized(
        cad_number=obj.cadNumber,
        readable_address=_get_readable_address(obj),
        object_type=obj.objectType,
        purpose=obj.purpose,
        is_actual=_map_is_actual(obj.status),
        status=obj.status,
        area_total=_parse_float(obj.area),
        level=_parse_int(obj.level),
        underground_floors=_parse_int(obj.undergroundFloors),
        wall_material=obj.wallMaterial,
        commissioning_year=_parse_int(obj.commissioningYear),
        year_build=_parse_int(obj.yearBuild),
        cadastral_value=_parse_float(obj.cadCost),
        cadastral_value_date=_parse_date(obj.cadUnitDate),
        info_update_date=_parse_date(obj.infoUpdate),
        reg_date=_parse_date(obj.regDate),
        encumbrances_count=_count(obj.encumbrances),
        rights_count=_count(obj.rights),
        inquiry_price=_parse_float(inquiry.price),
        inquiry_balance=_parse_float(inquiry.balance),
        inquiry_speed=_parse_int(inquiry.speed),
        inquiry_attempts=_parse_int(inquiry.attempts),
    )


def _get_readable_address(obj: RosreestrObjectDto) -> str | None:
    """Вернуть человекочитаемый адрес."""

    return obj.address.readableAddress if obj.address is not None else None


def _map_is_actual(status: str | None) -> bool | None:
    """Определить актуальность по статусу."""

    if status == '1':
        return True

    if status == '0':
        return False

    return None


def _parse_float(value: str | None) -> float | None:
    """Преобразовать значение в float."""

    if value is None:
        return None

    normalized = value.strip().replace(' ', '').replace(',', '.')
    if not normalized:
        return None

    try:
        return float(normalized)
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    """Преобразовать значение в int."""

    if value is None:
        return None

    normalized = value.strip()
    if not normalized:
        return None

    try:
        return int(float(normalized.replace(',', '.')))
    except ValueError:
        return None


def _parse_date(value: str | None) -> date | None:
    """Преобразовать строку в дату."""

    if value is None:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    formats = ('%d.%m.%Y', '%d.%m.%y', '%Y-%m-%d')
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    return None


def _count(items: list[object] | None) -> int | None:
    """Посчитать количество элементов в списке."""

    if items is None:
        return None
    return len(items)
