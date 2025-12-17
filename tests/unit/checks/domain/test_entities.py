from datetime import UTC, datetime, timedelta

import pytest
from checks.domain.entities.check import (
    Check,
    CheckId,
    CheckStatus,
    DomainValidationError,
    QueryType,
)


def make_check(**overrides) -> Check:
    now = datetime.now(UTC)
    data = {
        'query_type': QueryType.url,
        'raw_query': 'https://example.com',
        'status': CheckStatus.queued,
        'created_at': now,
        'updated_at': now,
        'user_id': None,
        'object_id': None,
        'job_id': None,
        'report_id': None,
        'error_code': None,
        'error_message': None,
    }
    data.update(overrides)
    return Check(data)


def test_check_id_generates_default_and_compares_by_value():
    first = CheckId()
    assert len(first.value) == 32
    same = CheckId(first.value)
    assert first == same
    assert hash(first) == hash(same)


def test_check_creation_requires_timezone_aware_datetimes():
    now = datetime.now(UTC)
    check = make_check(created_at=now, updated_at=now)
    assert check.created_at.tzinfo is not None


def test_naive_datetime_raises_error():
    naive = datetime.utcnow()
    with pytest.raises(DomainValidationError):
        make_check(created_at=naive)


def test_updated_before_created_raises_error():
    now = datetime.now(UTC)
    with pytest.raises(DomainValidationError):
        make_check(updated_at=now - timedelta(seconds=1))


def test_empty_raw_query_raises_error():
    with pytest.raises(DomainValidationError):
        make_check(raw_query='   ')


def test_failed_without_error_message_is_invalid():
    with pytest.raises(DomainValidationError):
        make_check(status=CheckStatus.failed, error_message=None)


def test_mark_failed_sets_status_and_requires_message():
    check = make_check()
    check.mark_failed('boom', code='ERR42')
    assert check.status is CheckStatus.failed
    assert check.error_message == 'boom'
    assert check.error_code == 'ERR42'
    with pytest.raises(DomainValidationError):
        check.mark_failed('   ')


def test_mark_ready_clears_error_state_and_sets_report_id():
    check = make_check()
    check.mark_failed('boom')
    check.mark_ready(report_id='rep-1')
    assert check.status is CheckStatus.ready
    assert check.error_message is None
    assert check.error_code is None
    assert check.report_id == 'rep-1'


def test_validate_query_type_limits_values():
    check = make_check(query_type=QueryType.url)
    check.validate_query_type()  # should not raise

    check_other = make_check(query_type=QueryType.developer)
    with pytest.raises(DomainValidationError):
        check_other.validate_query_type()
