"""Проверка моделей kad.arbitr.ru."""

from sources.kad_arbitr.models import (
    KadArbitrSearchPayload,
    KadArbitrSideFilter,
)


def test_to_xhr_dict() -> None:
    payload = KadArbitrSearchPayload(
        page=2,
        count=50,
        sides=[
            KadArbitrSideFilter(
                name='ООО Ромашка',
                type=1,
                exact_match=True,
            ),
        ],
    )

    result = payload.to_xhr_dict()

    assert set(result.keys()) == {
        'Page',
        'Count',
        'Courts',
        'DateFrom',
        'DateTo',
        'CaseNumbers',
        'Sides',
    }
    assert result['Sides'] == [
        {'Name': 'ООО Ромашка', 'Type': 1, 'ExactMatch': True},
    ]
