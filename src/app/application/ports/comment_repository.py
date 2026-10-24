import uuid
from typing import Protocol

from app.application.pagination import PaginatedResult, PaginationParams
from app.domain.aggregates.comment import Comment


class CommentRepositoryProtocol(Protocol):
    """порт репозитория комментариев"""

    async def add(self, comment: Comment) -> None:
        """сохранение нового комментария"""
        ...

    async def get_by_id(
        self, comment_id: uuid.UUID, for_update: bool = False
    ) -> Comment | None:
        """получение комментария по идентификатору"""
        ...

    async def exists_by_id(self, comment_id: uuid.UUID) -> bool:
        """проверка существования комментария по идентификатору"""
        ...

    async def find_by_source_and_external_id(
        self, source_url: str, external_id: int | str
    ) -> Comment | None:
        """поиск комментария по url источника и внешнему id"""
        ...

    async def find_by_source_and_external_ids(
        self, source_url: str, external_ids: list[int | str]
    ) -> dict[int | str, Comment]:
        """пакетный поиск комментариев по url источника и списку внешних id"""
        ...

    async def get_by_author(self, author: str) -> list[Comment]:
        """список комментариев автора"""
        ...

    async def get_by_source_url(self, source_url: str) -> list[Comment]:
        """список комментариев по url источника"""
        ...

    async def get_paginated(
        self,
        pagination: PaginationParams,
        author: str | None = None,
        source_url: str | None = None,
    ) -> PaginatedResult[Comment]:
        """постраничный список комментариев с фильтрацией"""
        ...

    async def update(
        self, comment: Comment, expected_version: int | None = None
    ) -> None:
        """обновление комментария с контролем версии occ"""
        ...

    async def delete(self, comment_id: uuid.UUID) -> bool:
        """удаление комментария по идентификатору"""
        ...
