"""XHR-клиент kad.arbitr.ru."""

from __future__ import annotations

import asyncio

import httpx

from sources.kad_arbitr.exceptions import (
    KadArbitrBlockedError,
    KadArbitrUnexpectedResponseError,
)
from sources.kad_arbitr.models import (
    KadArbitrSearchPayload,
    KadArbitrSearchResponse,
)
from sources.kad_arbitr.ports import KadArbitrClientPort

_DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 Safari/537.36'
)


class XhrKadArbitrClient(KadArbitrClientPort):
    """XHR-клиент для поиска дел kad.arbitr.ru."""

    def __init__(
        self,
        *,
        base_url: str = 'https://kad.arbitr.ru',
        timeout_seconds: int = 30,
        ssl_verify: bool = True,
        user_agent: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Сконфигурировать XHR-клиент."""

        self._base_url = base_url.rstrip('/')
        self._timeout_seconds = timeout_seconds
        self._ssl_verify = ssl_verify
        self._user_agent = user_agent or _DEFAULT_USER_AGENT
        self._warmed_up = False
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            verify=self._ssl_verify,
            timeout=self._timeout_seconds,
        )

    async def __aenter__(self) -> XhrKadArbitrClient:
        """Открыть клиентский контекст."""

        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        """Закрыть клиентский контекст."""

        await self.close()

    async def close(self) -> None:
        """Закрыть HTTP клиент."""

        if self._owns_client:
            await self._client.aclose()

    async def search_instances(
        self,
        *,
        payload: KadArbitrSearchPayload,
    ) -> KadArbitrSearchResponse:
        """Асинхронно выполнить поиск дел."""

        await self._warmup()
        request_headers = self._xhr_headers()
        body = payload.to_xhr_dict()
        backoffs = (0.3, 0.8, 1.6)
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                response = await self._client.post(
                    '/Kad/SearchInstances',
                    headers=request_headers,
                    json=body,
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

            text_body = response.text
            if text_body.lstrip().startswith('<'):
                snippet = text_body.lstrip()[:200].replace('\n', ' ')
                raise KadArbitrUnexpectedResponseError(
                    'kad.arbitr returned html: '
                    f'status={response.status_code} '
                    f'snippet={snippet!r}'
                )

            try:
                data = response.json()
            except ValueError as exc:
                snippet = text_body[:200].replace('\n', ' ')
                raise KadArbitrUnexpectedResponseError(
                    f'invalid json: status={response.status_code} '
                    f'snippet={snippet!r}'
                ) from exc

            if not isinstance(data, dict):
                raise KadArbitrUnexpectedResponseError('json is not object')

            try:
                return KadArbitrSearchResponse.from_dict(data)
            except ValueError as exc:
                raise KadArbitrUnexpectedResponseError(
                    f'invalid response: {exc}'
                ) from exc

        raise KadArbitrUnexpectedResponseError(
            f'unexpected error: {last_error}'
        )

    async def _warmup(self) -> None:
        """Выполнить прогрев сессии при первом запросе."""

        if self._warmed_up:
            return

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'User-Agent': self._user_agent,
        }
        await self._client.get('/', headers=headers)
        self._warmed_up = True

    def _xhr_headers(self) -> dict[str, str]:
        """Сформировать XHR заголовки."""

        return {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/json; charset=UTF-8',
            'Origin': 'https://kad.arbitr.ru',
            'Referer': 'https://kad.arbitr.ru/',
            'X-Requested-With': 'XMLHttpRequest',
            'x-date-format': 'iso',
            'User-Agent': self._user_agent,
        }

    @property
    def base_url(self) -> str:
        """Вернуть базовый URL клиента."""

        return self._base_url

    @property
    def timeout_seconds(self) -> int:
        """Вернуть таймаут запросов."""

        return self._timeout_seconds

    @property
    def ssl_verify(self) -> bool:
        """Вернуть флаг проверки SSL."""

        return self._ssl_verify

    @property
    def user_agent(self) -> str:
        """Вернуть user agent клиента."""

        return self._user_agent
