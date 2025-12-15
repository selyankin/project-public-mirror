from src.checks.application.helpers.url_extraction import (
    extract_address_from_url,
    is_supported_url,
)
from src.checks.domain.value_objects.url import UrlRaw


def test_extracts_address_param():
    url = UrlRaw('https://example.com/?address=ул+мира+7')
    assert extract_address_from_url(url) == 'ул мира 7'
    assert is_supported_url(url) is True


def test_extracts_query_param():
    url = UrlRaw('https://example.com/?q=ул%20мира%207')
    assert extract_address_from_url(url) == 'ул мира 7'


def test_returns_none_without_params():
    url = UrlRaw('https://example.com/')
    assert extract_address_from_url(url) is None
    assert is_supported_url(url) is False


def test_returns_none_for_empty_value():
    url = UrlRaw('https://example.com/?address=')
    assert extract_address_from_url(url) is None
