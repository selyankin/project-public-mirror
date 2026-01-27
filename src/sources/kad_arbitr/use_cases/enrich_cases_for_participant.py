"""Use-case обогащения дел kad.arbitr.ru."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sources.kad_arbitr.amounts_extractor import extract_amounts
from sources.kad_arbitr.claim_classifier import classify_claim
from sources.kad_arbitr.exceptions import (
    KadArbitrBlockedError,
    KadArbitrClientError,
)
from sources.kad_arbitr.models import (
    KadArbitrEnrichedCase,
    KadArbitrFacts,
    KadArbitrParticipantNormalized,
    evaluate_outcome_impact,
    map_role_to_group,
)
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

    facts: KadArbitrFacts


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
        except KadArbitrBlockedError:
            return EnrichKadArbitrCasesResult(
                facts=KadArbitrFacts(
                    status='blocked',
                    participant=participant,
                    participant_type=participant_type,
                    cases=[],
                    stats={},
                    reason='blocked',
                ),
            )
        except KadArbitrClientError:
            return EnrichKadArbitrCasesResult(
                facts=KadArbitrFacts(
                    status='error',
                    participant=participant,
                    participant_type=participant_type,
                    cases=[],
                    stats={},
                    reason='error',
                ),
            )

        cases_sorted = sorted(
            search_result.cases,
            key=lambda item: item.start_date or date.min,
            reverse=True,
        )
        limited = cases_sorted[:max_cases]
        enriched_cases: list[KadArbitrEnrichedCase] = []
        errors_count = 0
        error_examples: list[dict[str, str]] = []
        for case in limited:
            try:
                details = await self.details_uc.execute(
                    case_id=case.case_id,
                    target_participant=participant,
                )
                target_role = _select_target_role(details.participants)
                outcome = await self.case_outcome_uc.execute(
                    case_id=case.case_id,
                )
                outcome_text = outcome.extracted_text or ''
                claim_result = classify_claim(text=outcome_text)
                amounts_result = extract_amounts(
                    text=outcome_text,
                    max_amounts=3,
                )
                role_group = map_role_to_group(target_role)
                impact, impact_confidence = evaluate_outcome_impact(
                    outcome=outcome.outcome,
                    role_group=role_group,
                )
                enriched_cases.append(
                    KadArbitrEnrichedCase(
                        case_id=case.case_id,
                        case_number=case.case_number,
                        start_date=case.start_date,
                        case_type=case.case_type,
                        court=case.court,
                        url=case.url,
                        target_role=target_role,
                        target_role_group=role_group,
                        outcome=outcome.outcome,
                        confidence=outcome.confidence,
                        impact=impact,
                        impact_confidence=impact_confidence,
                        act_id=outcome.act_id,
                        evidence_snippet=outcome.evidence_snippet,
                        card_url=details.card_url,
                        claim_categories=claim_result.categories,
                        claim_confidence=claim_result.confidence,
                        claim_matched_keywords=claim_result.matched_keywords,
                        amounts=amounts_result.amounts,
                        amounts_fragments=amounts_result.matched_fragments,
                    )
                )
            except KadArbitrBlockedError:
                return EnrichKadArbitrCasesResult(
                    facts=KadArbitrFacts(
                        status='blocked',
                        participant=participant,
                        participant_type=participant_type,
                        cases=[],
                        stats={},
                        reason='blocked',
                    ),
                )
            except Exception as exc:
                errors_count += 1
                if len(error_examples) < 3:
                    error_examples.append(
                        {
                            'case_id': case.case_id,
                            'error': exc.__class__.__name__,
                        }
                    )
                continue

        stats = {
            'cases_total_found': len(limited),
            'cases_enriched_ok': len(enriched_cases),
            'cases_failed': errors_count,
            'cases_skipped': 0,
            'max_cases': max_cases,
        }
        if error_examples:
            stats['errors_examples'] = error_examples

        return EnrichKadArbitrCasesResult(
            facts=KadArbitrFacts(
                status='ok',
                participant=participant,
                participant_type=participant_type,
                cases=enriched_cases,
                stats=stats,
                reason=None,
            ),
        )


def _select_target_role(
    participants: list[KadArbitrParticipantNormalized],
) -> str | None:
    """Выбрать роль целевого участника."""

    priority = {
        'debtor': 0,
        'defendant': 0,
        'creditor': 1,
        'applicant': 1,
        'plaintiff': 1,
        'third_party': 2,
        'other': 3,
        None: 4,
    }
    selected_role = None
    selected_score = 99
    selected_inn = False
    selected_name_len = 0

    for participant in participants:
        if not participant.is_target_participant:
            continue

        role = participant.role
        score = priority.get(role, 4)
        has_inn = bool(participant.inn)
        name_len = len(participant.name.strip())
        if score < selected_score:
            selected_role = role
            selected_score = score
            selected_inn = has_inn
            selected_name_len = name_len
            continue

        if score != selected_score:
            continue

        if has_inn and not selected_inn:
            selected_role = role
            selected_inn = True
            selected_name_len = name_len
            continue

        if has_inn == selected_inn and name_len > selected_name_len:
            selected_role = role
            selected_name_len = name_len

    return selected_role
