from app.application.commands.comments.add.command import AddCommentCommand
from app.application.dtos import CommentDTO
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.domain.aggregates.comment import Comment
from app.domain.clock import Clock, utc_now
from app.domain.exceptions.comments import CommentAlreadyExistsError


class AddCommentHandler:
    """обработчик добавления нового комментария"""

    def __init__(
        self,
        comments: CommentRepositoryProtocol,
        clock: Clock = utc_now,
    ) -> None:
        self._comments = comments
        self._clock = clock

    async def __call__(self, command: AddCommentCommand) -> CommentDTO:
        if command.id is not None:
            existing_by_id = await self._comments.get_by_id(command.id)
            if existing_by_id is not None:
                raise CommentAlreadyExistsError()

        if command.external_id is not None and command.source_url:
            existing_by_natural = (
                await self._comments.find_by_source_and_external_id(
                    command.source_url, command.external_id
                )
            )
            if existing_by_natural is not None:
                raise CommentAlreadyExistsError()

        comment = Comment.create(
            id=command.id,
            source_url=command.source_url,
            external_id=command.external_id,
            author=command.author,
            text=command.text,
            created_at=self._clock(),
        )
        await self._comments.add(comment)
        return CommentDTO.from_domain(comment)
