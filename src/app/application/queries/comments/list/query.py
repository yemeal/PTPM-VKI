from pydantic import Field

from app.application.dtos import CommentDTO
from app.application.pagination import PaginatedResult, PaginationParams
from app.application.queries.base import BaseQuery


class GetCommentsQuery(BaseQuery[PaginatedResult[CommentDTO]]):
    """запрос списка комментариев с фильтрацией и пагинацией"""

    author: str | None = None
    source_url: str | None = None
    pagination: PaginationParams = Field(default_factory=PaginationParams)
