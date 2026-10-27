import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.domain.aggregates.comment import Comment
from app.domain.limits import MAX_MESSAGE_TEXT_LENGTH, MAX_USERNAME_LENGTH
from app.entrypoints.http.schemas import (
    AddCommentRequest,
    CommentResponse,
    ParsePageRequest,
    UpdateCommentRequest,
)


def test_add_comment_request_valid() -> None:
    req = AddCommentRequest(
        author="alice",
        text="Valid comment message",
        source_url="https://example.com/topic/1",
        external_id=123,
    )
    assert req.author == "alice"
    assert req.text == "Valid comment message"
    assert req.source_url == "https://example.com/topic/1"
    assert req.external_id == 123


def test_add_comment_request_defaults() -> None:
    req = AddCommentRequest(author="bob", text="Just text")
    assert req.source_url == ""
    assert req.external_id is None


def test_add_comment_request_rejects_empty_fields() -> None:
    with pytest.raises(ValidationError):
        AddCommentRequest(author="", text="Valid text")
    with pytest.raises(ValidationError):
        AddCommentRequest(author="alice", text="")


def test_add_comment_request_rejects_oversized_fields() -> None:
    too_long_author = "a" * (MAX_USERNAME_LENGTH + 1)
    with pytest.raises(ValidationError):
        AddCommentRequest(author=too_long_author, text="Valid text")

    too_long_text = "t" * (MAX_MESSAGE_TEXT_LENGTH + 1)
    with pytest.raises(ValidationError):
        AddCommentRequest(author="alice", text=too_long_text)


def test_add_comment_request_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        AddCommentRequest.model_validate(
            {"author": "alice", "text": "text", "unexpected": "field"}
        )


def test_update_comment_request_valid() -> None:
    req = UpdateCommentRequest(text="New text", expected_version=2)
    assert req.text == "New text"
    assert req.expected_version == 2


def test_update_comment_request_rejects_invalid_version() -> None:
    with pytest.raises(ValidationError):
        UpdateCommentRequest(text="New text", expected_version=0)
    with pytest.raises(ValidationError):
        UpdateCommentRequest(text="New text", expected_version=-1)


def test_update_comment_request_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        UpdateCommentRequest.model_validate(
            {"text": "text", "expected_version": 1, "extra": "data"}
        )


def test_parse_page_request_valid() -> None:
    req = ParsePageRequest(url="https://example.com/topic/10")
    assert str(req.url) == "https://example.com/topic/10"


def test_parse_page_request_rejects_invalid_url() -> None:
    with pytest.raises(ValidationError):
        ParsePageRequest(url="not_a_valid_url")
    with pytest.raises(ValidationError):
        ParsePageRequest(url="ftp://ftp.example.com")


def test_comment_response_from_domain(now: datetime) -> None:
    comment_id = uuid.uuid4()
    domain_comment = Comment.create(
        id=comment_id,
        source_url="https://example.com",
        external_id=99,
        author="alice",
        text="Domain comment",
        created_at=now,
    )
    resp = CommentResponse.from_domain(domain_comment)

    assert resp.id == comment_id
    assert resp.source_url == "https://example.com"
    assert resp.external_id == 99
    assert resp.author == "alice"
    assert resp.text == "Domain comment"
    assert resp.created_at == now
    assert resp.version == 1
