"""Тесты эвристики confidence для адресов."""

from checks.domain.value_objects.address import (
    AddressNormalized,
    evaluate_address_confidence,
    normalize_address,
    normalize_address_raw,
)


def _normalized(text: str) -> AddressNormalized:
    return normalize_address(normalize_address_raw(text))


def test_confidence_exact_for_full_address() -> None:
    """Полный адрес с городом, улицей и домом -> exact."""

    addr = _normalized('г. Москва, ул. Тверская, д. 1')
    assert evaluate_address_confidence(addr) == 'exact'


def test_confidence_medium_for_street_only() -> None:
    """Улица без дома -> medium."""

    addr = _normalized('ул. Тверская')
    assert evaluate_address_confidence(addr) == 'medium'


def test_confidence_low_for_city_only() -> None:
    """Город без улицы -> low."""

    addr = _normalized('г. Москва')
    assert evaluate_address_confidence(addr) == 'low'


def test_confidence_unknown_for_noise() -> None:
    """Текст без адресных признаков -> unknown."""

    addr = _normalized('привет как дела')
    assert evaluate_address_confidence(addr) == 'unknown'
