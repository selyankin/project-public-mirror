"""HTTP-клиент для обращения к ФИАС."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Final

import httpx
from checks.infrastructure.fias.dto import (
    FiasErrorResponse,
    FiasSearchAddressItemResponse,
)
from checks.infrastructure.fias.errors import (
    FiasServerError,
    FiasTimeoutError,
    FiasTransportError,
    FiasUnexpectedStatus,
)

logger = logging.getLogger(__name__)


class FiasClient:
    """Синхронный клиент ФИАС."""

    _SEARCH_PATH: Final[str] = '/api/spas/v2.0/SearchAddressItem'

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout_seconds: float,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        """Сохранить настройки доступа к ФИАС."""

        self._base_url = base_url.rstrip('/')
        self._headers = {'Authorization': f'Bearer {token}'}
        self._timeout = httpx.Timeout(timeout_seconds)
        self._client = client or httpx.Client()

    def search_address_item(
        self,
        search_string: str,
        *,
        address_type: int = 1,
    ) -> FiasSearchAddressItemResponse | None:
        """Выполнить поиск адреса в ФИАС."""

        params = {
            'search_string': search_string,
            'address_type': address_type,
        }
        url = f'{self._base_url}{self._SEARCH_PATH}'
        start = perf_counter()

        try:
            response = self._client.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self._timeout,
            )

        except httpx.TimeoutException as exc:
            raise FiasTimeoutError('FIAS request timed out.') from exc
        except httpx.RequestError as exc:
            raise FiasTransportError('FIAS transport error.') from exc

        finally:
            duration = perf_counter() - start
            logger.debug(
                'FIAS GET %s search=%s address_type=%s took=%.3fs',
                self._SEARCH_PATH,
                search_string[:120],
                address_type,
                duration,
            )

        if response.status_code == 200:
            return FiasSearchAddressItemResponse.model_validate(response.json())

        if response.status_code == 500:
            error_data = self._safe_json(response)
            error = FiasErrorResponse.model_validate(error_data)
            raise FiasServerError(description=error.description)

        raise FiasUnexpectedStatus(response.status_code, response.text[:200])

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, object]:
        """Попробовать распарсить JSON, возвращая пустой объект при сбое."""

        try:
            parsed = response.json()

        except ValueError:
            return {
                'description': response.text[:200],
            }

        if isinstance(parsed, dict):
            return parsed

        return {
            'description': str(parsed),
        }
