import uuid
from collections.abc import Callable

import pytest

from app.application.pagination import PaginatedResult, PaginationParams
from app.domain.aggregates.comment import Comment
from app.domain.exceptions.comments import ConcurrencyError


class FakeCommentRepository:
    """in-memory фейк репозитория для изолированного тестирования юзкейсов"""

    def __init__(self) -> None:
        self.items: dict[uuid.UUID, Comment] = {}
        self.updated_count: int = 0

    async def add(self, comment: Comment) -> None:
        self.items[comment.id] = comment.model_copy(deep=True)

    async def get_by_id(
        self, comment_id: uuid.UUID, for_update: bool = False
    ) -> Comment | None:
        item = self.items.get(comment_id)
        return item.model_copy(deep=True) if item is not None else None

    async def exists_by_id(self, comment_id: uuid.UUID) -> bool:
        return comment_id in self.items

    async def find_by_source_and_external_id(
        self, source_url: str, external_id: int | str
    ) -> Comment | None:
        for c in self.items.values():
            if c.source_url == source_url and str(c.external_id) == str(
                external_id
            ):
                return c.model_copy(deep=True)
        return None

    async def find_by_source_and_external_ids(
        self, source_url: str, external_ids: list[int | str]
    ) -> dict[int | str, Comment]:
        if not external_ids:
            return {}
        str_ids = {str(eid) for eid in external_ids}
        res: dict[int | str, Comment] = {}
        for c in self.items.values():
            if (
                c.source_url == source_url
                and c.external_id is not None
                and str(c.external_id) in str_ids
            ):
                res[c.external_id] = c.model_copy(deep=True)
        return res

    async def get_by_author(self, author: str) -> list[Comment]:
        return [
            c.model_copy(deep=True)
            for c in self.items.values()
            if c.author.value == author
        ]

    async def get_by_source_url(self, source_url: str) -> list[Comment]:
        return [
            c.model_copy(deep=True)
            for c in self.items.values()
            if c.source_url == source_url
        ]

    async def get_paginated(
        self,
        pagination: PaginationParams,
        author: str | None = None,
        source_url: str | None = None,
    ) -> PaginatedResult[Comment]:
        filtered = [c.model_copy(deep=True) for c in self.items.values()]
        if author is not None:
            filtered = [c for c in filtered if c.author.value == author]
        if source_url is not None:
            filtered = [c for c in filtered if c.source_url == source_url]
        filtered.sort(key=lambda c: c.created_at)
        total = len(filtered)
        items = filtered[
            pagination.offset : pagination.offset + pagination.limit
        ]
        return PaginatedResult(
            items=items,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    async def update(
        self, comment: Comment, expected_version: int | None = None
    ) -> None:
        target = self.items.get(comment.id)
        if target is None:
            raise ConcurrencyError()
        exp = (
            expected_version
            if expected_version is not None
            else comment.version - 1
        )
        if target.version != exp:
            raise ConcurrencyError()
        self.items[comment.id] = comment.model_copy(deep=True)
        self.updated_count += 1

    async def delete(self, comment_id: uuid.UUID) -> bool:
        if comment_id in self.items:
            del self.items[comment_id]
            return True
        return False


class FakeForumParser:
    """фейковый парсер страниц форума для тестов слоя application"""

    def __init__(self, canned_comments: list[Comment] | None = None) -> None:
        self.canned_comments = canned_comments or []

    async def parse_page(
        self, url: str, visited_urls: set[str] | None = None
    ) -> list[Comment]:
        return self.canned_comments


@pytest.fixture
def fake_repo() -> FakeCommentRepository:
    return FakeCommentRepository()


@pytest.fixture
def repo(fake_repo: FakeCommentRepository) -> FakeCommentRepository:
    return fake_repo


@pytest.fixture
def fake_parser_factory() -> Callable[[list[Comment] | None], FakeForumParser]:
    def _factory(canned: list[Comment] | None = None) -> FakeForumParser:
        return FakeForumParser(canned_comments=canned)

    return _factory
