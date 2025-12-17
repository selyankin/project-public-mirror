"""DTO для работы с API ФИАС."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class FiasErrorResponse(BaseModel):
    """Ответ об ошибке от API ФИАС."""

    description: str


class FiasAddressDetails(BaseModel):
    """Детальное описание адреса в разрезе ФИАС."""

    postal_code: str | None = None
    ifns_ul: str | None = None
    ifns_fl: str | None = None
    ifns_tul: str | None = None
    ifns_tfl: str | None = None
    okato: str | None = None
    oktmo: str | None = None
    kladr_code: str | None = None
    cadastral_number: str | None = None
    apart_building: str | None = None
    remove_cadastr: str | None = None
    oktmo_budget: str | None = None
    is_adm_capital: str | None = None
    is_mun_capital: str | None = None


class FiasSuccessorRef(BaseModel):
    """Информация о правопреемнике адресного объекта."""

    object_id: int
    object_guid: UUID


class FiasHistName(BaseModel):
    """Историческое название адресного объекта."""

    name: str
    short_type: str


class FiasHierarchyItem(BaseModel):
    """Элемент иерархии адреса."""

    object_id: int
    object_level_id: int
    object_guid: UUID
    full_name: str
    full_name_short: str | None = None
    kladr_code: str | None = None
    object_type: str | None = None
    hierarchy_place: int | None = None
    hist_names: list[FiasHistName] | None = None


class FiasFederalDistrict(BaseModel):
    """Данные по федеральному округу."""

    id: int
    full_name: str
    short_name: str
    center_id: int


class FiasSearchAddressItemResponse(BaseModel):
    """Корневой ответ SearchAddressItem."""

    object_id: int
    object_level_id: int
    operation_type_id: int
    object_guid: UUID
    address_type: int
    full_name: str
    region_code: int
    is_active: bool
    path: str
    address_details: FiasAddressDetails | None = None
    successor_ref: FiasSuccessorRef | None = None
    hierarchy: list[FiasHierarchyItem] | None = None
    federal_district: FiasFederalDistrict | None = None
    hierarchy_place: int | None = None
