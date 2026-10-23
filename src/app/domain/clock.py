from collections.abc import Callable
from datetime import UTC, datetime

from app.domain.exceptions.base import InvalidDomainTimestampError

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """текущее время в таймзоне utc"""
    return datetime.now(UTC)


def ensure_utc(dt: datetime | None = None) -> datetime:
    """нормализация времени к utc с валидацией таймзоны"""
    if dt is None:
        return utc_now()
    if dt.utcoffset() is None:
        raise InvalidDomainTimestampError()
    return dt.astimezone(UTC)
