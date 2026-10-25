from app.application.dtos import CommentDTO
from app.application.ports.comment_repository import CommentRepositoryProtocol
from app.application.queries.comments.get.query import GetCommentQuery
from app.domain.exceptions.comments import CommentNotFoundError


class GetCommentQueryHandler:
    """обработчик получения комментария по id"""

    def __init__(self, comments: CommentRepositoryProtocol) -> None:
        self._comments = comments

    async def __call__(self, query: GetCommentQuery) -> CommentDTO:
        comment = await self._comments.get_by_id(query.id)
        if comment is None:
            raise CommentNotFoundError()
        return CommentDTO.from_domain(comment)
