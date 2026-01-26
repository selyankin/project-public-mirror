"""Извлечение исхода дела из PDF текста."""

from __future__ import annotations

import re
from dataclasses import dataclass

from sources.kad_arbitr.models import (
    KadArbitrActOutcomeNormalized,
    KadArbitrOutcomeConfidence,
    KadArbitrOutcomeType,
)


@dataclass(frozen=True)
class OutcomeRule:
    """Правило определения исхода."""

    rule_id: str
    outcome: KadArbitrOutcomeType
    confidence: KadArbitrOutcomeConfidence
    patterns: tuple[str, ...]
    negative_patterns: tuple[str, ...] = ()
    priority: int = 100
    notes: str | None = None


@dataclass(frozen=True)
class OutcomeRuleCompiled:
    """Скомпилированное правило исхода."""

    rule: OutcomeRule
    patterns: tuple[re.Pattern[str], ...]
    negative_patterns: tuple[re.Pattern[str], ...]


_RESOLUTION_MARKER_RE = re.compile(
    r'(решил|определил|постановил)\s*:',
    re.IGNORECASE,
)

_RULES: tuple[OutcomeRule, ...] = (
    OutcomeRule(
        rule_id='bankruptcy_bankrupt_declared',
        outcome='bankruptcy_bankrupt_declared',
        confidence='high',
        patterns=(r'признат[ья].{0,40}банкрот',),
        priority=10,
    ),
    OutcomeRule(
        rule_id='bankruptcy_competition',
        outcome='bankruptcy_competition',
        confidence='high',
        patterns=(r'ввест[ьи].{0,60}конкурсн(ое|ого).{0,30}производств',),
        priority=11,
    ),
    OutcomeRule(
        rule_id='bankruptcy_observation',
        outcome='bankruptcy_observation',
        confidence='high',
        patterns=(r'ввест[ьи].{0,60}наблюден',),
        priority=12,
    ),
    OutcomeRule(
        rule_id='settlement_approved',
        outcome='settlement_approved',
        confidence='high',
        patterns=(
            r'утвердит[ья].{0,40}миров(ое|ое соглашение)',
            r'миров(ое|ое соглашение).{0,40}утвердит',
        ),
        priority=20,
    ),
    OutcomeRule(
        rule_id='partial',
        outcome='partial',
        confidence='high',
        patterns=(
            r'удовлетворит[ья].{0,30}частичн',
            r'частичн.{0,30}удовлетворит',
        ),
        negative_patterns=(
            r'просил.{0,40}удовлетвор',
            r'просили.{0,40}удовлетвор',
        ),
        priority=30,
    ),
    OutcomeRule(
        rule_id='satisfied',
        outcome='satisfied',
        confidence='high',
        patterns=(
            r'иск(овые)? требован.{0,80}удовлетворит',
            r'удовлетворит[ья].{0,60}иск',
        ),
        negative_patterns=(
            r'просил.{0,40}удовлетвор',
            r'просили.{0,40}удовлетвор',
        ),
        priority=31,
    ),
    OutcomeRule(
        rule_id='denied',
        outcome='denied',
        confidence='high',
        patterns=(
            r'в удовлетворени.{0,60}отказат',
            r'отказат[ья].{0,60}в удовлетворени',
        ),
        negative_patterns=(
            r'просил.{0,40}отказат',
            r'просили.{0,40}отказат',
        ),
        priority=32,
    ),
    OutcomeRule(
        rule_id='terminated',
        outcome='terminated',
        confidence='medium',
        patterns=(r'прекратит[ья].{0,60}производств',),
        priority=40,
    ),
    OutcomeRule(
        rule_id='left_without_review',
        outcome='left_without_review',
        confidence='medium',
        patterns=(r'оставит[ья].{0,60}без рассмотрени',),
        priority=41,
    ),
    OutcomeRule(
        rule_id='complaint_left_without_movement',
        outcome='complaint_left_without_movement',
        confidence='medium',
        patterns=(r'оставит[ья].{0,60}без движени',),
        priority=42,
    ),
    OutcomeRule(
        rule_id='complaint_returned',
        outcome='complaint_returned',
        confidence='medium',
        patterns=(r'возвратит[ья].{0,60}(жалоб|заявлен|иск)',),
        priority=43,
    ),
    OutcomeRule(
        rule_id='appeal_left_unchanged',
        outcome='appeal_left_unchanged',
        confidence='medium',
        patterns=(
            r'оставит[ья].{0,60}без изменени',
            r'решени.{0,80}оставит[ья].{0,40}без изменени',
        ),
        priority=50,
    ),
    OutcomeRule(
        rule_id='appeal_canceled',
        outcome='appeal_canceled',
        confidence='medium',
        patterns=(
            r'отменит[ья].{0,80}(решени|определени|постановлен)',
            r'(решени|определени|постановлен).{0,80}отменит[ья]',
            r'(решени|определени|постановлен).{0,80}отменить',
            r'отменить.{0,80}(решени|определени|постановлен)',
        ),
        priority=51,
    ),
    OutcomeRule(
        rule_id='appeal_changed',
        outcome='appeal_changed',
        confidence='medium',
        patterns=(
            r'изменит[ья].{0,80}(решени|определени|постановлен)',
            r'(решени|определени|постановлен).{0,80}изменит[ья]',
            r'(решени|определени|постановлен).{0,80}изменить',
            r'изменить.{0,80}(решени|определени|постановлен)',
        ),
        priority=52,
    ),
    OutcomeRule(
        rule_id='complaint_left_unsatisfied',
        outcome='complaint_left_unsatisfied',
        confidence='medium',
        patterns=(
            r'жалоб.{0,40}оставит[ья].{0,40}без удовлетворени',
            r'оставит[ья].{0,40}без удовлетворени.{0,40}жалоб',
        ),
        priority=60,
    ),
)


