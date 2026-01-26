"""Проверка выбора финального акта."""

from datetime import date

from sources.kad_arbitr.acts_selector import select_final_act
from sources.kad_arbitr.models import KadArbitrJudicialActNormalized


def test_selector_prefers_appeal() -> None:
    acts = [
        KadArbitrJudicialActNormalized(
            act_id='first',
            act_type='decision',
            act_type_raw='Решение',
            act_date=date(2026, 1, 10),
        ),
        KadArbitrJudicialActNormalized(
            act_id='appeal',
            act_type='resolution',
            act_type_raw='Постановление апелляции',
            act_date=date(2026, 2, 1),
        ),
    ]

    selected = select_final_act(acts=acts)

    assert selected is not None
    assert selected.act_id == 'appeal'


def test_selector_skips_technical_act() -> None:
    acts = [
        KadArbitrJudicialActNormalized(
            act_id='tech',
            act_type='resolution',
            act_type_raw='Постановление апелляции',
            title='Оставить без движения',
        ),
        KadArbitrJudicialActNormalized(
            act_id='decision',
            act_type='decision',
            act_type_raw='Решение',
            act_date=date(2026, 1, 10),
        ),
    ]

    selected = select_final_act(acts=acts)

    assert selected is not None
    assert selected.act_id == 'decision'


def test_selector_picks_cassation_with_final_marker() -> None:
    acts = [
        KadArbitrJudicialActNormalized(
            act_id='acceptance',
            act_type='determination',
            act_type_raw='Определение о принятии',
        ),
        KadArbitrJudicialActNormalized(
            act_id='cassation',
            act_type='resolution',
            act_type_raw='Постановление кассации',
            title='Оставить без изменения',
        ),
    ]

    selected = select_final_act(acts=acts)

    assert selected is not None
    assert selected.act_id == 'cassation'


def test_selector_prefers_marker_over_missing_dates() -> None:
    acts = [
        KadArbitrJudicialActNormalized(
            act_id='decision',
            act_type='decision',
            act_type_raw='Решение',
        ),
        KadArbitrJudicialActNormalized(
            act_id='appeal',
            act_type='resolution',
            act_type_raw='Постановление апелляции',
            title='Отменить решение',
        ),
    ]

    selected = select_final_act(acts=acts)

    assert selected is not None
    assert selected.act_id == 'appeal'
