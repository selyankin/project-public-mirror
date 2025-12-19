"""Проверки сборки отчёта из модулей."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from reports.application.services.module_builders import (
    DEFAULT_MODULE_BUILDERS,
)
from reports.application.services.report_assembler import ReportAssembler


@pytest.mark.asyncio
async def test_report_assembler_builds_sections() -> None:
    """Модули добавляются в секции и заполняют данные."""

    assembler = ReportAssembler(DEFAULT_MODULE_BUILDERS)
    check_id = uuid4()
    check_payload = {
        'check_id': check_id,
        'kind': 'address',
        'raw_input': 'г. Москва, ул. Тверская, 1',
        'normalized_address': {
            'normalized': 'г. москва, ул. тверская, д. 1',
            'confidence': 'high',
            'source': 'stub',
            'tokens': ['г.', 'москва'],
        },
        'risk_card': {
            'score': 10,
            'level': 'low',
            'summary': 'низкий риск',
        },
        'signals': [
            {
                'code': 'address_confidence_low',
                'title': 'Низкая точность',
                'description': 'Описание',
                'severity': 1,
                'evidence_refs': [],
            }
        ],
        'created_at': datetime.now(UTC),
        'schema_version': 2,
        'fias': {'fias_id': 'moscow-001'},
    }
    modules = ['base_summary', 'risk_signals', 'fias_normalization']

    payload = await assembler.assemble(check_payload, modules)

    assert payload['meta']['check_id'] == check_id
    assert payload['meta']['schema_version'] == 1
    assert list(payload['meta']['modules']) == modules
    sections = payload['sections']
    assert set(sections.keys()) == set(modules)
    assert sections['fias_normalization']['fias'] == {'fias_id': 'moscow-001'}
    assert sections['risk_signals']['signals'][0]['code'] == (
        'address_confidence_low'
    )
