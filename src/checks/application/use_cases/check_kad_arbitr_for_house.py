"""Use-case проверки kad.arbitr.ru по данным GIS ЖКХ."""

from __future__ import annotations

from dataclasses import dataclass

from checks.application.kad_arbitr.kad_arbitr_signal_builder import (
    build_kad_arbitr_signals_from_facts,
)
from risks.domain.entities.risk_card import RiskSignal
from risks.domain.signals_catalog import get_signal_definition
from sources.gis_gkh.models import GisGkhHouseNormalized
from sources.kad_arbitr.exceptions import (
    KadArbitrBlockedError,
    KadArbitrClientError,
)
from sources.kad_arbitr.models import KadArbitrFacts
from sources.kad_arbitr.pdf.http_pdf_fetcher import HttpPdfFetcher
from sources.kad_arbitr.pdf.text_extractors import (
    CompositePdfTextExtractor,
    PdfMinerTextExtractor,
    PyPdfTextExtractor,
)
from sources.kad_arbitr.ports import KadArbitrClientPort
from sources.kad_arbitr.use_cases.enrich_case_participants import (
    EnrichKadArbitrCaseParticipants,
)
from sources.kad_arbitr.use_cases.enrich_cases_for_participant import (
    EnrichKadArbitrCasesForParticipant,
)
from sources.kad_arbitr.use_cases.resolve_act_outcome import (
    ResolveKadArbitrActOutcome,
)
from sources.kad_arbitr.use_cases.resolve_case_acts import (
    ResolveKadArbitrCaseActs,
)
from sources.kad_arbitr.use_cases.resolve_case_details import (
    ResolveKadArbitrCaseDetails,
)
from sources.kad_arbitr.use_cases.resolve_case_outcome import (
    ResolveKadArbitrCaseOutcome,
)
from sources.kad_arbitr.use_cases.resolve_cases_for_participant import (
    ResolveKadArbitrCasesForParticipant,
)


@dataclass(slots=True)
class KadArbitrHouseCheckResult:
    """Результат проверки kad.arbitr.ru для дома."""

    participant_used: str | None
    facts: KadArbitrFacts | None
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
                facts=None,
                signals=[
                    _build_status_signal('kad_arbitr_participant_not_found')
                ],
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
                facts=None,
                signals=[
                    _build_status_signal('kad_arbitr_participant_not_found')
                ],
                status='participant_not_found',
            )

        search_uc = ResolveKadArbitrCasesForParticipant(
            client=self.kad_arbitr_client,
            base_url=self.base_url,
        )
        details_uc = ResolveKadArbitrCaseDetails(
            client=self.kad_arbitr_client,
            base_url=self.base_url,
        )
        participants_uc = EnrichKadArbitrCaseParticipants(
            details_uc=details_uc,
        )
        acts_uc = ResolveKadArbitrCaseActs(
            client=self.kad_arbitr_client,
            base_url=self.base_url,
        )
        text_extractor = CompositePdfTextExtractor(
            primary=PyPdfTextExtractor(),
            fallback=PdfMinerTextExtractor(),
        )
        pdf_fetcher = HttpPdfFetcher()
        act_outcome_uc = ResolveKadArbitrActOutcome(
            fetcher=pdf_fetcher,
            text_extractor=text_extractor,
        )
        case_outcome_uc = ResolveKadArbitrCaseOutcome(
            acts_uc=acts_uc,
            act_outcome_uc=act_outcome_uc,
        )
        resolver = EnrichKadArbitrCasesForParticipant(
            search_uc=search_uc,
            details_uc=participants_uc,
            case_outcome_uc=case_outcome_uc,
            base_url=self.base_url,
        )
        try:
            result = await resolver.execute(
                participant=participant,
                max_pages=max_pages,
            )
        except KadArbitrBlockedError:
            facts = KadArbitrFacts(
                status='blocked',
                participant=participant,
                participant_type=None,
                cases=[],
                stats={},
                reason='blocked',
            )
            return KadArbitrHouseCheckResult(
                participant_used=participant,
                facts=facts,
                signals=build_kad_arbitr_signals_from_facts(facts=facts),
                status='blocked',
            )

        except KadArbitrClientError:
            facts = KadArbitrFacts(
                status='error',
                participant=participant,
                participant_type=None,
                cases=[],
                stats={},
                reason='error',
            )
            return KadArbitrHouseCheckResult(
                participant_used=participant,
                facts=facts,
                signals=build_kad_arbitr_signals_from_facts(facts=facts),
                status='error',
            )
        finally:
            await pdf_fetcher.close()

        facts = result.facts
        if facts.status != 'ok':
            return KadArbitrHouseCheckResult(
                participant_used=participant,
                facts=facts,
                signals=build_kad_arbitr_signals_from_facts(facts=facts),
                status=facts.status,
            )
        return KadArbitrHouseCheckResult(
            participant_used=participant,
            facts=facts,
            signals=build_kad_arbitr_signals_from_facts(facts=facts),
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


def _build_status_signal(code: str) -> RiskSignal:
    """Собрать сигнал состояния источника."""

    definition = get_signal_definition(code)
    return RiskSignal(
        {
            'code': definition.code,
            'title': definition.title,
            'description': definition.description,
            'severity': int(definition.severity),
            'evidence_refs': [],
            'details': {
                'source': 'kad_arbitr',
                'status': code.replace('kad_arbitr_', ''),
            },
        }
    )
