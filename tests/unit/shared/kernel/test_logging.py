import logging

import pytest
from shared.kernel import logging as logging_module
from shared.kernel.settings import get_settings


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/flaffy')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
    monkeypatch.setenv('SERVICE_NAME', 'flaffy-service')
    get_settings.cache_clear()
    logging_module._configured = False
    yield
    get_settings.cache_clear()
    logging_module._configured = False
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    root.setLevel(logging.WARNING)


def test_setup_logging_configures_root_logger():
    logging_module.setup_logging()

    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1


def test_setup_logging_is_idempotent():
    logging_module.setup_logging()
    root = logging.getLogger()
    initial_handlers = list(root.handlers)

    logging_module.setup_logging()
    assert root.handlers == initial_handlers


def test_get_logger_without_name_returns_service_logger():
    logger = logging_module.get_logger()
    assert logger.name == 'flaffy-service'
