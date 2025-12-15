"""Stub adapter for address normalization."""

from __future__ import annotations

from src.checks.domain.value_objects.address import (
    AddressNormalized,
    AddressRaw,
    normalize_address,
)


class AddressResolverStub:
    """In-memory stub that normalizes addresses using domain logic."""

    __slots__ = ("_data",)

    def __init__(self, data: dict):
        """Create resolver stub instance."""
        self._data = dict(data)

    @staticmethod
    def normalize(raw: AddressRaw) -> AddressNormalized:
        """Normalize raw address using domain normalization rules."""
        return normalize_address(raw)
