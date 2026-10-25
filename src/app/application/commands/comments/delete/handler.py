from app.application.commands.comments.delete.command import (
    DeleteCommentCommand,
)
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.domain.exceptions.comments import CommentNotFoundError


class DeleteCommentHandler:
    """обработчик удаления комментария"""

    def __init__(self, comments: CommentRepositoryProtocol) -> None:
        self._comments = comments

    async def __call__(self, command: DeleteCommentCommand) -> bool:
        deleted = await self._comments.delete(command.id)
        if not deleted:
            raise CommentNotFoundError()
        return True
