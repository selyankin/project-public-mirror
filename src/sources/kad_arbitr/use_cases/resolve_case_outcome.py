"""Use-case получения исхода по делу."""

from __future__ import annotations

from sources.kad_arbitr.models import (
    KadArbitrCaseOutcomeNormalized,
    KadArbitrJudicialActNormalized,
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

        selected = _select_act(acts_result.acts)
        act_outcome = await self._act_outcome_uc.execute(act=selected)

        return KadArbitrCaseOutcomeNormalized(
            case_id=case_id,
            act_id=selected.act_id,
            outcome=act_outcome.outcome,
            confidence=act_outcome.confidence,
            matched_phrase=act_outcome.matched_phrase,
            evidence_snippet=act_outcome.evidence_snippet,
            reason=act_outcome.reason,
        )


def _select_act(
    acts: list[KadArbitrJudicialActNormalized],
) -> KadArbitrJudicialActNormalized:
    """Выбрать акт для определения исхода."""

    dated = [act for act in acts if act.act_date is not None]
    if dated:
        return max(dated, key=lambda item: item.act_date or item.act_id)

    return acts[0]
