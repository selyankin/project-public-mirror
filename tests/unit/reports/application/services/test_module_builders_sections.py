"""Проверки отдельных модулей отчёта."""

import pytest

from reports.application.services.module_builders import (
    address_quality,
    base_summary,
    risk_signals,
)

pytestmark = pytest.mark.asyncio


async def test_base_summary_builds_highlights() -> None:
    """Резюме отражает риск и ключевые факты."""

    payload = {
        'kind': 'address',
        'raw_input': 'г. Москва, ул. Тверская, 1',
        'normalized_address': {
            'normalized': 'г. москва, ул. тверская, д. 1',
        },
        'risk_card': {'score': 85},
        'signals': [
            {'code': 'a', 'title': 'A'},
            {'code': 'b', 'title': 'B'},
        ],
        'fias': {'fias_id': 'uuid', 'normalized': '...'},
    }

    section = await base_summary.build(payload)

    assert section['risk_level'] == 'high'
    assert section['signals_count'] == 2
    assert any('сигналов' in item.lower() for item in section['highlights'])


async def test_address_quality_without_fias() -> None:
    """При отсутствии нормализации ставим оценку D."""

    payload = {
        'normalized_address': {},
        'fias': None,
    }

    section = await address_quality.build(payload)

    assert section['is_normalized'] is False
    assert section['quality_grade'] == 'D'
    assert 'Не удалось нормализовать адрес' in section['issues'][0]


async def test_address_quality_with_confidence() -> None:
    """При наличии уверенности grade зависит от порогов."""

    payload = {
        'normalized_address': {'confidence': 'high'},
        'fias': {'confidence': 0.8},
    }

    section = await address_quality.build(payload)

    assert section['is_normalized'] is True
    assert section['quality_grade'] == 'B'
    assert section['confidence'] == 0.8


async def test_risk_signals_builds_items() -> None:
    """Сигналы нормализуются в count/items."""

    payload = {
        'signals': [
            {
                'code': 'addr_low',
                'title': 'Low address quality',
                'severity': 'critical',
                'description': 'desc',
                'evidence_refs': ['a'],
            },
            {
                'code': 'info_code',
                'title': '',
                'severity': 10,
            },
        ],
    }

    section = await risk_signals.build(payload)

    assert section['count'] == 2
    assert section['items'][0]['severity'] == 'critical'
    assert 'evidence' in section['items'][0]
    assert section['items'][1]['title'] == 'info_code'
