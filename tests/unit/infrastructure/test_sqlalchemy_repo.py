import uuid
from datetime import datetime, timedelta

import pytest

from app.application.pagination import PaginationParams
from app.domain.aggregates.comment import Comment
from app.domain.exceptions.comments import (
    CommentAlreadyExistsError,
    ConcurrencyError,
)
from app.infrastructure.repositories.sqlalchemy_comment_repo import (
    SqlAlchemyCommentRepository,
)


async def test_repo_add_and_get_by_id(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    comment_id = uuid.uuid4()
    comment = Comment.create(
        id=comment_id,
        source_url="https://forum.example.com/topic/1",
        external_id=101,
        author="alice",
        text="Test message",
        created_at=now,
    )
    await repo.add(comment)

    fetched = await repo.get_by_id(comment_id)
    assert fetched is not None
    assert fetched.id == comment_id
    assert fetched.source_url == "https://forum.example.com/topic/1"
    assert fetched.external_id == 101
    assert fetched.author.value == "alice"
    assert fetched.text.value == "Test message"
    assert fetched.created_at == now
    assert fetched.version == 1
    assert fetched.updated_at is None


async def test_repo_exists_by_id(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    comment_id = uuid.uuid4()
    assert await repo.exists_by_id(comment_id) is False

    comment = Comment.create(
        id=comment_id,
        source_url="https://forum.example.com/topic/1",
        external_id=101,
        author="alice",
        text="Test message",
        created_at=now,
    )
    await repo.add(comment)
    assert await repo.exists_by_id(comment_id) is True


async def test_repo_get_by_id_not_found(
    repo: SqlAlchemyCommentRepository,
) -> None:
    fetched = await repo.get_by_id(uuid.uuid4())
    assert fetched is None


async def test_repo_find_by_source_and_external_id(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    comment = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=505,
        author="alice",
        text="Unique post",
        created_at=now,
    )
    await repo.add(comment)

    found = await repo.find_by_source_and_external_id(
        "https://forum.example.com/topic/1", 505
    )
    assert found is not None
    assert found.id == comment.id

    not_found = await repo.find_by_source_and_external_id(
        "https://forum.example.com/topic/1", 999
    )
    assert not_found is None


async def test_repo_unique_constraint_source_external_id(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    c1 = Comment.create(
        source_url="https://4pda.to/topic/1",
        external_id=101,
        author="user1",
        text="Text 1",
        created_at=now,
    )
    c2 = Comment.create(
        source_url="https://4pda.to/topic/1",
        external_id=101,
        author="user2",
        text="Text 2",
        created_at=now,
    )
    await repo.add(c1)
    with pytest.raises(CommentAlreadyExistsError):
        await repo.add(c2)


async def test_repo_same_external_id_different_sources(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    c1 = Comment.create(
        source_url="https://4pda.to/topic/1",
        external_id=101,
        author="user1",
        text="Text 1",
        created_at=now,
    )
    c2 = Comment.create(
        source_url="https://habr.com/post/2",
        external_id=101,
        author="user2",
        text="Text 2",
        created_at=now,
    )
    await repo.add(c1)
    await repo.add(c2)

    found1 = await repo.find_by_source_and_external_id(
        "https://4pda.to/topic/1", 101
    )
    found2 = await repo.find_by_source_and_external_id(
        "https://habr.com/post/2", 101
    )
    assert found1 is not None and found2 is not None
    assert found1.id != found2.id


async def test_repo_get_by_author(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    c1 = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=1,
        author="author_1",
        text="Msg 1",
        created_at=now,
    )
    c2 = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=2,
        author="author_2",
        text="Msg 2",
        created_at=now + timedelta(seconds=1),
    )
    c3 = Comment.create(
        source_url="https://forum.example.com/topic/2",
        external_id=3,
        author="author_1",
        text="Msg 3",
        created_at=now + timedelta(seconds=2),
    )
    await repo.add(c1)
    await repo.add(c2)
    await repo.add(c3)

    results = await repo.get_by_author("author_1")
    assert len(results) == 2
    assert [c.id for c in results] == [c1.id, c3.id]

    empty_results = await repo.get_by_author("non_existent")
    assert empty_results == []


async def test_repo_update(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    comment = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original text",
        created_at=now,
    )
    await repo.add(comment)

    later = now + timedelta(minutes=10)
    comment.edit_text("Updated text", now=later)
    await repo.update(comment)

    fetched = await repo.get_by_id(comment.id)
    assert fetched is not None
    assert fetched.text.value == "Updated text"
    assert fetched.updated_at == later
    assert fetched.version == 2


async def test_repo_delete(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    comment = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=1,
        author="alice",
        text="To delete",
        created_at=now,
    )
    await repo.add(comment)

    deleted = await repo.delete(comment.id)
    assert deleted is True

    fetched = await repo.get_by_id(comment.id)
    assert fetched is None

    deleted_again = await repo.delete(comment.id)
    assert deleted_again is False


async def test_repo_multiple_none_external_ids_allowed(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    c1 = Comment.create(
        source_url="https://forum.example.com/topic/1",
        author="alice",
        text="User manual post 1",
        external_id=None,
        created_at=now,
    )
    c2 = Comment.create(
        source_url="https://forum.example.com/topic/1",
        author="bob",
        text="User manual post 2",
        external_id=None,
        created_at=now,
    )
    await repo.add(c1)
    await repo.add(c2)

    found1 = await repo.get_by_id(c1.id)
    found2 = await repo.get_by_id(c2.id)
    assert found1 is not None and found2 is not None
    assert found1.external_id is None
    assert found2.external_id is None


async def test_repo_update_concurrency_error(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    comment = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=1,
        author="alice",
        text="Original text",
        created_at=now,
    )
    await repo.add(comment)

    later = now + timedelta(minutes=10)
    comment.edit_text("Updated text", now=later)
    # передача несовпадающей ожидаемой версии
    with pytest.raises(ConcurrencyError):
        await repo.update(comment, expected_version=99)


async def test_repo_find_by_source_and_external_ids(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    c1 = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=10,
        author="alice",
        text="Msg 10",
        created_at=now,
    )
    c2 = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=20,
        author="bob",
        text="Msg 20",
        created_at=now,
    )
    c3 = Comment.create(
        source_url="https://forum.example.com/topic/2",
        external_id=30,
        author="charlie",
        text="Msg 30",
        created_at=now,
    )
    await repo.add(c1)
    await repo.add(c2)
    await repo.add(c3)

    found = await repo.find_by_source_and_external_ids(
        "https://forum.example.com/topic/1", [10, 20, 999]
    )
    assert set(found.keys()) == {10, 20}
    assert found[10].id == c1.id
    assert found[20].id == c2.id


async def test_repo_get_paginated(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    for i in range(5):
        await repo.add(
            Comment.create(
                source_url="https://forum.example.com/topic/1",
                external_id=i + 1,
                author="alice" if i % 2 == 0 else "bob",
                text=f"Msg {i}",
                created_at=now + timedelta(seconds=i),
            )
        )

    # 1. первая страница (limit=2, offset=0)
    p1 = await repo.get_paginated(
        pagination=PaginationParams(limit=2, offset=0),
        source_url="https://forum.example.com/topic/1",
    )
    assert p1.total == 5
    assert len(p1.items) == 2
    assert p1.items[0].text.value == "Msg 0"
    assert p1.items[1].text.value == "Msg 1"

    # 2. вторая страница (limit=2, offset=2)
    p2 = await repo.get_paginated(
        pagination=PaginationParams(limit=2, offset=2),
        source_url="https://forum.example.com/topic/1",
    )
    assert p2.total == 5
    assert len(p2.items) == 2
    assert p2.items[0].text.value == "Msg 2"
    assert p2.items[1].text.value == "Msg 3"

    # 3. фильтрация по автору
    p_author = await repo.get_paginated(
        pagination=PaginationParams(limit=10, offset=0),
        author="alice",
    )
    assert p_author.total == 3
    assert all(c.author.value == "alice" for c in p_author.items)

    # 4. комбинированная фильтрация по автору и источнику
    p_both = await repo.get_paginated(
        pagination=PaginationParams(limit=10, offset=0),
        author="alice",
        source_url="https://forum.example.com/topic/1",
    )
    assert p_both.total == 3
    assert len(p_both.items) == 3


async def test_repo_get_by_source_url(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    url1 = "https://forum.example.com/topic/1"
    url2 = "https://forum.example.com/topic/2"
    c1 = Comment.create(
        source_url=url1,
        external_id=1,
        author="alice",
        text="T1",
        created_at=now,
    )
    c2 = Comment.create(
        source_url=url1,
        external_id=2,
        author="bob",
        text="T2",
        created_at=now + timedelta(seconds=1),
    )
    c3 = Comment.create(
        source_url=url2,
        external_id=3,
        author="charlie",
        text="T3",
        created_at=now + timedelta(seconds=2),
    )
    await repo.add(c1)
    await repo.add(c2)
    await repo.add(c3)

    results = await repo.get_by_source_url(url1)
    assert len(results) == 2
    assert [c.id for c in results] == [c1.id, c2.id]

    empty = await repo.get_by_source_url("https://nonexistent.com")
    assert empty == []


async def test_repo_get_by_id_for_update(
    repo: SqlAlchemyCommentRepository, now: datetime
) -> None:
    comment = Comment.create(
        source_url="https://forum.example.com/topic/1",
        external_id=1,
        author="alice",
        text="For update test",
        created_at=now,
    )
    await repo.add(comment)

    fetched = await repo.get_by_id(comment.id, for_update=True)
    assert fetched is not None
    assert fetched.id == comment.id


async def test_repo_find_by_source_and_external_ids_empty(
    repo: SqlAlchemyCommentRepository,
) -> None:
    res = await repo.find_by_source_and_external_ids(
        "https://example.com/topic", []
    )
    assert res == {}


def test_mapper_handles_integer_external_id(now: datetime) -> None:
    from app.infrastructure.db.mappers import CommentMapper
    from app.infrastructure.db.models import CommentModel

    model = CommentModel(
        id=uuid.uuid4(),
        source_url="https://example.com",
        external_id=12345,  # int directly from SQLite column
        author="user",
        text="text",
        created_at=now,
        version=1,
    )
    domain = CommentMapper.to_domain(model)
    assert domain.external_id == 12345