def normalize_text(value: str) -> str:
    """Нормализовать текст для поиска."""

    lowered = value.lower().replace('ё', 'е')
    return re.sub(r'\s+', ' ', lowered).strip()


def find_with_context(
    text: str,
    pattern: re.Pattern[str],
    *,
    window: int = 240,
) -> tuple[str, str] | None:
    """Найти совпадение и вернуть фразу и контекст."""

    match = pattern.search(text)
    if not match:
        return None

    start, end = match.span()
    left = max(0, start - window)
    right = min(len(text), end + window)
    snippet = text[left:right].strip()
    return match.group(0), snippet


def extract_outcome_from_text(
    *,
    text: str,
) -> KadArbitrActOutcomeNormalized:
    """Определить исход по тексту судебного акта."""

    if not text or not text.strip():
        return _unknown_outcome(reason='empty text')

    normalized = normalize_text(text)
    resolution = _extract_resolution_zone(normalized)

    if resolution:
        result = _match_rules(resolution)
        if result is not None:
            result.notes = 'matched in resolution zone'
            return result

    result = _match_rules(normalized)
    if result is not None:
        return result

    return _unknown_outcome(reason='no patterns matched')


def _compile_rules(
    rules: tuple[OutcomeRule, ...]
) -> tuple[OutcomeRuleCompiled, ...]:
    compiled = []
    for rule in rules:
        compiled.append(
            OutcomeRuleCompiled(
                rule=rule,
                patterns=tuple(
                    re.compile(pat, re.IGNORECASE) for pat in rule.patterns
                ),
                negative_patterns=tuple(
                    re.compile(pat, re.IGNORECASE)
                    for pat in rule.negative_patterns
                ),
            )
        )
    compiled.sort(key=lambda item: item.rule.priority)
    return tuple(compiled)


_COMPILED_RULES = _compile_rules(_RULES)


def _match_rules(text: str) -> KadArbitrActOutcomeNormalized | None:
    for compiled in _COMPILED_RULES:
        match = _match_rule(text, compiled)
        if match is not None:
            return match
    return None


def _match_rule(
    text: str,
    compiled: OutcomeRuleCompiled,
) -> KadArbitrActOutcomeNormalized | None:
    rule = compiled.rule
    for negative in compiled.negative_patterns:
        if negative.search(text):
            return None

    for pattern, pattern_raw in zip(
        compiled.patterns, rule.patterns, strict=False
    ):
        found = find_with_context(text, pattern)
        if not found:
            continue
        matched_phrase, snippet = found
        return KadArbitrActOutcomeNormalized(
            act_id='',
            outcome=rule.outcome,
            confidence=rule.confidence,
            matched_phrase=matched_phrase,
            evidence_snippet=snippet,
            matched_rule_id=rule.rule_id,
            matched_pattern=pattern_raw,
            notes=rule.notes,
        )
    return None


def _extract_resolution_zone(text: str) -> str | None:
    match = _RESOLUTION_MARKER_RE.search(text)
    if not match:
        return None

    start = match.start()
    end = min(len(text), start + 25000)
    return text[start:end]


def _unknown_outcome(*, reason: str) -> KadArbitrActOutcomeNormalized:
    """Сформировать неизвестный исход."""

    return KadArbitrActOutcomeNormalized(
        act_id='',
        outcome='unknown',
        confidence='low',
        reason=reason,
        notes='no rule matched',
    )
