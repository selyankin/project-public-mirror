"""HTTP-клиент для обращения к ФИАС по сети."""

from __future__ import annotations

import asyncio
import logging
from random import uniform
from time import perf_counter
from typing import Any

import httpx

from checks.application.ports.fias_client import NormalizedAddress

logger = logging.getLogger(__name__)


class ApiFiasClient:
    """Async-клиент ФИАС, совместимый с приложением."""

    __slots__ = (
        '_http_client',
        '_endpoint',
        '_base_url',
        '_headers',
        '_timeout',
        '_retries',
        '_backoff',
        '_semaphore',
    )

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        http_client: httpx.AsyncClient,
        timeout_seconds: float,
        retries: int,
        retry_backoff_seconds: float,
        concurrency_limit: int,
        endpoint: str,
    ) -> None:
        """Сохранить параметры доступа к ФИАС."""

        self._http_client = http_client
        self._endpoint = (
            endpoint if endpoint.startswith('/') else f'/{endpoint}'
        )
        self._base_url = base_url.rstrip('/')
        self._headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
        }
        self._timeout = httpx.Timeout(timeout_seconds)
        self._retries = max(0, retries)
        self._backoff = max(0.0, retry_backoff_seconds)
        self._semaphore = asyncio.Semaphore(max(1, concurrency_limit))

    async def normalize_address(self, query: str) -> NormalizedAddress | None:
        """Попробовать нормализовать адрес через ФИАС."""

        params = {
            'search_string': query,
            'address_type': 1,
        }
        query_len = len(query)
        async with self._semaphore:
            for attempt in range(self._retries + 1):
                if attempt:
                    delay = self._backoff * (2**attempt)
                    jitter = uniform(0, min(0.1, delay * 0.1)) if delay else 0.0
                    await asyncio.sleep(delay + jitter)

                logger.debug(
                    'fias_request_start endpoint=%s attempt=%s query_len=%s',
                    self._endpoint,
                    attempt,
                    query_len,
                )
                start = perf_counter()
                response: httpx.Response | None = None
                try:
                    response = await self._http_client.get(
                        self._build_url(),
                        params=params,
                        headers=self._headers,
                        timeout=self._timeout,
                    )
                except httpx.RequestError as exc:
                    logger.warning(
                        'fias_request_error endpoint=%s attempt=%s error=%s',
                        self._endpoint,
                        attempt,
                        exc.__class__.__name__,
                    )
                    if attempt == self._retries:
                        logger.error(
                            'fias_request_failed query_len=%s reason=request',
                            query_len,
                        )
                        return None
                    continue
                finally:
                    duration = perf_counter() - start
                    logger.debug(
                        'fias_response_received status=%s duration=%.3fs',
                        response.status_code if response else 'n/a',
                        duration,
                    )

                if response is None:
                    continue

                status = response.status_code
                if status == 200:
                    payload = self._safe_json(response)
                    parsed = self._parse_normalized(payload, query)
                    if parsed is None:
                        logger.warning(
                            'fias_payload_invalid query_len=%s keys=%s',
                            query_len,
                            self._payload_keys(payload),
                        )
                        return None

                    logger.info(
                        'fias_request_success query_len=%s keys=%s',
                        query_len,
                        self._payload_keys(payload),
                    )
                    return parsed

                if status in (401, 403, 404):
                    logger.warning(
                        'fias_request_denied status=%s '
                        'endpoint=%s query_len=%s',
                        status,
                        self._endpoint,
                        query_len,
                    )
                    return None

                if self._should_retry_status(status):
                    logger.warning(
                        'fias_retryable_status status=%s attempt=%s',
                        status,
                        attempt,
                    )
                    if attempt == self._retries:
                        logger.error(
                            'fias_retries_exhausted status=%s query_len=%s',
                            status,
                            query_len,
                        )
                        return None
                    continue

                logger.warning(
                    'fias_unexpected_status status=%s body=%s',
                    status,
                    response.text[:200],
                )
                return None

        logger.info(
            'fias_request_no_result query_len=%s attempts=%s',
            query_len,
            self._retries + 1,
        )
        return None

    def search_address_item(
        self,
        search_string: str,
        *,
        address_type: int = 1,
    ) -> NormalizedAddress | None:
        """Синхронный шим для устаревших адаптеров."""

        coro = self.normalize_address(search_string)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    @staticmethod
    def _parse_normalized(payload: Any, query: str) -> NormalizedAddress | None:
        """Преобразовать ответ API к доменной модели."""

        if not isinstance(payload, dict):
            logger.warning(
                'fias_payload_not_dict type=%s query_len=%s',
                type(payload).__name__,
                len(query),
            )
            return None

        normalized = payload.get('full_name') or payload.get('path')
        if not isinstance(normalized, str):
            logger.warning(
                'fias_payload_missing_full_name keys=%s',
                list(payload.keys())[:5],
            )
            return None

        fias_guid = payload.get('object_guid')
        fias_id = str(fias_guid) if fias_guid else None
        confidence_value = payload.get('search_precision')
        if confidence_value is not None:
            try:
                confidence = float(confidence_value)
            except (TypeError, ValueError):
                confidence = None

        else:
            confidence = None

        return NormalizedAddress(
            source_query=query,
            normalized=normalized,
            fias_id=fias_id,
            confidence=confidence,
            raw=payload,
        )

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        """Безопасно распарсить JSON-ответ."""

        try:
            return response.json()
        except ValueError:
            logger.warning(
                'Failed to decode FIAS JSON body=%s',
                response.text[:200],
            )
            return {}

    def _build_url(self) -> str:
        """Построить полный URL для запроса."""

        return f'{self._base_url}{self._endpoint}'

    @staticmethod
    def _payload_keys(payload: Any) -> list[str]:
        """Вернуть список ключей верхнего уровня."""

        if isinstance(payload, dict):
            return list(payload.keys())[:5]
        return []

    @staticmethod
    def _should_retry_status(status: int) -> bool:
        """Определить, стоит ли повторять запрос по статусу."""

        return status in {429, 500, 502, 503, 504}
