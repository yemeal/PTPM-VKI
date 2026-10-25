import uuid
from datetime import datetime

import pytest

from app.application.dtos import CommentDTO
from app.application.pagination import PaginationParams
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.application.queries.comments.get.handler import (
    GetCommentQueryHandler,
)
from app.application.queries.comments.get.query import GetCommentQuery
from app.application.queries.comments.list.handler import (
    GetCommentsQueryHandler,
)
from app.application.queries.comments.list.query import GetCommentsQuery
from app.domain.aggregates.comment import Comment
from app.domain.exceptions.comments import CommentNotFoundError


async def test_get_comment_query_success(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    handler = GetCommentQueryHandler(comments=repo)
    comment_id = uuid.uuid4()
    expected = Comment.create(
        id=comment_id,
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Hello",
        created_at=now,
    )
    await repo.add(expected)

    result = await handler(GetCommentQuery(id=comment_id))
    assert isinstance(result, CommentDTO)
    assert result == CommentDTO.from_domain(expected)


async def test_get_comment_query_not_found(
    repo: CommentRepositoryProtocol,
) -> None:
    handler = GetCommentQueryHandler(comments=repo)
    with pytest.raises(CommentNotFoundError):
        await handler(GetCommentQuery(id=uuid.uuid4()))


async def test_get_comments_query_with_filters_and_pagination(
    repo: CommentRepositoryProtocol, now: datetime
) -> None:
    handler = GetCommentsQueryHandler(comments=repo)
    c1 = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=1,
        author="alice",
        text="Post 1",
        created_at=now,
    )
    c2 = Comment.create(
        source_url="https://example.com/topic/1",
        external_id=2,
        author="bob",
        text="Post 2",
        created_at=now,
    )
    c3 = Comment.create(
        source_url="https://example.com/topic/2",
        external_id=3,
        author="alice",
        text="Post 3",
        created_at=now,
    )
    await repo.add(c1)
    await repo.add(c2)
    await repo.add(c3)

    # 1. фильтр по автору
    author_res = await handler(GetCommentsQuery(author="alice"))
    assert author_res.total == 2
    assert len(author_res.items) == 2
    assert all(isinstance(c, CommentDTO) for c in author_res.items)
    assert {c.id for c in author_res.items} == {c1.id, c3.id}

    # 2. фильтр по источнику
    source_res = await handler(
        GetCommentsQuery(source_url="https://example.com/topic/1")
    )
    assert source_res.total == 2
    assert {c.id for c in source_res.items} == {c1.id, c2.id}

    # 3. фильтр по автору и источнику
    both_res = await handler(
        GetCommentsQuery(
            author="alice", source_url="https://example.com/topic/1"
        )
    )
    assert both_res.total == 1
    assert both_res.items[0].id == c1.id

    # 4. пагинация limit и offset
    paged_res = await handler(
        GetCommentsQuery(pagination=PaginationParams(limit=1, offset=1))
    )
    assert paged_res.total == 3
    assert len(paged_res.items) == 1
    assert paged_res.limit == 1
    assert paged_res.offset == 1
