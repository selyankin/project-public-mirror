"""Проверка best-effort обогащения дел kad.arbitr.ru."""

from datetime import date

import pytest

from sources.kad_arbitr.exceptions import KadArbitrBlockedError
from sources.kad_arbitr.models import (
    KadArbitrCaseDetailsNormalized,
    KadArbitrCaseNormalized,
    KadArbitrCaseOutcomeNormalized,
    KadArbitrParticipantNormalized,
)
from sources.kad_arbitr.use_cases.enrich_cases_for_participant import (
    EnrichKadArbitrCasesForParticipant,
)

pytestmark = pytest.mark.asyncio


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
                    ),
                    KadArbitrCaseNormalized(
                        case_id='2',
                        case_number='А40-2/2025',
                        start_date=date(2025, 2, 10),
                    ),
                    KadArbitrCaseNormalized(
                        case_id='3',
                        case_number='А40-3/2025',
                        start_date=date(2025, 3, 10),
                    ),
                ]
            },
        )()


class _ParticipantsErrorStub:
    async def execute(self, *, case_id: str, target_participant: str):
        if case_id == '2':
            raise ValueError('broken')
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


class _ParticipantsBlockedStub:
    async def execute(self, *, case_id: str, target_participant: str):
        if case_id == '2':
            raise KadArbitrBlockedError('blocked')
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
        return KadArbitrCaseOutcomeNormalized(
            case_id=case_id,
            act_id=f'act-{case_id}',
            outcome='satisfied',
            confidence='high',
            extracted_text='Взыскать 1 000 000 руб.',
        )


async def test_enrich_best_effort_skips_errors() -> None:
    use_case = EnrichKadArbitrCasesForParticipant(
        search_uc=_SearchStub(),
        details_uc=_ParticipantsErrorStub(),
        case_outcome_uc=_OutcomeStub(),
    )

    result = await use_case.execute(participant='ООО Ромашка', max_cases=3)

    assert result.facts.status == 'ok'
    assert len(result.facts.cases) == 2
    assert result.facts.stats['cases_failed'] == 1


async def test_enrich_best_effort_blocked() -> None:
    use_case = EnrichKadArbitrCasesForParticipant(
        search_uc=_SearchStub(),
        details_uc=_ParticipantsBlockedStub(),
        case_outcome_uc=_OutcomeStub(),
    )

    result = await use_case.execute(participant='ООО Ромашка', max_cases=3)

    assert result.facts.status == 'blocked'
    assert result.facts.cases == []
