"""Catalog of risk signal definitions."""

from __future__ import annotations

from typing import Any

from risks.domain.constants.enums.risk import SignalSeverity
from risks.domain.exceptions.risk import RiskDomainError


class SignalDefinition:
    """Definition of a risk signal."""

    __slots__ = (
        'code',
        'title',
        'description',
        'severity',
    )

    def __init__(self, data: dict[str, Any]):
        """Create a signal definition from raw data."""

        if not isinstance(data, dict):
            raise RiskDomainError('SignalDefinition data must be a dict.')

        self.code = self._ensure_non_empty(data.get('code'), 'code', 80)
        self.title = self._ensure_non_empty(data.get('title'), 'title', 200)
        self.description = self._ensure_non_empty(
            data.get('description'),
            'description',
            2000,
        )
        self.severity = self._coerce_severity(data.get('severity'))

    @staticmethod
    def _ensure_non_empty(
        value: Any,
        field: str,
        max_len: int,
    ) -> str:
        if not isinstance(value, str):
            raise RiskDomainError(f'{field} must be a string.')

        trimmed = value.strip()
        if not trimmed:
            raise RiskDomainError(f'{field} cannot be empty.')

        if len(trimmed) > max_len:
            raise RiskDomainError(f'{field} length must be <= {max_len}.')

        return trimmed

    def _coerce_severity(self, value: Any) -> SignalSeverity:
        if isinstance(value, SignalSeverity):
            return value

        if isinstance(value, int):
            try:
                return SignalSeverity(value)
            except ValueError as exc:
                raise RiskDomainError(f'Unknown severity: {value}') from exc

        if isinstance(value, str):
            key = value.strip().lower()
            if not key:
                raise RiskDomainError('Severity cannot be empty.')

            if key.isdigit():
                return self._coerce_severity(int(key))

            try:
                return SignalSeverity[key]
            except KeyError as exc:
                raise RiskDomainError(f'Unknown severity: {value!r}') from exc

        raise RiskDomainError('Severity must be str, int, or SignalSeverity.')

    def to_dict(self) -> dict[str, Any]:
        """Serialize definition to a plain dict."""
        return {
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'severity': int(self.severity),
        }


DEFINITIONS: dict[str, SignalDefinition] = {
    'address_incomplete': SignalDefinition(
        {
            'code': 'address_incomplete',
            'title': 'Incomplete address',
            'description': (
                'The provided address looks incomplete for reliable checks'
            ),
            'severity': 'medium',
        },
    ),
    'possible_apartments': SignalDefinition(
        {
            'code': 'possible_apartments',
            'title': 'Possible apartments',
            'description': (
                'Address text may indicate apartments; '
                'legal status may differ'
            ),
            'severity': 'medium',
        },
    ),
    'hostel_keyword': SignalDefinition(
        {
            'code': 'hostel_keyword',
            'title': 'Hostel / dormitory indication',
            'description': 'Address text may indicate a dormitory format',
            'severity': 'high',
        },
    ),
    'residential_complex_hint': SignalDefinition(
        {
            'code': 'residential_complex_hint',
            'title': 'Residential complex mentioned',
            'description': (
                'The query mentions a residential complex; '
                'verify developer and project data'
            ),
            'severity': 'low',
        },
    ),
    'address_confidence_unknown': SignalDefinition(
        {
            'code': 'address_confidence_unknown',
            'title': 'Невозможно определить точность адреса',
            'description': (
                'Запрос адреса слишком общий или неструктурный, '
                'что снижает точность проверки'
            ),
            'severity': SignalSeverity.medium,
        },
    ),
    'address_confidence_low': SignalDefinition(
        {
            'code': 'address_confidence_low',
            'title': 'Низкая точность адреса',
            'description': (
                'Адрес содержит только населённый пункт и не позволяет '
                'однозначно определить объект'
            ),
            'severity': SignalSeverity.medium,
        },
    ),
    'address_source_stub': SignalDefinition(
        {
            'code': 'address_source_stub',
            'title': 'Адрес определён без ФИАС',
            'description': (
                'Нормализация выполнена локально и может отличаться от '
                'данных ФИАС'
            ),
            'severity': SignalSeverity.low,
        },
    ),
    'url_not_supported_yet': SignalDefinition(
        {
            'code': 'url_not_supported_yet',
            'title': 'URL checks are not supported yet',
            'description': (
                'The provided URL cannot be processed at the moment'
            ),
            'severity': 'low',
        },
    ),
    'query_type_not_supported': SignalDefinition(
        {
            'code': 'query_type_not_supported',
            'title': 'Query type is not supported yet',
            'description': (
                'This query type is not supported in the current version'
            ),
            'severity': 'low',
        },
    ),
    'query_not_address_like': SignalDefinition(
        {
            'code': 'query_not_address_like',
            'title': 'Query is not address-like',
            'description': 'The provided text does not look like an address',
            'severity': 'medium',
        },
    ),
    'kad_arbitr_has_bankruptcy_cases': SignalDefinition(
        {
            'code': 'kad_arbitr_has_bankruptcy_cases',
            'title': 'Найдены дела о банкротстве',
            'description': (
                'В истории участника присутствуют дела о банкротстве'
            ),
            'severity': SignalSeverity.high,
        },
    ),
    'kad_arbitr_many_cases_last_12m': SignalDefinition(
        {
            'code': 'kad_arbitr_many_cases_last_12m',
            'title': 'Много дел за последние 12 месяцев',
            'description': ('Количество дел за последний год превышает порог'),
            'severity': SignalSeverity.medium,
        },
    ),
    'kad_arbitr_mostly_defendant': SignalDefinition(
        {
            'code': 'kad_arbitr_mostly_defendant',
            'title': 'Участник чаще ответчик',
            'description': (
                'Большая часть дел содержит участника как ответчика'
            ),
            'severity': SignalSeverity.medium,
        },
    ),
    'kad_arbitr_no_cases_found': SignalDefinition(
        {
            'code': 'kad_arbitr_no_cases_found',
            'title': 'Дела в kad.arbitr.ru не найдены',
            'description': ('По участнику не найдено судебных дел в базе'),
            'severity': SignalSeverity.info,
        },
    ),
}

ORDERED_CODES: tuple[str, ...] = (
    'address_incomplete',
    'possible_apartments',
    'hostel_keyword',
    'residential_complex_hint',
    'address_confidence_unknown',
    'address_confidence_low',
    'address_source_stub',
    'url_not_supported_yet',
    'query_type_not_supported',
    'query_not_address_like',
    'kad_arbitr_has_bankruptcy_cases',
    'kad_arbitr_many_cases_last_12m',
    'kad_arbitr_mostly_defendant',
    'kad_arbitr_no_cases_found',
)


def get_signal_definition(code: str) -> SignalDefinition:
    """Return signal definition by code."""
    try:
        return DEFINITIONS[code]
    except KeyError as exc:
        raise KeyError(f'Signal definition not found: {code!r}') from exc


def all_signal_definitions() -> tuple[SignalDefinition, ...]:
    """Return all signal definitions in stable order."""
    return tuple(DEFINITIONS[code] for code in ORDERED_CODES)
