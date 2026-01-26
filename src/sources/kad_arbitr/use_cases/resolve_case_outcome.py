"""Use-case получения исхода по делу."""

from __future__ import annotations

from sources.kad_arbitr.acts_selector import select_final_act
from sources.kad_arbitr.models import (
    KadArbitrCaseOutcomeNormalized,
)
from sources.kad_arbitr.use_cases.resolve_act_outcome import (
    ResolveKadArbitrActOutcome,
)
from sources.kad_arbitr.use_cases.resolve_case_acts import (
    ResolveKadArbitrCaseActs,
)


class ResolveKadArbitrCaseOutcome:
    """Use-case определения исхода по делу."""

    def __init__(
        self,
        *,
        acts_uc: ResolveKadArbitrCaseActs,
        act_outcome_uc: ResolveKadArbitrActOutcome,
    ) -> None:
        """Сохранить зависимости use-case."""

        self._acts_uc = acts_uc
        self._act_outcome_uc = act_outcome_uc

    async def execute(self, *, case_id: str) -> KadArbitrCaseOutcomeNormalized:
        """Определить исход по делу."""

        acts_result = await self._acts_uc.execute(case_id=case_id)
        if not acts_result.acts:
            return KadArbitrCaseOutcomeNormalized(
                case_id=case_id,
                reason='no acts found',
            )

        selected = select_final_act(acts=acts_result.acts)
        if selected is None:
            return KadArbitrCaseOutcomeNormalized(
                case_id=case_id,
                reason='no acts found',
            )

        act_outcome = await self._act_outcome_uc.execute(act=selected)

        return KadArbitrCaseOutcomeNormalized(
            case_id=case_id,
            act_id=selected.act_id,
            outcome=act_outcome.outcome,
            confidence=act_outcome.confidence,
            extracted_text=getattr(act_outcome, 'extracted_text', None),
            matched_phrase=act_outcome.matched_phrase,
            evidence_snippet=act_outcome.evidence_snippet,
            reason=act_outcome.reason,
        )
