import pytest

from src.checks.domain.value_objects.url import UrlRaw


def test_valid_https_url():
    url = UrlRaw("https://example.com")
    assert url.value == "https://example.com"


def test_valid_http_url():
    url = UrlRaw("http://example.com/path")
    assert url.value == "http://example.com/path"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "ftp://example.com",
        "example.com",
    ],
)
def test_invalid_url_values(value):
    with pytest.raises(ValueError):
        UrlRaw(value)
