"""Декоратор клиента Росреестра с кэшированием."""

from __future__ import annotations

from sources.rosreestr.cache.ports import RosreestrCachePort
from sources.rosreestr.dto import RosreestrApiResponse
from sources.rosreestr.ports import RosreestrClientPort


class CachedRosreestrClient(RosreestrClientPort):
    """Клиент Росреестра с кэшем ответов."""

    def __init__(
        self,
        *,
        inner: RosreestrClientPort,
        cache: RosreestrCachePort,
        ttl_seconds: int,
    ) -> None:
        """Сохранить зависимости."""

        self._inner = inner
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    def get_object(
        self,
        *,
        cadastral_number: str,
    ) -> RosreestrApiResponse:
        """Получить объект Росреестра с кэшированием."""

        key = f'rosreestr:object:{cadastral_number}'
        cached = self._cache.get(key=key)
        if cached:
            return RosreestrApiResponse.from_dict(cached)

        response = self._inner.get_object(cadastral_number=cadastral_number)
        if response.status == 200 and response.found:
            self._cache.set(
                key=key,
                value=response.to_dict(),
                ttl_seconds=self._ttl_seconds,
            )
        return response

    def find_cadastrals(self, *, address: str) -> list[str]:
        """Проксировать поисковый метод без кэша."""

        return self._inner.find_cadastrals(address=address)
