import uuid

from app.application.commands.base import BaseCommand
from app.application.dtos import CommentDTO


class UpdateCommentCommand(BaseCommand[CommentDTO]):
    """команда обновления текста комментария"""

    id: uuid.UUID
    text: str
    expected_version: int
