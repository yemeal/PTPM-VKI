import uuid

from app.application.dtos import CommentDTO
from app.application.queries.base import BaseQuery


class GetCommentQuery(BaseQuery[CommentDTO]):
    """запрос получения комментария по id"""

    id: uuid.UUID
