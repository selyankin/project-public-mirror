"""Risk card aggregate models."""

from __future__ import annotations

from typing import Any

from src.risks.domain.entities.helpers import (
    coerce_risk_level,
    coerce_severity,
    ensure_non_empty_str,
    level_from_score,
)
from src.risks.domain.exceptions.risk import RiskDomainError


class RiskSignal:
    """Single risk signal describing an issue or observation."""

    __slots__ = (
        'code',
        'title',
        'description',
        'severity',
        'evidence_refs',
    )

    def __init__(self, data: dict[str, Any]):
        """Initialize a RiskSignal from raw data."""

        if not isinstance(data, dict):
            raise RiskDomainError('RiskSignal data must be a dict.')

        self.code = ensure_non_empty_str(data.get('code'), 'code', 80)
        self.title = ensure_non_empty_str(data.get('title'), 'title', 200)
        self.description = ensure_non_empty_str(
            data.get('description'),
            'description',
            2000,
        )
        self.severity = coerce_severity(data.get('severity'))
        self.evidence_refs = self._coerce_refs(data.get('evidence_refs'))

    def _coerce_refs(self, value: Any) -> tuple[str, ...]:
        refs: tuple[str, ...]
        if value is None:
            refs = ()

        elif isinstance(value, list | tuple):
            cleaned = []
            for idx, item in enumerate(value):
                cleaned.append(
                    ensure_non_empty_str(
                        item,
                        f'evidence_refs[{idx}]',
                        500,
                    ),
                )
            refs = tuple(cleaned)

        else:
            raise RiskDomainError(
                'evidence_refs must be a sequence of strings.'
            )

        return refs

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the signal."""

        return {
            'code': self.code,
            'title': self.title,
            'description': self.description,
            'severity': int(self.severity),
            'evidence_refs': list(self.evidence_refs),
        }


class RiskCard:
    """Aggregate summarizing risk score and signals."""

    __slots__ = (
        'score',
        'level',
        'summary',
        'signals',
    )

    def __init__(self, data: dict[str, Any]):
        """Initialize a RiskCard from raw data."""
        if not isinstance(data, dict):
            raise RiskDomainError('RiskCard data must be a dict.')

        score_raw = data.get('score')
        if not isinstance(score_raw, int):
            raise RiskDomainError('Score must be an integer.')

        if score_raw < 0 or score_raw > 100:
            raise RiskDomainError('Score must be between 0 and 100.')

        self.score = score_raw
        self.level = coerce_risk_level(data.get('level'))
        self.summary = ensure_non_empty_str(
            data.get('summary'), 'summary', 2000
        )
        self.signals = self._coerce_signals(data.get('signals'))

        expected_level = level_from_score(self.score)
        if self.level != expected_level:
            raise RiskDomainError(
                f'Score {self.score} requires level {expected_level.value}.',
            )

    def _coerce_signals(self, value: Any) -> tuple[RiskSignal, ...]:
        if value is None:
            return ()

        if not isinstance(value, list | tuple):
            raise RiskDomainError('signals must be a list or tuple.')

        normalized = []
        for idx, item in enumerate(value):
            if isinstance(item, RiskSignal):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(RiskSignal(item))
            else:
                raise RiskDomainError(
                    f'signals[{idx}] must be RiskSignal or dict.',
                )

        return tuple(normalized)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the risk card."""
        return {
            'score': self.score,
            'level': self.level.value,
            'summary': self.summary,
            'signals': [signal.to_dict() for signal in self.signals],
        }

    def with_signals(self, signals: list[RiskSignal]) -> RiskCard:
        """Return a copy of this risk card with a new signal list."""
        payload = {
            'score': self.score,
            'level': self.level.value,
            'summary': self.summary,
            'signals': signals,
        }
        return RiskCard(payload)
