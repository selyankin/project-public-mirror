"""Модели запроса и ответа kad.arbitr.ru."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(slots=True)
class KadArbitrSideFilter:
    """Фильтр стороны процесса."""

    name: str
    type: int | None = None
    exact_match: bool = False


@dataclass(slots=True)
class KadArbitrSearchPayload:
    """Параметры поиска дел."""

    page: int = 1
    count: int = 25
    sides: list[KadArbitrSideFilter] = field(default_factory=list)
    case_numbers: list[str] = field(default_factory=list)
    courts: list[str] = field(default_factory=list)
    date_from: str | None = None
    date_to: str | None = None

    def to_xhr_dict(self) -> dict[str, object]:
        """Преобразовать запрос в формат XHR."""

        sides_payload = [
            {
                'Name': side.name,
                'Type': side.type,
                'ExactMatch': side.exact_match,
            }
            for side in self.sides
        ]
        return {
            'Page': self.page,
            'Count': self.count,
            'Courts': list(self.courts),
            'DateFrom': self.date_from,
            'DateTo': self.date_to,
            'CaseNumbers': list(self.case_numbers),
            'Sides': sides_payload,
        }


@dataclass(slots=True)
class KadArbitrCaseRaw:
    """Сырой кейс из результата поиска."""

    case_id: str
    case_number: str
    court: str | None = None
    case_type: str | None = None
    start_date: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> KadArbitrCaseRaw:
        """Построить модель дела из словаря."""

        case_id = data.get('CaseId') or data.get('caseId')
        case_number = data.get('CaseNumber') or data.get('caseNumber')
        if not case_id or not case_number:
            raise ValueError('case_id and case_number are required')

        return cls(
            case_id=str(case_id),
            case_number=str(case_number),
            court=_to_str(data.get('CourtName') or data.get('courtName')),
            case_type=_to_str(data.get('CaseType') or data.get('caseType')),
            start_date=_to_str(data.get('Date') or data.get('date')),
        )


@dataclass(slots=True)
class KadArbitrCaseNormalized:
    """Нормализованный кейс kad.arbitr.ru."""

    case_id: str
    case_number: str
    court: str | None = None
    case_type: str | None = None
    start_date: date | None = None
    participant_role: str | None = None
    url: str | None = None


@dataclass(slots=True)
class KadArbitrSearchResponse:
    """Ответ поиска по делам."""

    items: list[KadArbitrCaseRaw] = field(default_factory=list)
    total: int = 0
    page: int = 1
    pages: int = 1

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> KadArbitrSearchResponse:
        """Построить модель ответа из словаря."""

        items_raw = data.get('Items') or data.get('items') or []
        items: list[KadArbitrCaseRaw] = []
        if isinstance(items_raw, list):
            for item in items_raw:
                if isinstance(item, dict):
                    items.append(KadArbitrCaseRaw.from_dict(item))

        total = _to_int(data.get('Total') or data.get('total')) or 0
        page = _to_int(data.get('Page') or data.get('page')) or 1
        pages = _to_int(data.get('Pages') or data.get('pages')) or 1

        return cls(items=items, total=total, page=page, pages=pages)


def _to_str(value: object | None) -> str | None:
    """Преобразовать значение в строку."""
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _to_int(value: object | None) -> int | None:
    """Преобразовать значение в целое число."""
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_iso_date(value: str | None) -> date | None:
    """Безопасно распарсить дату из ISO-строки."""

    if value is None:
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    try:
        return date.fromisoformat(trimmed)
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(trimmed).date()
    except ValueError:
        return None
