"""Проверка use-case обогащения дел kad.arbitr.ru."""

from datetime import date

import pytest

from sources.kad_arbitr.models import (
    KadArbitrCaseDetailsNormalized,
    KadArbitrCaseNormalized,
    KadArbitrCaseOutcomeNormalized,
    KadArbitrParticipantNormalized,
)
from sources.kad_arbitr.use_cases.enrich_cases_for_participant import (
    EnrichKadArbitrCasesForParticipant,
)


class _SearchStub:
    async def execute(
        self,
        *,
        participant: str,
        participant_type: int | None = None,
        max_pages: int = 3,
    ):
        return type(
            'Result',
            (),
            {
                'cases': [
                    KadArbitrCaseNormalized(
                        case_id='1',
                        case_number='А40-1/2025',
                        start_date=date(2025, 1, 10),
                        participant_role='defendant',
                    ),
                    KadArbitrCaseNormalized(
                        case_id='2',
                        case_number='А40-2/2025',
                        start_date=date(2025, 2, 10),
                        participant_role='defendant',
                    ),
                ]
            },
        )()


class _ParticipantsStub:
    async def execute(self, *, case_id: str, target_participant: str):
        participants = [
            KadArbitrParticipantNormalized(
                name='ООО Ромашка',
                role='defendant',
                inn='7701234567',
                is_target_participant=True,
            )
        ]
        return KadArbitrCaseDetailsNormalized(
            case_id=case_id,
            participants=participants,
            card_url=f'https://kad.arbitr.ru/Card/{case_id}',
        )


class _OutcomeStub:
    async def execute(self, *, case_id: str):
        if case_id == '2':
            return KadArbitrCaseOutcomeNormalized(
                case_id=case_id,
                act_id='act-2',
                outcome='satisfied',
                confidence='high',
                evidence_snippet='удовлетворить иск',
                extracted_text=(
                    'Договор долевого участия по 214-ФЗ. '
                    'Взыскать 2 000 000 руб.'
                ),
            )
        return KadArbitrCaseOutcomeNormalized(
            case_id=case_id,
            act_id='act-1',
            outcome='unknown',
            confidence='low',
        )


pytestmark = pytest.mark.asyncio


async def test_enrich_cases_for_participant_collects_signals() -> None:
    use_case = EnrichKadArbitrCasesForParticipant(
        search_uc=_SearchStub(),
        details_uc=_ParticipantsStub(),
        case_outcome_uc=_OutcomeStub(),
    )

    result = await use_case.execute(participant='ООО Ромашка', max_cases=2)

    assert len(result.facts.cases) == 2
    assert result.facts.status == 'ok'
    enriched = result.facts.cases[0]
    assert 'ddu_penalty' in enriched.claim_categories
    assert 2000000 in enriched.amounts
    assert enriched.impact == 'negative'


async def test_enrich_cases_for_participant_respects_limit() -> None:
    use_case = EnrichKadArbitrCasesForParticipant(
        search_uc=_SearchStub(),
        details_uc=_ParticipantsStub(),
        case_outcome_uc=_OutcomeStub(),
    )

    result = await use_case.execute(participant='ООО Ромашка', max_cases=1)

    assert len(result.facts.cases) == 1
