"""HTTP-загрузчик PDF kad.arbitr.ru."""

from __future__ import annotations

import asyncio

import httpx

from sources.kad_arbitr.exceptions import (
    KadArbitrBlockedError,
    KadArbitrUnexpectedResponseError,
)
from sources.kad_arbitr.pdf.ports import PdfFetcherPort
from sources.kad_arbitr.throttling import RateLimiter


class HttpPdfFetcher(PdfFetcherPort):
    """Загружает PDF по HTTP."""

    def __init__(
        self,
        *,
        timeout_seconds: int = 30,
        ssl_verify: bool = True,
        headers: dict[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Сконфигурировать HTTP загрузчик."""

        self._timeout_seconds = timeout_seconds
        self._ssl_verify = ssl_verify
        self._headers = headers or {}
        self._owns_client = client is None
        self._rate_limiter = rate_limiter
        self._client = client or httpx.AsyncClient(
            timeout=self._timeout_seconds,
            verify=self._ssl_verify,
        )

    async def fetch(self, *, url: str) -> bytes:
        """Асинхронно загрузить PDF по ссылке."""

        backoffs = (0.3, 0.8, 1.6)
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                await self._wait_rate_limit()
                response = await self._client.get(
                    url,
                    headers=self._headers,
                )
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(backoffs[attempt])
                    continue
                raise KadArbitrUnexpectedResponseError(
                    f'network error: {exc}'
                ) from exc

            if response.status_code == 403:
                raise KadArbitrBlockedError('kad.arbitr blocked request')

            if response.status_code >= 500:
                last_error = KadArbitrUnexpectedResponseError(
                    f'status={response.status_code}'
                )
                if attempt < 2:
                    await asyncio.sleep(backoffs[attempt])
                    continue
                raise last_error

            body = response.content or b''
            if body.lstrip().startswith(b'<'):
                snippet = body[:200].decode('utf-8', errors='ignore')
                snippet = snippet.replace('\n', ' ')
                raise KadArbitrUnexpectedResponseError(
                    f'status={response.status_code} ' f'snippet={snippet!r}'
                )

            return body

        raise KadArbitrUnexpectedResponseError(
            f'unexpected error: {last_error}'
        )

    async def close(self) -> None:
        """Закрыть HTTP клиент."""

        if self._owns_client:
            await self._client.aclose()

    async def _wait_rate_limit(self) -> None:
        """Ограничить частоту запросов."""

        if self._rate_limiter is None:
            return

        await self._rate_limiter.wait()
