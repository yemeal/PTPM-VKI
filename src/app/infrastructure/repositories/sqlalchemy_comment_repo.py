import uuid

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.pagination import PaginatedResult, PaginationParams
from app.domain.aggregates.comment import Comment
from app.domain.exceptions.comments import (
    CommentAlreadyExistsError,
    ConcurrencyError,
)
from app.infrastructure.db.mappers import CommentMapper
from app.infrastructure.db.models import CommentModel


class SqlAlchemyCommentRepository:
    """репозиторий комментариев на sqlalchemy asyncsession"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, comment: Comment) -> None:
        model = CommentMapper.to_model(comment)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as err:
            raise CommentAlreadyExistsError() from err

    async def update(
        self, comment: Comment, expected_version: int | None = None
    ) -> None:
        target_version = (
            expected_version
            if expected_version is not None
            else comment.version - 1
        )
        stmt = (
            update(CommentModel)
            .where(
                CommentModel.id == comment.id,
                CommentModel.version == target_version,
            )
            .values(
                author=comment.author.value,
                text=comment.text.value,
                source_url=comment.source_url,
                external_id=(
                    str(comment.external_id)
                    if comment.external_id is not None
                    else None
                ),
                updated_at=comment.updated_at,
                version=comment.version,
            )
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        if isinstance(result, CursorResult) and result.rowcount == 0:
            raise ConcurrencyError()

    async def get_by_id(
        self, comment_id: uuid.UUID, for_update: bool = False
    ) -> Comment | None:
        stmt = select(CommentModel).where(CommentModel.id == comment_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CommentMapper.to_domain(model) if model is not None else None

    async def exists_by_id(self, comment_id: uuid.UUID) -> bool:
        stmt = select(CommentModel.id).where(CommentModel.id == comment_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def find_by_source_and_external_id(
        self, source_url: str, external_id: int | str
    ) -> Comment | None:
        stmt = select(CommentModel).where(
            CommentModel.source_url == source_url,
            CommentModel.external_id == str(external_id),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CommentMapper.to_domain(model) if model is not None else None

    async def find_by_source_and_external_ids(
        self, source_url: str, external_ids: list[int | str]
    ) -> dict[int | str, Comment]:
        if not external_ids:
            return {}
        str_ids = [str(eid) for eid in external_ids]
        stmt = select(CommentModel).where(
            CommentModel.source_url == source_url,
            CommentModel.external_id.in_(str_ids),
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        res: dict[int | str, Comment] = {}
        for m in models:
            domain_comment = CommentMapper.to_domain(m)
            if domain_comment.external_id is not None:
                res[domain_comment.external_id] = domain_comment
        return res

    async def get_by_author(self, author: str) -> list[Comment]:
        stmt = (
            select(CommentModel)
            .where(CommentModel.author == author)
            .order_by(CommentModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [CommentMapper.to_domain(m) for m in models]

    async def get_by_source_url(self, source_url: str) -> list[Comment]:
        stmt = (
            select(CommentModel)
            .where(CommentModel.source_url == source_url)
            .order_by(CommentModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [CommentMapper.to_domain(m) for m in models]

    async def get_paginated(
        self,
        pagination: PaginationParams,
        author: str | None = None,
        source_url: str | None = None,
    ) -> PaginatedResult[Comment]:
        conditions = []
        if author is not None:
            conditions.append(CommentModel.author == author)
        if source_url is not None:
            conditions.append(CommentModel.source_url == source_url)

        count_stmt = select(func.count()).select_from(CommentModel)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_res = await self._session.execute(count_stmt)
        total = count_res.scalar_one()

        data_stmt = select(CommentModel)
        if conditions:
            data_stmt = data_stmt.where(and_(*conditions))
        data_stmt = (
            data_stmt.order_by(CommentModel.created_at.asc())
            .limit(pagination.limit)
            .offset(pagination.offset)
        )
        result = await self._session.execute(data_stmt)
        models = result.scalars().all()
        items = [CommentMapper.to_domain(m) for m in models]

        return PaginatedResult(
            items=items,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        )

    async def delete(self, comment_id: uuid.UUID) -> bool:
        stmt = delete(CommentModel).where(CommentModel.id == comment_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        if isinstance(result, CursorResult):
            return result.rowcount > 0
        return False
