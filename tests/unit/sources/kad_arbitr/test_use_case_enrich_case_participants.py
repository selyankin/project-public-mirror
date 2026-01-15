"""Проверка use-case обогащения участников."""

import pytest

from sources.kad_arbitr.stub_client import StubKadArbitrClient
from sources.kad_arbitr.use_cases.enrich_case_participants import (
    EnrichKadArbitrCaseParticipants,
)
from sources.kad_arbitr.use_cases.resolve_case_details import (
    ResolveKadArbitrCaseDetails,
)

pytestmark = pytest.mark.asyncio


def _build_html() -> str:
    return (
        '<html><body>'
        '<div>Истец: ООО Ромашка ИНН 7701234567</div>'
        '<div>Ответчик: ООО Лютик ИНН 7712345678</div>'
        '</body></html>'
    )


async def test_enrich_case_participants_marks_by_inn() -> None:
    client = StubKadArbitrClient(
        case_cards_by_id={'case-1': _build_html()},
    )
    details_uc = ResolveKadArbitrCaseDetails(client=client)
    use_case = EnrichKadArbitrCaseParticipants(details_uc=details_uc)

    result = await use_case.execute(
        case_id='case-1',
        target_participant='7701234567',
    )

    assert result.participants[0].is_target_participant
    assert not result.participants[1].is_target_participant


async def test_enrich_case_participants_marks_by_name() -> None:
    client = StubKadArbitrClient(
        case_cards_by_id={'case-1': _build_html()},
    )
    details_uc = ResolveKadArbitrCaseDetails(client=client)
    use_case = EnrichKadArbitrCaseParticipants(details_uc=details_uc)

    result = await use_case.execute(
        case_id='case-1',
        target_participant='ООО Ромашка',
    )

    assert result.participants[0].is_target_participant
    assert not result.participants[1].is_target_participant


async def test_enrich_case_participants_no_match() -> None:
    client = StubKadArbitrClient(
        case_cards_by_id={'case-1': _build_html()},
    )
    details_uc = ResolveKadArbitrCaseDetails(client=client)
    use_case = EnrichKadArbitrCaseParticipants(details_uc=details_uc)

    result = await use_case.execute(
        case_id='case-1',
        target_participant='ООО Неизвестно',
    )

    assert not result.participants[0].is_target_participant
    assert not result.participants[1].is_target_participant
