"""Factory for building address resolver instances."""

from __future__ import annotations

from checks.adapters.address_resolver_stub import AddressResolverStub
from checks.application.ports.checks import AddressResolverPort
from checks.infrastructure.address_resolver_fias import FiasAddressResolver
from shared.kernel.settings import Settings


def build_address_resolver(settings: Settings) -> AddressResolverPort:
    """Return address resolver implementation based on settings."""

    if settings.fias_enabled:
        return FiasAddressResolver(
            base_url=settings.FIAS_BASE_URL,
            token=settings.FIAS_TOKEN,
            timeout_seconds=settings.FIAS_TIMEOUT_SECONDS,
        )

    return AddressResolverStub({})
