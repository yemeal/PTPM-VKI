import uuid
from datetime import datetime, timedelta

import pytest

from app.application.commands.comments.add.command import AddCommentCommand
from app.application.commands.comments.add.handler import AddCommentHandler
from app.application.commands.comments.delete.command import (
    DeleteCommentCommand,
)
from app.application.commands.comments.delete.handler import (
    DeleteCommentHandler,
)
from app.application.commands.comments.update.command import (
    UpdateCommentCommand,
)
from app.application.commands.comments.update.handler import (
    UpdateCommentHandler,
)
from app.application.commands.parse_page.command import ParsePageCommand
from app.application.commands.parse_page.handler import ParsePageHandler
from app.application.dtos import CommentDTO
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.domain.aggregates.comment import Comment
from app.domain.exceptions.comments import (
    CommentAlreadyExistsError,
    CommentNotFoundError,
    ConcurrencyError,
)


class FakeForumParser:
    """фейк парсера страниц форума"""

    def __init__(self, canned_comments: list[Comment] | None = None) -> None:
        self.canned_comments = canned_comments or []

    async def parse_page(
        self, url: str, visited_urls: set[str] | None = None
    ) -> list[Comment]:
        return self.canned_comments


async def test_add_comment_success(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    handler = AddCommentHandler(comments=repo, clock=lambda: now)
    custom_id = uuid.uuid4()
    command = AddCommentCommand(
        id=custom_id,
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Hello world!",
    )

    comment = await handler(command)

    assert isinstance(comment, CommentDTO)
    assert comment.id == custom_id
    assert comment.source_url == "https://example.com/topic/1"
    assert comment.external_id == 1
    assert comment.author == "alice"
    assert comment.text == "Hello world!"
    saved = await repo.get_by_id(custom_id)
    assert saved is not None
    assert saved.id == comment.id
    assert saved.author.value == comment.author
    assert saved.text.value == comment.text


async def test_add_comment_already_exists_by_id(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    handler = AddCommentHandler(comments=repo, clock=lambda: now)
    custom_id = uuid.uuid4()
    await repo.add(
        Comment.create(
            id=custom_id,
            source_url="https://example.com/topic/1",
            external_id=1,
            author="alice",
            text="Old",
            created_at=now,
        )
    )

    command = AddCommentCommand(
        id=custom_id,
        source_url="https://example.com/topic/2",
        external_id=2,
        author="alice",
        text="New text",
    )
    with pytest.raises(CommentAlreadyExistsError):
        await handler(command)


async def test_add_comment_already_exists_by_source_and_external_id(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    handler = AddCommentHandler(comments=repo, clock=lambda: now)
    await repo.add(
        Comment.create(
            source_url="https://example.com/topic/1",
            external_id=1,
            author="alice",
            text="Old",
            created_at=now,
        )
    )

    command = AddCommentCommand(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="bob",
        text="New text",
    )
    with pytest.raises(CommentAlreadyExistsError):
        await handler(command)


async def test_update_comment_success(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    later = now + timedelta(minutes=5)
    handler = UpdateCommentHandler(comments=repo, clock=lambda: later)
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original",
        created_at=now,
    )
    await repo.add(comment)

    updated = await handler(
        UpdateCommentCommand(
            id=comment.id, text="Edited text", expected_version=1
        )
    )

    assert isinstance(updated, CommentDTO)
    assert updated.text == "Edited text"
    assert updated.version == 2
    assert updated.updated_at == later


async def test_update_comment_noop(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    later = now + timedelta(minutes=5)
    handler = UpdateCommentHandler(comments=repo, clock=lambda: later)
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original",
        created_at=now,
    )
    await repo.add(comment)

    updated = await handler(
        UpdateCommentCommand(
            id=comment.id, text="Original", expected_version=1
        )
    )

    assert isinstance(updated, CommentDTO)
    assert updated.text == "Original"
    assert updated.version == 1


async def test_update_comment_not_found(
    repo: CommentRepositoryProtocol,
) -> None:
    handler = UpdateCommentHandler(comments=repo)
    with pytest.raises(CommentNotFoundError):
        await handler(
            UpdateCommentCommand(
                id=uuid.uuid4(), text="Text", expected_version=1
            )
        )


async def test_update_comment_concurrency_error(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    handler = UpdateCommentHandler(comments=repo, clock=lambda: now)
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original",
        created_at=now,
    )
    await repo.add(comment)

    with pytest.raises(ConcurrencyError):
        await handler(
            UpdateCommentCommand(
                id=comment.id, text="Edited", expected_version=99
            )
        )


async def test_delete_comment_success(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    handler = DeleteCommentHandler(comments=repo)
    comment = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Text",
        created_at=now,
    )
    await repo.add(comment)

    result = await handler(DeleteCommentCommand(id=comment.id))
    assert result is True
    assert (await repo.get_by_id(comment.id)) is None


async def test_delete_comment_not_found(
    repo: CommentRepositoryProtocol,
) -> None:
    handler = DeleteCommentHandler(comments=repo)
    with pytest.raises(CommentNotFoundError):
        await handler(DeleteCommentCommand(id=uuid.uuid4()))


async def test_parse_page_handler(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    later = now + timedelta(minutes=1)
    url = "https://example.com/topic/1"
    existing = Comment.create(
        source_url=url,
        external_id=1,
        author="alice",
        text="Old text",
        created_at=now,
    )
    await repo.add(existing)

    canned = [
        Comment.create(
            source_url=url,
            external_id=1,
            author="alice",
            text="New text",
            created_at=now,
        ),
        Comment.create(
            source_url=url,
            external_id=2,
            author="bob",
            text="Bob text",
            created_at=now,
        ),
    ]
    parser = FakeForumParser(canned_comments=canned)
    handler = ParsePageHandler(
        parser=parser, comments=repo, clock=lambda: later
    )

    result = await handler(ParsePageCommand(url=url))

    assert result.total_parsed == 2
    assert result.saved_count == 2
    assert len(result.comments) == 2
    assert all(isinstance(c, CommentDTO) for c in result.comments)

    stored1 = await repo.find_by_source_and_external_id(url, 1)
    assert stored1 is not None
    assert stored1.id == existing.id
    assert stored1.text.value == "New text"
    assert stored1.version == 2

    stored2 = await repo.find_by_source_and_external_id(url, 2)
    assert stored2 is not None
    assert stored2.text.value == "Bob text"
