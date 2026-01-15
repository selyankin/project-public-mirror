"""Проверка use-case определения исхода по делу."""

from datetime import date

import pytest

from sources.kad_arbitr.models import KadArbitrJudicialActNormalized
from sources.kad_arbitr.use_cases.resolve_case_outcome import (
    ResolveKadArbitrCaseOutcome,
)


class _ActsStub:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def execute(self, *, case_id: str):
        self.calls.append(case_id)
        return type(
            'ActsResult',
            (),
            {
                'acts': [
                    KadArbitrJudicialActNormalized(
                        act_id='old',
                        act_type='decision',
                        act_date=date(2024, 1, 1),
                    ),
                    KadArbitrJudicialActNormalized(
                        act_id='new',
                        act_type='decision',
                        act_date=date(2025, 1, 1),
                    ),
                ]
            },
        )()


class _OutcomeStub:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def execute(self, *, act: KadArbitrJudicialActNormalized):
        self.calls.append(act.act_id)
        return type(
            'Outcome',
            (),
            {
                'outcome': 'satisfied',
                'confidence': 'high',
                'matched_phrase': 'удовлетворить',
                'evidence_snippet': 'удовлетворить иск',
                'reason': None,
            },
        )()


pytestmark = pytest.mark.asyncio


async def test_resolve_case_outcome_selects_latest_act() -> None:
    acts_uc = _ActsStub()
    outcome_uc = _OutcomeStub()
    use_case = ResolveKadArbitrCaseOutcome(
        acts_uc=acts_uc,
        act_outcome_uc=outcome_uc,
    )

    result = await use_case.execute(case_id='case-1')

    assert result.act_id == 'new'
    assert outcome_uc.calls == ['new']
