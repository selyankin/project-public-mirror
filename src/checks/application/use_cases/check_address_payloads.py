"""Построители payload для проверки адреса."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any

from checks.application.ports.fias_client import NormalizedAddress
from shared.domain.entities import HouseKey
from sources.domain.entities import ListingNormalized
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.rosreestr.models import RosreestrHouseNormalized


def build_house_payload(
    *,
    normalized: NormalizedAddress,
    listing: ListingNormalized | None,
) -> dict[str, Any] | None:
    """Собрать публичный payload идентификаторов дома."""

    del listing
    try:
        house_key = HouseKey.build(
            fias_houseguid=normalized.fias_houseguid,
            gar_house_id=normalized.gar_house_id,
            gar_object_id=normalized.gar_object_id,
        )
        house_key_value = house_key.value
    except ValueError:
        house_key_value = None

    payload: dict[str, Any] = {}
    if house_key_value:
        payload['house_key'] = house_key_value
    if normalized.fias_houseguid:
        payload['fias_houseguid'] = normalized.fias_houseguid
    if normalized.fias_aoguid:
        payload['fias_aoguid'] = normalized.fias_aoguid
    if normalized.gar_house_id:
        payload['gar_house_id'] = normalized.gar_house_id
    if normalized.gar_object_id:
        payload['gar_object_id'] = normalized.gar_object_id
    if normalized.postal_code:
        payload['postal_code'] = normalized.postal_code
    if normalized.oktmo:
        payload['oktmo'] = normalized.oktmo
    if normalized.okato:
        payload['okato'] = normalized.okato
    if normalized.region_code:
        payload['region_code'] = normalized.region_code
    if normalized.cadastral_number:
        payload['cadastral_number'] = normalized.cadastral_number
    if normalized.status:
        payload['status'] = normalized.status
    if normalized.is_active is not None:
        payload['is_active'] = normalized.is_active
    if normalized.updated_at is not None:
        payload['updated_at'] = normalized.updated_at.isoformat()

    return payload or None


def rosreestr_house_to_payload(
    house: RosreestrHouseNormalized,
) -> dict[str, Any]:
    """Преобразовать доменную модель Росреестра к dict."""

    payload = asdict(house)
    for key, value in payload.items():
        if isinstance(value, date):
            payload[key] = value.isoformat()

    return payload


def gis_gkh_house_to_payload(house: GisGkhHouseNormalized) -> dict[str, Any]:
    """Преобразовать доменную модель GIS ЖКХ к dict."""

    return asdict(house)


def build_sources_payload(
    *,
    rosreestr_payload: dict[str, Any] | None,
    gis_gkh_payload: dict[str, Any] | None,
    kad_arbitr_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Собрать payload источников."""

    payload: dict[str, Any] = {}
    if rosreestr_payload:
        payload['rosreestr'] = rosreestr_payload
    if gis_gkh_payload:
        payload['gis_gkh'] = gis_gkh_payload
    if kad_arbitr_payload:
        payload['kad_arbitr'] = kad_arbitr_payload

    return payload or None
