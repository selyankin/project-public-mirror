"""Value-object для текстового представления адреса."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AddressText:
    """Содержит текст адреса с базовой нормализацией."""

    value: str

    def __post_init__(self) -> None:
        """Проверить непустоту и нормализовать пробелы."""

        normalized = ' '.join((self.value or '').strip().split())
        if not normalized:
            raise ValueError('AddressText не может быть пустым')
        object.__setattr__(self, 'value', normalized)

    def __str__(self) -> str:
        """Вернуть строковое представление."""

        return self.value
