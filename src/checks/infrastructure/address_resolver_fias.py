"""FIAS-backed address resolver adapter."""

import logging

from checks.application.ports.checks import AddressResolverPort
from checks.domain.value_objects.address import (
    AddressNormalized,
    AddressRaw,
    normalize_address,
)
from checks.infrastructure.fias.client import FiasClient
from checks.infrastructure.fias.errors import FiasError

logger = logging.getLogger(__name__)


class FiasAddressResolver(AddressResolverPort):
    """Address resolver that will use the FIAS API."""

    __slots__ = ('_client',)

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout_seconds: float,
    ) -> None:
        """Store FIAS connection parameters."""

        self._client = FiasClient(
            base_url=base_url,
            token=token,
            timeout_seconds=timeout_seconds,
        )

    def normalize(self, raw: AddressRaw) -> AddressNormalized:
        """Normalize address using FIAS (stubbed for now)."""

        normalized = normalize_address(raw)
        try:
            self._client.search_address_item(raw.value)
        except FiasError as exc:
            logger.warning(
                'FIAS lookup failed, fallback to domain normalization: %s',
                exc,
            )
            normalized.source = 'stub'
        else:
            normalized.source = 'fias'

        return normalized
