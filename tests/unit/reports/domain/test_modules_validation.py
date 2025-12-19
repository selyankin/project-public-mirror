"""Проверки валидации модулей отчёта."""

import pytest

from reports.domain.exceptions.report import (
    ReportInvalidModulesError,
    ReportModuleNotFoundError,
    ReportModulePaymentRequiredError,
)
from reports.domain.modules.catalog import DEFAULT_MODULES
from reports.domain.modules.validation import validate_modules


def test_validate_modules_unknown_module():
    with pytest.raises(ReportModuleNotFoundError):
        validate_modules(['unknown-module'])


def test_validate_modules_adds_dependencies():
    module_ids, specs = validate_modules(['risk_signals'])
    assert module_ids[0] == DEFAULT_MODULES[0]
    assert 'risk_signals' in module_ids
    assert specs[-1].id == 'risk_signals'


def test_validate_modules_paid_module_requires_payment():
    with pytest.raises(ReportModulePaymentRequiredError):
        validate_modules(['fias_normalization'])


def test_validate_modules_empty_list_invalid():
    with pytest.raises(ReportInvalidModulesError):
        validate_modules([])
