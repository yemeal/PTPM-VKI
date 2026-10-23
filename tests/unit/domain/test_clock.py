from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.domain.clock import ensure_utc, utc_now
from app.domain.exceptions.base import InvalidDomainTimestampError


def test_utc_now_returns_timezone_aware_utc_datetime() -> None:
    before = datetime.now(UTC)
    now = utc_now()
    after = datetime.now(UTC)

    assert isinstance(now, datetime)
    assert now.tzinfo is UTC
    assert before <= now <= after


def test_ensure_utc_defaults_to_now_when_none() -> None:
    before = datetime.now(UTC)
    res = ensure_utc(None)
    after = datetime.now(UTC)

    assert isinstance(res, datetime)
    assert res.tzinfo is UTC
    assert before <= res <= after


def test_ensure_utc_converts_timezone_aware_to_utc() -> None:
    custom_tz = timezone(timedelta(hours=3))
    dt = datetime(2026, 10, 26, 15, 30, tzinfo=custom_tz)
    res = ensure_utc(dt)

    assert res.tzinfo is UTC
    assert res == dt


def test_ensure_utc_rejects_naive_datetime() -> None:
    naive_dt = datetime(2026, 10, 26, 15, 30)
    with pytest.raises(InvalidDomainTimestampError):
        ensure_utc(naive_dt)
