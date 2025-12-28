"""Реализация клиента Росреестра через api-cloud.ru."""

from __future__ import annotations

import httpx

from sources.rosreestr.dto import RosreestrApiResponse
from sources.rosreestr.exceptions import RosreestrClientError
from sources.rosreestr.ports import RosreestrClientPort

API_URL = 'https://api-cloud.ru/api/rosreestr.php'


class ApiCloudRosreestrClient(RosreestrClientPort):
    """HTTP-клиент для Rosreestr API-Cloud."""

    __slots__ = ('_client', '_token', '_timeout')

    def __init__(
        self,
        *,
        token: str | None,
        timeout_seconds: int = 120,
        client: httpx.Client | None = None,
    ) -> None:
        """Сохранить параметры доступа."""

        if not token:
            raise RosreestrClientError('token is required')
        self._token = token
        self._timeout = timeout_seconds
        self._client = client or httpx.Client(timeout=self._timeout)

    def get_object(self, *, cadastral_number: str) -> RosreestrApiResponse:
        """Получить объект по кадастровому номеру."""

        params = {
            'type': 'object',
            'cadastr': cadastral_number,
        }
        response = self._request(params)
        return RosreestrApiResponse.from_dict(response)

    def _request(self, params: dict[str, str]) -> dict | list | None:
        headers = {'Token': self._token}

        try:
            response = self._client.get(
                API_URL,
                params=params,
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()

        except httpx.HTTPError as exc:
            raise RosreestrClientError(str(exc)) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise RosreestrClientError('invalid json') from exc
