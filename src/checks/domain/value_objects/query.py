"""Унифицированный вход проверки адреса или URL."""

from __future__ import annotations

from typing import Any

from checks.domain.exceptions.domain import QueryInputError

from src.checks.domain.constants.enums.domain import QueryType


class CheckQuery:
    """Value object для типизированного запроса проверки."""

    __slots__ = ('type', 'query')

    def __init__(self, data: dict[str, Any]):
        """Создать унифицированный запрос проверки."""

        if not isinstance(data, dict):
            raise QueryInputError('Ожидался словарь параметров запроса.')

        raw_query = data.get('query')
        if not isinstance(raw_query, str):
            raise QueryInputError('Поле query должно быть строкой.')

        trimmed = raw_query.strip()
        if not trimmed:
            raise QueryInputError('Поле query не может быть пустым.')

        if len(trimmed) > 2000:
            raise QueryInputError('Поле query превышает 2000 символов.')

        raw_type = data.get('type')
        try:
            query_type = (
                raw_type
                if isinstance(raw_type, QueryType)
                else QueryType(str(raw_type).strip().lower())
            )

        except (ValueError, AttributeError) as exp:
            raise QueryInputError('Неподдерживаемый тип запроса.') from exp

        self.type: QueryType = query_type
        self.query: str = trimmed
