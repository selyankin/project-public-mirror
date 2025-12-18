import pytest

from checks.domain.value_objects.address import (
    AddressValidationError,
    normalize_address,
    normalize_address_raw,
)


def test_empty_string_raises_validation_error():
    with pytest.raises(AddressValidationError):
        normalize_address_raw('   ')


def test_whitespace_is_collapsed():
    raw = normalize_address_raw("  123 \n Main\tStreet  ")
    normalized = normalize_address(raw)
    assert normalized.normalized == '123 main street'


def test_commas_are_normalized():
    raw = normalize_address_raw('Foo ,  Bar ,Baz')
    normalized = normalize_address(raw)
    assert normalized.normalized == 'foo, bar, baz'


def test_tokens_are_tuple_and_non_empty():
    raw = normalize_address_raw('1 Infinite Loop')
    normalized = normalize_address(raw)
    assert isinstance(normalized.tokens, tuple)
    assert normalized.tokens == ('1', 'infinite', 'loop')


def test_normalized_is_lowercase():
    raw = normalize_address_raw('FlAfFy Avenue')
    normalized = normalize_address(raw)
    assert normalized.normalized == 'flaffy avenue'


def test_address_raw_equality_and_hash():
    first = normalize_address_raw('  Foo Street 42 ')
    second = normalize_address_raw('Foo Street 42')
    assert first == second
    assert hash(first) == hash(second)


def test_address_normalized_equality_and_hash():
    first = normalize_address(normalize_address_raw('Main Street, 1'))
    second = normalize_address(normalize_address_raw('MAIN STREET , 1'))
    assert first == second
    assert hash(first) == hash(second)
