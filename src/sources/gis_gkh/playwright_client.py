"""Клиент GIS ЖКХ на основе Playwright."""

from __future__ import annotations

import json
import uuid
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from sources.gis_gkh.consts import (
    BASE_LANDING,
    BASE_URL,
    HOUSES_PAGE,
    HOUSES_PUBLIC_ENDPOINT,
    REGION_GUID_MAP,
)
from sources.gis_gkh.exceptions import GisGkhBadResponseError, GisGkhError
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.gis_gkh.ports import GisGkhClientPort

_DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/143.0.0.0 Safari/537.36'
)


class PlaywrightGisGkhClient(GisGkhClientPort):
    """Playwright-клиент для поиска домов в GIS ЖКХ."""

    def __init__(
        self,
        *,
        timeout_seconds: int = 60,
        headless: bool = True,
        ssl_verify: bool = True,
        user_agent: str | None = None,
    ) -> None:
        """Сконфигурировать клиент."""

        self._timeout_seconds = timeout_seconds
        self._headless = headless
        self._ssl_verify = ssl_verify
        self._user_agent = user_agent or _DEFAULT_USER_AGENT

        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._session_guid = str(uuid.uuid4())

    async def __aenter__(self) -> PlaywrightGisGkhClient:
        """Открыть ресурсы Playwright."""

        await self._init()
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        """Закрыть ресурсы Playwright."""

        await self.close()

    async def close(self) -> None:
        """Закрыть браузерные ресурсы."""

        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
        finally:
            self._page = None
            self._context = None
            self._browser = None
            if self._pw:
                await self._pw.stop()
                self._pw = None

    async def search_by_cadnum(
        self,
        *,
        cadnum: str,
        region_code: str,
    ) -> list[GisGkhHouseNormalized]:
        """Найти дома по кадастровому номеру."""

        await self._init()
        region_guid = self._resolve_region_guid(region_code)

        params = {
            'pageIndex': 1,
            'elementsPerPage': 10,
        }
        payload = {
            'regionCode': region_guid,
            'cadastreNumber': cadnum,
            'useReadOnlyDataSource': True,
            'fiasHouseCodeList': None,
            'estStatus': None,
        }

        data = await self._api_post_json(
            HOUSES_PUBLIC_ENDPOINT,
            params=params,
            payload=payload,
        )
        items = data.get('items')
        if not isinstance(items, list):
            return []

        result: list[GisGkhHouseNormalized] = []
        for item in items:
            if isinstance(item, dict):
                result.append(GisGkhHouseNormalized.from_dict(item))

        return result

    async def _init(self) -> None:
        """Инициализировать браузерный контекст."""

        if self._page is not None:
            return

        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            user_agent=self._user_agent,
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=not self._ssl_verify,
        )
        self._page = await self._context.new_page()

        await self._page.goto(
            BASE_LANDING,
            wait_until='domcontentloaded',
            timeout=self._timeout_ms,
        )
        await self._page.wait_for_timeout(1200)
        await self._page.goto(
            HOUSES_PAGE,
            wait_until='domcontentloaded',
            timeout=self._timeout_ms,
        )
        await self._page.wait_for_timeout(1200)

    async def _api_post_json(
        self,
        path: str,
        *,
        params: dict[str, object],
        payload: dict[str, object],
    ) -> dict[str, Any]:
        """Выполнить POST запрос и вернуть JSON."""

        if not self._context:
            raise GisGkhError('Browser context is not initialized.')

        url = f'{BASE_URL}{path}'
        headers = {
            'Accept': 'application/json; charset=utf-8',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': BASE_URL,
            'Referer': BASE_LANDING,
            'X-Requested-With': 'XMLHttpRequest',
            'State-Guid': '/houses',
            'Session-Guid': self._session_guid,
            'Request-Guid': str(uuid.uuid4()),
        }

        last_snippet = None
        for _ in range(3):
            response = await self._context.request.post(
                url,
                params=params,
                headers=headers,
                data=json.dumps(payload),
                timeout=self._timeout_ms,
            )
            body = await response.text()
            if self._is_challenge_html(body):
                last_snippet = body.lstrip()[:200].replace('\n', ' ')
                await self._solve_challenge_by_navigation(BASE_LANDING)
                continue

            if body.lstrip().startswith('<'):
                snippet = body.lstrip()[:200].replace('\n', ' ')
                raise GisGkhBadResponseError(
                    'GIS ЖКХ вернул HTML вместо JSON: '
                    f'status={response.status} snippet={snippet!r}',
                )

            try:
                data = json.loads(body)
            except json.JSONDecodeError as exc:
                snippet = body[:200].replace('\n', ' ')
                raise GisGkhBadResponseError(
                    'Не удалось распарсить JSON: '
                    f'status={response.status} snippet={snippet!r}',
                ) from exc

            if isinstance(data, dict):
                return data

            raise GisGkhBadResponseError('Ответ не является JSON-объектом.')

        raise GisGkhBadResponseError(
            'Не удалось пройти защиту GIS ЖКХ. '
            f'last_snippet={last_snippet!r}',
        )

    async def _solve_challenge_by_navigation(self, url: str) -> None:
        """Пройти антибот через навигацию на страницу."""

        if self._context is None:
            raise GisGkhError('Browser context is not initialized.')

        page = await self._context.new_page()
        try:
            try:
                await page.goto(url, wait_until='commit', timeout=12_000)
            except PlaywrightTimeoutError:
                pass
            await page.wait_for_timeout(2500)
        finally:
            await page.close()

    def _resolve_region_guid(self, region_code: str) -> str:
        """Получить guid региона по коду."""

        guid = REGION_GUID_MAP.get(region_code)
        if not guid:
            raise GisGkhBadResponseError(
                f'Не найден guid региона для кода {region_code}.',
            )

        return guid

    @property
    def _timeout_ms(self) -> int:
        """Вернуть таймаут в миллисекундах."""

        return int(self._timeout_seconds * 1000)

    @staticmethod
    def _is_challenge_html(body: str) -> bool:
        """Проверить, что ответ похож на challenge-страницу."""

        content = body.lstrip()
        return (
            content.startswith('<')
            and 'Challenge=' in content
            and 'ChallengeId=' in content
        )
