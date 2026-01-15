"""Use-case обогащения дел kad.arbitr.ru."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition
from sources.kad_arbitr.exceptions import (
    KadArbitrBlockedError,
    KadArbitrClientError,
)
from sources.kad_arbitr.models import (
    KadArbitrEnrichedCase,
    KadArbitrParticipantNormalized,
)
from sources.kad_arbitr.signals import build_kad_arbitr_outcome_signals
from sources.kad_arbitr.use_cases.enrich_case_participants import (
    EnrichKadArbitrCaseParticipants,
)
from sources.kad_arbitr.use_cases.resolve_case_outcome import (
    ResolveKadArbitrCaseOutcome,
)
from sources.kad_arbitr.use_cases.resolve_cases_for_participant import (
    ResolveKadArbitrCasesForParticipant,
)


@dataclass(slots=True)
class EnrichKadArbitrCasesResult:
    """Результат обогащения дел по участнику."""

    cases: list[KadArbitrEnrichedCase]
    signals: list[RiskSignal]
    stats: dict[str, int | float]
    status: str


@dataclass(slots=True)
class EnrichKadArbitrCasesForParticipant:
    """Use-case обогащения дел по участнику."""

    search_uc: ResolveKadArbitrCasesForParticipant
    details_uc: EnrichKadArbitrCaseParticipants
    case_outcome_uc: ResolveKadArbitrCaseOutcome
    base_url: str = 'https://kad.arbitr.ru'

    async def execute(
        self,
        *,
        participant: str,
        participant_type: int | None = None,
        max_pages: int = 2,
        max_cases: int = 20,
    ) -> EnrichKadArbitrCasesResult:
        """Обогатить дела по участнику."""

        try:
            search_result = await self.search_uc.execute(
                participant=participant,
                participant_type=participant_type,
                max_pages=max_pages,
            )
            cases_sorted = sorted(
                search_result.cases,
                key=lambda item: item.start_date or date.min,
                reverse=True,
            )
            limited = cases_sorted[:max_cases]
            enriched_cases: list[KadArbitrEnrichedCase] = []
            for case in limited:
                details = await self.details_uc.execute(
                    case_id=case.case_id,
                    target_participant=participant,
                )
                target_role = _select_target_role(details.participants)
                outcome = await self.case_outcome_uc.execute(
                    case_id=case.case_id,
                )
                enriched_cases.append(
                    KadArbitrEnrichedCase(
                        case_id=case.case_id,
                        case_number=case.case_number,
                        start_date=case.start_date,
                        target_role=target_role,
                        outcome=outcome.outcome,
                        confidence=outcome.confidence,
                        act_id=outcome.act_id,
                        evidence_snippet=outcome.evidence_snippet,
                        card_url=details.card_url,
                    )
                )

        except KadArbitrBlockedError:
            return EnrichKadArbitrCasesResult(
                cases=[],
                signals=[_build_status_signal('kad_arbitr_source_blocked')],
                stats={},
                status='blocked',
            )

        except KadArbitrClientError:
            return EnrichKadArbitrCasesResult(
                cases=[],
                signals=[_build_status_signal('kad_arbitr_source_error')],
                stats={},
                status='error',
            )

        outcome_signals = build_kad_arbitr_outcome_signals(
            cases=enriched_cases,
        )
        stats = {
            'total': len(enriched_cases),
            'max_cases': max_cases,
        }
        return EnrichKadArbitrCasesResult(
            cases=enriched_cases,
            signals=outcome_signals,
            stats=stats,
            status='ok',
        )


def _select_target_role(
    participants: list[KadArbitrParticipantNormalized],
) -> str | None:
    """Выбрать роль целевого участника."""

    priority = {
        'defendant': 3,
        'plaintiff': 2,
        'third_party': 1,
        'other': 0,
    }
    selected_role = None
    selected_score = -1
    for participant in participants:
        if not participant.is_target_participant:
            continue

        role = participant.role
        score = priority.get(role or '', 0)
        if score > selected_score:
            selected_role = role
            selected_score = score

    return selected_role


def _build_status_signal(code: str) -> RiskSignal:
    """Собрать системный сигнал статуса."""

    definition = get_signal_definition(code)
    if code == 'kad_arbitr_source_blocked':
        status = 'blocked'
    elif code == 'kad_arbitr_source_error':
        status = 'error'
    else:
        status = 'unknown'

    return RiskSignal(
        {
            'code': definition.code,
            'title': definition.title,
            'description': definition.description,
            'severity': int(definition.severity),
            'evidence_refs': [],
            'details': {
                'status': status,
                'source': 'kad_arbitr',
            },
        }
    )
