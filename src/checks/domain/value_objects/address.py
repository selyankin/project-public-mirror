"""Value objects for address data in the Check domain."""

from typing import Literal

from checks.domain.constants.address import COMMA_RE, WHITESPACE_RE
from checks.domain.exceptions.address import AddressValidationError

AddressConfidence = Literal['exact', 'high', 'medium', 'low', 'unknown']
AddressSource = Literal['stub', 'fias']


class AddressRaw:
    """Represents unprocessed user-provided address text."""

    __slots__ = ('value',)

    def __init__(self, value: str):
        """Constructor"""

        if not isinstance(value, str):
            raise TypeError('Address must be a string.')

        trimmed = value.strip()
        if not trimmed:
            raise AddressValidationError('Address cannot be empty.')

        if len(trimmed) > 500:
            raise AddressValidationError('Address is too long.')

        self.value = trimmed

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'AddressRaw(value={self.value!r})'

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AddressRaw):
            return NotImplemented

        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


class AddressNormalized:
    """Represents normalized address data."""

    __slots__ = (
        'raw',
        'normalized',
        'tokens',
        'confidence',
        'source',
    )

    def __init__(
        self,
        raw: AddressRaw,
        normalized: str,
        tokens: tuple[str, ...],
        *,
        confidence: AddressConfidence = 'unknown',
        source: AddressSource = 'stub',
    ):
        """Constructor"""

        if not normalized:
            raise AddressValidationError('Normalized address cannot be empty.')

        if not tokens:
            raise AddressValidationError('Normalized address tokens missing.')

        self.raw = raw
        self.normalized = normalized
        self.tokens = tokens
        self.confidence = confidence
        self.source = source

    def __str__(self) -> str:
        return self.normalized

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AddressNormalized):
            return NotImplemented

        return self.normalized == other.normalized

    def __hash__(self) -> int:
        return hash(self.normalized)


def normalize_address_raw(raw: str) -> AddressRaw:
    """Validate and wrap a raw address string."""

    return AddressRaw(raw)


def evaluate_address_confidence(
    addr: AddressNormalized,
) -> AddressConfidence:
    """Грубая оценка точности нормализации адреса."""

    lower = addr.normalized.lower()

    def _contains_any(keywords: tuple[str, ...]) -> bool:
        return any(keyword in lower for keyword in keywords)

    has_street = _contains_any(
        (
            'ул.',
            'ул ',
            'улица',
            'пр-т',
            'проспект',
            'просп.',
            'пер.',
            'переулок',
            'бульвар',
            'бул.',
            'шоссе',
        ),
    )
    has_city = _contains_any(
        (
            'г.',
            'г ',
            'город',
            'пос.',
            'пос ',
            'поселок',
            'посёлок',
            'пгт',
            'дер.',
            'деревня',
            'село',
        ),
    )
    has_digits = any(ch.isdigit() for ch in lower)
    has_house_marker = _contains_any(('д.', 'д ', 'дом', 'дом ', 'house'))
    has_house = has_digits and has_house_marker

    if has_house and has_street and has_city:
        return 'exact'
    if has_house and has_street:
        return 'high'
    if has_street:
        return 'medium'
    if has_city:
        return 'low'
    return 'unknown'


def normalize_address(address: AddressRaw) -> AddressNormalized:
    """Return a normalized representation of the given address."""

    text = address.value
    collapsed = WHITESPACE_RE.sub(' ', text)
    comma_adjusted = COMMA_RE.sub(', ', collapsed)
    normalized = comma_adjusted.lower()
    tokens = tuple(normalized.split(' '))

    if not tokens or any(not token for token in tokens):
        raise AddressValidationError('Normalized tokens invalid.')

    normalized_addr = AddressNormalized(address, normalized, tokens)
    normalized_addr.confidence = evaluate_address_confidence(normalized_addr)
    normalized_addr.source = 'stub'
    return normalized_addr
