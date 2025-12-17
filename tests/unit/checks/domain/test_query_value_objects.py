import pytest
from checks.domain.constants.enums.domain import QueryType
from checks.domain.value_objects.query import CheckQuery, QueryInputError


def test_valid_address_query():
    query = CheckQuery({'type': 'address', 'query': ' ул мира 7 '})
    assert query.type is QueryType.address
    assert query.query == 'ул мира 7'


def test_valid_url_query():
    query = CheckQuery({'type': QueryType.url, 'query': 'https://example.com'})
    assert query.type is QueryType.url
    assert query.query == 'https://example.com'


@pytest.mark.parametrize('payload', ['', '   '])
def test_empty_query_raises(payload):
    with pytest.raises(QueryInputError):
        CheckQuery({'type': 'address', 'query': payload})


def test_unknown_type_raises():
    with pytest.raises(QueryInputError):
        CheckQuery({'type': 'unknown', 'query': 'value'})
