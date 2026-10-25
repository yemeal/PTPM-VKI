from app.application.dtos import CommentDTO
from app.application.pagination import PaginatedResult
from app.application.ports.comment_repository import CommentRepositoryProtocol
from app.application.queries.comments.list.query import GetCommentsQuery


class GetCommentsQueryHandler:
    """обработчик запроса списка комментариев с фильтрацией и пагинацией"""

    def __init__(self, comments: CommentRepositoryProtocol) -> None:
        self._comments = comments

    async def __call__(
        self, query: GetCommentsQuery
    ) -> PaginatedResult[CommentDTO]:
        result = await self._comments.get_paginated(
            pagination=query.pagination,
            author=query.author,
            source_url=query.source_url,
        )
        return PaginatedResult[CommentDTO](
            items=[CommentDTO.from_domain(c) for c in result.items],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )
