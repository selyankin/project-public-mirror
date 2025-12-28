"""Use-case получения данных Росреестра по кадастровому номеру."""

from __future__ import annotations

from sources.rosreestr.exceptions import RosreestrBadResponseError
from sources.rosreestr.mapper import map_object_to_normalized
from sources.rosreestr.models import RosreestrHouseNormalized
from sources.rosreestr.ports import RosreestrClientPort

__all__ = ['ResolveRosreestrHouseByCadastralUseCase']


class ResolveRosreestrHouseByCadastralUseCase:
    """Возвращает нормализованное описание дома по кадастру."""

    def __init__(self, client: RosreestrClientPort):
        """Конструктор"""

        self.client = client

    def execute(
        self,
        *,
        cadastral_number: str,
    ) -> RosreestrHouseNormalized | None:
        """Получить объект Росреестра или None, если не найден."""

        self._validate_cadastral_number(cadastral_number)
        response = self.client.get_object(cadastral_number=cadastral_number)
        if response.status != 200:
            raise RosreestrBadResponseError(
                f'unexpected status: {response.status}',
            )

        if not response.found or response.object is None:
            return None

        normalized = map_object_to_normalized(response.object)
        if normalized is None:
            raise RosreestrBadResponseError('unable to map object')

        return normalized

    @staticmethod
    def _validate_cadastral_number(value: str) -> None:
        """Проверить базовую корректность кадастрового номера."""

        if not value or ':' not in value:
            raise ValueError('cadastral number must include ":" separators')

        allowed = set('0123456789:')
        if any(char not in allowed for char in value):
            raise ValueError(
                'cadastral number must contain digits and ":" only'
            )
