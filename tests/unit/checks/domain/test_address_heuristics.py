from src.checks.domain.helpers.address_heuristics import is_address_like


def test_address_like_with_street_and_number():
    assert is_address_like('ул мира 7') is True


def test_not_address_without_digits_and_keywords():
    assert is_address_like('москва') is False


def test_not_address_plain_text():
    assert is_address_like('привет как дела') is False


def test_keyword_only_street():
    assert is_address_like('улица ленина') is True


def test_too_many_special_symbols():
    assert is_address_like('@@@###$$$%%%^^^&&&***') is False
