"""Проверка нормализации и сопоставления участников."""

from sources.kad_arbitr.models import (
    is_probably_same_participant,
    normalize_participant_name,
)


def test_normalize_participant_name_strips_legal_form() -> None:
    assert normalize_participant_name('ООО "Ромашка"') == 'ромашка'


def test_is_probably_same_participant_contains() -> None:
    assert is_probably_same_participant(
        target='ПАО СБЕРБАНК',
        candidate='Сбербанк',
    )
