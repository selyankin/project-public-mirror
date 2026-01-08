"""Нормализованные модели GIS ЖКХ."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _to_str(value: object | None) -> str | None:
    """Нормализовать значение в строку."""
    if not value:
        return None

    text = str(value).strip()
    return text or None


def _to_float(value: object | None) -> float | None:
    """Преобразовать значение в число с плавающей точкой."""
    if not value:
        return None

    try:
        return float(str(value).replace(',', '.'))
    except ValueError:
        return None


def _to_int(value: object | None) -> int | None:
    """Преобразовать значение в целое число."""
    if not value:
        return None

    try:
        return int(float(str(value).replace(',', '.')))
    except ValueError:
        return None


@dataclass(slots=True)
class GisGkhHouseNormalized:
    """Нормализованный дом из GIS ЖКХ."""

    cadastral_number: str
    region_code: str | None = None
    house_guid: str | None = None
    house_code: str | None = None
    address: str | None = None
    management_company: str | None = None
    management_status: str | None = None
    total_area: float | None = None
    living_area: float | None = None
    floors: int | None = None
    year_built: int | None = None
    cadastre_number: str | None = None
    condition: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GisGkhHouseNormalized:
        """Построить модель из словаря API."""

        def _get_first(*keys: str) -> object | None:
            """Вернуть первое найденное значение по ключам."""

            for key in keys:
                if key in data:
                    return data.get(key)

            return None

        def _get_nested(parent_key: str, child_key: str) -> object | None:
            """Вернуть вложенное значение из словаря."""

            parent = data.get(parent_key)
            if isinstance(parent, dict):
                return parent.get(child_key)

            return None

        return cls(
            cadastral_number=_to_str(
                _get_first('cadastral_number', 'cadastreNumber'),
            )
            or '',
            region_code=_to_str(_get_first('region_code', 'regionCode')),
            house_guid=_to_str(_get_first('house_guid', 'houseGuid')),
            house_code=_to_str(_get_first('house_code', 'houseCode')),
            address=_to_str(
                _get_first(
                    'address',
                    'formattedAddress',
                    'houseTextAddress',
                ),
            ),
            management_company=_to_str(
                _get_first(
                    'management_company',
                    'managementCompany',
                )
                or _get_nested('managementOrganization', 'fullName'),
            ),
            management_status=_to_str(
                _get_first('management_status', 'managementTypeName'),
            ),
            total_area=_to_float(_get_first('total_area', 'totalSquare')),
            living_area=_to_float(
                _get_first('living_area', 'residentialSquare'),
            ),
            floors=_to_int(_get_first('floors', 'maxFloorCount')),
            year_built=_to_int(_get_first('year_built', 'buildingYear')),
            cadastre_number=_to_str(
                _get_first('cadastre_number', 'cadastreNumber'),
            ),
            condition=_to_str(
                _get_first('condition', 'houseConditionName'),
            ),
        )
