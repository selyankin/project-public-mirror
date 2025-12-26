"""Проверки извлечения window.__preloadedState__."""

import pytest

from sources.domain.exceptions import ListingParseError
from sources.infrastructure.avito import extract_preloaded_state_json


def test_extract_preloaded_state_returns_json() -> None:
    """Функция возвращает корректную JSON-строку."""

    html = """
    <script>
        window.__preloadedState__ = {"foo": "bar", "nested": {"a": 1}};
    </script>
    """
    json_str = extract_preloaded_state_json(html)
    assert json_str == '{"foo": "bar", "nested": {"a": 1}}'


def test_extract_preloaded_state_not_found() -> None:
    """Если блока нет, поднимается ListingParseError."""

    html = '<html><body>No state here</body></html>'
    with pytest.raises(ListingParseError):
        extract_preloaded_state_json(html)
