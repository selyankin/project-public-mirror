"""Value objects for address data in the Check domain."""

from checks.domain.constants.address import COMMA_RE, WHITESPACE_RE
from checks.domain.exceptions.address import AddressValidationError


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
    )

    def __init__(
        self,
        raw: AddressRaw,
        normalized: str,
        tokens: tuple[str, ...],
    ):
        """Constructor"""

        if not normalized:
            raise AddressValidationError('Normalized address cannot be empty.')

        if not tokens:
            raise AddressValidationError('Normalized address tokens missing.')

        self.raw = raw
        self.normalized = normalized
        self.tokens = tokens

    def __str__(self) -> str:
        return self.normalized

    def __repr__(self) -> str:
        return (
            'AddressNormalized('
            f'normalized={self.normalized!r}, tokens={self.tokens!r})'
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AddressNormalized):
            return NotImplemented

        return self.normalized == other.normalized

    def __hash__(self) -> int:
        return hash(self.normalized)


def normalize_address_raw(raw: str) -> AddressRaw:
    """Validate and wrap a raw address string."""

    return AddressRaw(raw)


def normalize_address(address: AddressRaw) -> AddressNormalized:
    """Return a normalized representation of the given address."""

    text = address.value
    collapsed = WHITESPACE_RE.sub(' ', text)
    comma_adjusted = COMMA_RE.sub(', ', collapsed)
    normalized = comma_adjusted.lower()
    tokens = tuple(normalized.split(' '))

    if not tokens or any(not token for token in tokens):
        raise AddressValidationError('Normalized tokens invalid.')

    return AddressNormalized(address, normalized, tokens)
