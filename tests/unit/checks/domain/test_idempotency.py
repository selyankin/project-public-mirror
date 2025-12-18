"""Тесты построения идемпотентных ключей."""

from checks.domain.helpers.idempotency import build_check_cache_key


def test_same_inputs_produce_same_key() -> None:
    """Одинаковые параметры дают одинаковый ключ."""

    first = build_check_cache_key(
        input_kind='address',
        input_value='ул мира 7',
        fias_mode='stub',
        version='v1',
    )
    second = build_check_cache_key(
        input_kind='address',
        input_value='ул мира 7',
        fias_mode='stub',
        version='v1',
    )
    assert first == second


def test_different_mode_produces_different_key() -> None:
    """Разные режимы FIAS дают разные ключи."""

    stub_key = build_check_cache_key(
        input_kind='address',
        input_value='ул мира 7',
        fias_mode='stub',
    )
    api_key = build_check_cache_key(
        input_kind='address',
        input_value='ул мира 7',
        fias_mode='api',
    )
    assert stub_key != api_key


def test_different_kinds_use_different_keys() -> None:
    """Разные типы ввода дают разные ключи."""

    address_key = build_check_cache_key(
        input_kind='address',
        input_value='ул мира 7',
        fias_mode='stub',
    )
    url_key = build_check_cache_key(
        input_kind='url',
        input_value='https://example.com/?address=ул+мира+7',
        fias_mode='stub',
    )
    assert address_key != url_key
