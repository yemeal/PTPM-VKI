from app.application.commands.comments.update.command import (
    UpdateCommentCommand,
)
from app.application.dtos import CommentDTO
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.domain.clock import Clock, utc_now
from app.domain.exceptions.comments import (
    CommentNotFoundError,
    ConcurrencyError,
)


class UpdateCommentHandler:
    """обработчик обновления комментария с контролем версий occ"""

    def __init__(
        self,
        comments: CommentRepositoryProtocol,
        clock: Clock = utc_now,
    ) -> None:
        self._comments = comments
        self._clock = clock

    async def __call__(self, command: UpdateCommentCommand) -> CommentDTO:
        comment = await self._comments.get_by_id(command.id)
        if comment is None:
            raise CommentNotFoundError()

        if comment.version != command.expected_version:
            raise ConcurrencyError()

        if comment.edit_text(command.text, now=self._clock()):
            await self._comments.update(
                comment, expected_version=command.expected_version
            )

        return CommentDTO.from_domain(comment)
