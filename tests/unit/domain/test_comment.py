import uuid
from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domain.aggregates.comment import Comment
from app.domain.exceptions.comments import InvalidMessageTextError
from app.domain.value_objects.message_text import MessageText
from app.domain.value_objects.username import Username


def test_comment_create_and_properties(now: datetime) -> None:
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=42,
        author="alice",
        text="Hello world!",
        created_at=now,
    )

    assert isinstance(comment.id, uuid.UUID)
    assert comment.source_url == "https://example.com/topic/1"
    assert comment.external_id == 42
    assert comment.author == Username.from_str("alice")
    assert comment.text == MessageText.from_str("Hello world!")
    assert comment.created_at == now
    assert comment.updated_at is None
    assert comment.version == 1


def test_comment_create_with_explicit_uuid(now: datetime) -> None:
    custom_id = uuid.uuid4()
    comment = Comment.create(
        id=custom_id,
        source_url="https://example.com/topic/1",
        external_id=42,
        author="alice",
        text="Hello world!",
        created_at=now,
    )
    assert comment.id == custom_id


def test_comment_create_with_none_external_id(now: datetime) -> None:
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        author="alice",
        text="Hello world!",
        created_at=now,
    )
    assert comment.external_id is None


def test_comment_edit_text_success(now: datetime) -> None:
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original text",
        created_at=now,
    )
    later = now + timedelta(minutes=1)

    changed = comment.edit_text("New edited text", now=later)

    assert changed is True
    assert comment.text.value == "New edited text"
    assert comment.updated_at == later
    assert comment.version == 2


def test_comment_edit_text_noop(now: datetime) -> None:
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original text",
        created_at=now,
    )
    later = now + timedelta(minutes=1)

    changed = comment.edit_text("Original text", now=later)

    assert changed is False
    assert comment.text.value == "Original text"
    assert comment.updated_at is None
    assert comment.version == 1


def test_comment_edit_text_invalid_rollback(now: datetime) -> None:
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original text",
        created_at=now,
    )
    later = now + timedelta(minutes=1)

    with pytest.raises(InvalidMessageTextError):
        comment.edit_text("   ", now=later)

    assert comment.text.value == "Original text"
    assert comment.updated_at is None
    assert comment.version == 1


def test_comment_immutability(now: datetime) -> None:
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original text",
        created_at=now,
    )

    id_attr = "id"
    with pytest.raises(ValidationError):
        setattr(comment, id_attr, uuid.uuid4())

    author_attr = "author"
    with pytest.raises(ValidationError):
        setattr(comment, author_attr, Username.from_str("bob"))
