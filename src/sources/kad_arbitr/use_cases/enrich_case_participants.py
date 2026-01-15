"""Use-case обогащения участников дела kad.arbitr.ru."""

from __future__ import annotations

from dataclasses import replace

from sources.kad_arbitr.models import (
    KadArbitrCaseDetailsNormalized,
    is_inn,
    is_probably_same_participant,
    normalize_inn,
)
from sources.kad_arbitr.use_cases.resolve_case_details import (
    ResolveKadArbitrCaseDetails,
)


class EnrichKadArbitrCaseParticipants:
    """Use-case обогащения участников дела."""

    def __init__(
        self,
        *,
        details_uc: ResolveKadArbitrCaseDetails,
    ) -> None:
        """Сохранить зависимости use-case."""

        self._details_uc = details_uc

    async def execute(
        self,
        *,
        case_id: str,
        target_participant: str,
    ) -> KadArbitrCaseDetailsNormalized:
        """Обогатить участников и определить целевого."""

        details = await self._details_uc.execute(case_id=case_id)
        target_norm = normalize_inn(target_participant)
        target_is_inn = target_norm is not None and is_inn(target_norm)
        updated = []

        for participant in details.participants:
            if target_is_inn:
                is_target = participant.inn == target_norm
            else:
                is_target = is_probably_same_participant(
                    target=target_participant,
                    candidate=participant.name,
                )
            updated.append(
                replace(
                    participant,
                    is_target_participant=is_target,
                )
            )

        return replace(details, participants=updated)
