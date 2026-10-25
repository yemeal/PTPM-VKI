import logging
import re
from datetime import datetime

from pydantic import ValidationError

from app.domain.aggregates.comment import Comment
from app.domain.exceptions.base import DomainError
from app.domain.limits import MAX_MESSAGE_TEXT_LENGTH

logger = logging.getLogger(__name__)

TRUNCATION_SUFFIX: str = "\n... [truncated]"


def clean_external_id(raw_id: object) -> int | str | None:
    """очистка и нормализация внешнего идентификатора сообщения"""
    if not raw_id:
        return None
    raw_str = str(raw_id).strip()
    cleaned = re.split(r"[?#]", raw_str)[-1]
    cleaned = re.split(r"/", cleaned)[-1]
    cleaned = re.sub(
        r"^(?:comment[-_]?|post[-_]?|msg[-_]?|entry[-_]?|p[-_]?|c[-_]?)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    if not cleaned:
        return None
    if cleaned.isdigit():
        val = int(cleaned)
        return val if val > 0 else None
    if re.match(r"^[A-Za-z0-9_-]+$", cleaned):
        return cleaned
    matches = re.findall(r"\d+", raw_str)
    if matches:
        val = int(matches[-1])
        return val if val > 0 else None
    return None


def truncate_message_text(text: str) -> str:
    """усечение текста сообщения по лимиту домена"""
    if len(text) > MAX_MESSAGE_TEXT_LENGTH:
        cutoff = MAX_MESSAGE_TEXT_LENGTH - len(TRUNCATION_SUFFIX)
        return text[:cutoff].rstrip() + TRUNCATION_SUFFIX
    return text


def build_comment(
    *,
    source_url: str,
    external_id: int | str,
    author: str,
    text: str,
    created_at: datetime,
) -> Comment | None:
    """безопасное создание агрегата комментария с доменной валидацией"""
    message_text = truncate_message_text(text)
    try:
        return Comment.create(
            source_url=source_url,
            external_id=external_id,
            author=author,
            text=message_text,
            created_at=created_at,
        )
    except (ValidationError, ValueError, DomainError) as err:
        logger.warning(
            "Skipping malformed comment on %s (external_id=%s): %s",
            source_url,
            external_id,
            err,
        )
        return None
