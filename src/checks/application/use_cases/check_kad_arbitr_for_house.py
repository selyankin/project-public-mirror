"""Use-case проверки kad.arbitr.ru по данным GIS ЖКХ."""

from __future__ import annotations

from dataclasses import dataclass

from risks.domain.entities.risk_card import RiskSignal
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.kad_arbitr.exceptions import (
    KadArbitrBlockedError,
    KadArbitrClientError,
)
from sources.kad_arbitr.models import KadArbitrCaseNormalized
from sources.kad_arbitr.ports import KadArbitrClientPort
from sources.kad_arbitr.use_cases.resolve_cases_for_participant import (
    ResolveKadArbitrCasesForParticipant,
)


@dataclass(slots=True)
class KadArbitrHouseCheckResult:
    """Результат проверки kad.arbitr.ru для дома."""

    participant_used: str | None
    cases: list[KadArbitrCaseNormalized]
    signals: list[RiskSignal]
    status: str


@dataclass(slots=True)
class CheckKadArbitrForHouse:
    """Оркестрация проверки kad.arbitr.ru по дому."""

    kad_arbitr_client: KadArbitrClientPort
    base_url: str = 'https://kad.arbitr.ru'

    async def execute(
        self,
        *,
        gis_gkh_result: GisGkhHouseNormalized | None,
        max_pages: int = 3,
    ) -> KadArbitrHouseCheckResult:
        """Выполнить проверку по данным GIS ЖКХ."""

        if gis_gkh_result is None:
            return KadArbitrHouseCheckResult(
                participant_used=None,
                cases=[],
                signals=[],
                status='participant_not_found',
            )

        participant = _extract_inn(gis_gkh_result.management_company)
        if not participant:
            participant = _normalize_participant_name(
                gis_gkh_result.management_company
            )

        if not participant:
            return KadArbitrHouseCheckResult(
                participant_used=None,
                cases=[],
                signals=[],
                status='participant_not_found',
            )

        resolver = ResolveKadArbitrCasesForParticipant(
            client=self.kad_arbitr_client,
            base_url=self.base_url,
        )
        try:
            result = await resolver.execute(
                participant=participant,
                max_pages=max_pages,
            )
        except KadArbitrBlockedError:
            return KadArbitrHouseCheckResult(
                participant_used=participant,
                cases=[],
                signals=[],
                status='blocked',
            )
        except KadArbitrClientError:
            return KadArbitrHouseCheckResult(
                participant_used=participant,
                cases=[],
                signals=[],
                status='error',
            )

        return KadArbitrHouseCheckResult(
            participant_used=participant,
            cases=result.cases,
            signals=result.signals,
            status='ok',
        )


def _extract_inn(value: str | None) -> str | None:
    """Попробовать извлечь ИНН из строки."""

    if not value:
        return None

    digits = []
    found = []
    for char in value:
        if char.isdigit():
            digits.append(char)
        else:
            if len(digits) in {10, 12}:
                found.append(''.join(digits))
            digits = []

    if len(digits) in {10, 12}:
        found.append(''.join(digits))

    return found[0] if found else None


def _normalize_participant_name(value: str | None) -> str | None:
    """Подготовить имя участника для поиска."""

    if value is None:
        return None

    trimmed = value.strip()
    return trimmed or None
