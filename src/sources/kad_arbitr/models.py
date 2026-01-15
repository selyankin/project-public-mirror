"""Модели запроса и ответа kad.arbitr.ru."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal


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
class KadArbitrParticipantNormalized:
    """Нормализованный участник дела."""

    name: str
    role: str
    inn: str | None = None
    ogrn: str | None = None
    is_target_participant: bool = False


@dataclass(slots=True)
class KadArbitrCaseDetailsNormalized:
    """Нормализованные детали карточки дела."""

    case_id: str
    case_number: str | None = None
    court: str | None = None
    participants: list[KadArbitrParticipantNormalized] = field(
        default_factory=list,
    )
    card_url: str | None = None


@dataclass(slots=True)
class KadArbitrJudicialActNormalized:
    """Нормализованный судебный акт."""

    act_id: str
    act_type: str
    act_type_raw: str | None = None
    act_date: date | None = None
    pdf_url: str | None = None
    raw_url: str | None = None
    title: str | None = None


@dataclass(slots=True)
class KadArbitrCaseActsNormalized:
    """Нормализованные судебные акты по делу."""

    case_id: str
    card_url: str | None = None
    acts: list[KadArbitrJudicialActNormalized] = field(default_factory=list)


KadArbitrOutcomeType = Literal[
    'satisfied',
    'denied',
    'partial',
    'terminated',
    'left_without_review',
    'settlement_approved',
    'bankruptcy_observation',
    'bankruptcy_competition',
    'bankruptcy_bankrupt_declared',
    'unknown',
]

KadArbitrOutcomeConfidence = Literal['high', 'medium', 'low']


@dataclass(slots=True)
class KadArbitrActOutcomeNormalized:
    """Нормализованный исход судебного акта."""

    act_id: str
    outcome: KadArbitrOutcomeType
    confidence: KadArbitrOutcomeConfidence
    matched_phrase: str | None = None
    evidence_snippet: str | None = None
    reason: str | None = None
    source: str = 'kad_arbitr_pdf'


@dataclass(slots=True)
class KadArbitrCaseOutcomeNormalized:
    """Нормализованный исход по делу."""

    case_id: str
    act_id: str | None = None
    outcome: KadArbitrOutcomeType = 'unknown'
    confidence: KadArbitrOutcomeConfidence = 'low'
    matched_phrase: str | None = None
    evidence_snippet: str | None = None
    reason: str | None = None


@dataclass(slots=True)
class KadArbitrEnrichedCase:
    """Обогащённый кейс kad.arbitr.ru."""

    case_id: str
    case_number: str | None = None
    start_date: date | None = None
    target_role: str | None = None
    outcome: KadArbitrOutcomeType = 'unknown'
    confidence: KadArbitrOutcomeConfidence = 'low'
    act_id: str | None = None
    evidence_snippet: str | None = None
    card_url: str | None = None


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


def parse_ru_date(value: str | None) -> date | None:
    """Безопасно распарсить дату из русской строки."""

    if value is None:
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    try:
        return datetime.strptime(trimmed, '%d.%m.%Y').date()
    except ValueError:
        pass

    try:
        return date.fromisoformat(trimmed)
    except ValueError:
        return None


def map_act_type(raw: str | None) -> str:
    """Сопоставить тип судебного акта."""

    if raw is None:
        return 'other'

    lowered = raw.lower()
    if 'решен' in lowered:
        return 'decision'
    if 'определен' in lowered:
        return 'determination'
    if 'постановлен' in lowered:
        return 'resolution'
    return 'other'


def normalize_inn(value: str | None) -> str | None:
    """Нормализовать ИНН."""

    if value is None:
        return None

    digits = ''.join(char for char in value if char.isdigit())
    if len(digits) in (10, 12):
        return digits

    return None


def normalize_ogrn(value: str | None) -> str | None:
    """Нормализовать ОГРН."""

    if value is None:
        return None

    digits = ''.join(char for char in value if char.isdigit())
    if len(digits) in (13, 15):
        return digits

    return None


def normalize_participant_name(value: str) -> str:
    """Нормализовать имя участника."""

    cleaned = value.lower().replace('ё', 'е')
    for char in ('«', '»', '"', "'", ',', '.', '(', ')'):
        cleaned = cleaned.replace(char, ' ')
    cleaned = ' '.join(cleaned.split())
    for prefix in ('ооо', 'оао', 'зао', 'пао', 'ао'):
        if cleaned.startswith(prefix + ' '):
            cleaned = cleaned[len(prefix) + 1 :]
            break
    return cleaned.strip()


def is_probably_same_participant(*, target: str, candidate: str) -> bool:
    """Проверить, что участники совпадают по имени."""

    target_norm = normalize_participant_name(target)
    candidate_norm = normalize_participant_name(candidate)
    if not target_norm or not candidate_norm:
        return False
    if target_norm == candidate_norm:
        return True
    if len(target_norm) >= 6 and target_norm in candidate_norm:
        return True
    if len(candidate_norm) >= 6 and candidate_norm in target_norm:
        return True
    return False


def is_inn(value: str) -> bool:
    """Проверить, что строка является ИНН."""

    digits = ''.join(char for char in value if char.isdigit())
    return len(digits) in (10, 12)


def is_ogrn(value: str) -> bool:
    """Проверить, что строка является ОГРН."""

    digits = ''.join(char for char in value if char.isdigit())
    return len(digits) in (13, 15)


def is_bankruptcy_outcome(outcome: str) -> bool:
    """Проверить, что исход относится к банкротству."""

    return outcome in {
        'bankruptcy_observation',
        'bankruptcy_competition',
        'bankruptcy_bankrupt_declared',
    }


def is_negative_outcome_for_defendant(outcome: str) -> bool:
    """Проверить, что исход негативен для ответчика."""

    return outcome in {
        'satisfied',
        'partial',
        'bankruptcy_observation',
        'bankruptcy_competition',
        'bankruptcy_bankrupt_declared',
    }


def is_negative_outcome_for_plaintiff(outcome: str) -> bool:
    """Проверить, что исход негативен для истца."""

    return outcome in {'denied'}
