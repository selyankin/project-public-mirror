"""Выбор финального судебного акта kad.arbitr.ru."""

from __future__ import annotations

from sources.kad_arbitr.models import KadArbitrJudicialActNormalized


def normalize_act_text(value: str | None) -> str:
    """Нормализовать текст акта."""

    if not value:
        return ''

    lowered = value.lower().replace('ё', 'е')
    return ' '.join(lowered.split())


def act_priority_group(act: KadArbitrJudicialActNormalized) -> int:
    """Вернуть приоритет группы акта."""

    text = _act_text(act)
    if any(marker in text for marker in ('кассац', 'апелляц', 'надзор')):
        return 10
    if 'постановлен' in text:
        return 20
    if 'решен' in text:
        return 30
    if 'определен' in text:
        return 40
    return 50


def act_is_technical(act: KadArbitrJudicialActNormalized) -> bool:
    """Определить технический акт."""

    text = _act_text(act)
    technical_markers = (
        'оставить без движения',
        'возвратить',
        'принять к производству',
        'назначить судебное заседание',
        'отложить',
        'перерыв',
        'вызвать',
        'истребовать',
    )
    return any(marker in text for marker in technical_markers)


def act_contains_final_markers(act: KadArbitrJudicialActNormalized) -> bool:
    """Проверить наличие финальных маркеров."""

    text = _act_text(act)
    markers = (
        'оставить без изменения',
        'отменить',
        'изменить',
        'утвердить миров',
        'признать банкрот',
        'ввести конкурс',
        'ввести наблюден',
    )
    return any(marker in text for marker in markers)


def select_final_act(
    *,
    acts: list[KadArbitrJudicialActNormalized],
) -> KadArbitrJudicialActNormalized | None:
    """Выбрать финальный судебный акт."""

    if not acts:
        return None

    filtered = [act for act in acts if not act_is_technical(act)]
    candidates = filtered or acts

    scored = sorted(candidates, key=_act_score)
    return scored[0] if scored else None


def _act_text(act: KadArbitrJudicialActNormalized) -> str:
    return normalize_act_text(
        ' '.join(part for part in (act.act_type_raw, act.title) if part)
    )


def _act_score(
    act: KadArbitrJudicialActNormalized,
) -> tuple[int, int, int, int]:
    group_priority = act_priority_group(act)
    final_marker_bonus = 0 if act_contains_final_markers(act) else 1
    if act.act_date is None:
        date_score = 0
    else:
        date_score = -act.act_date.toordinal()

    if 'постановлен' in _act_text(act) or 'решен' in _act_text(act):
        type_bonus = 0
    elif 'определен' in _act_text(act):
        type_bonus = 1
    else:
        type_bonus = 2

    return (
        group_priority,
        final_marker_bonus,
        date_score,
        type_bonus,
    )
