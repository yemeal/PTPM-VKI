import uuid

from app.application.commands.base import BaseCommand
from app.application.dtos import CommentDTO


class AddCommentCommand(BaseCommand[CommentDTO]):
    """команда добавления комментария"""

    author: str
    text: str
    source_url: str = ""
    external_id: int | str | None = None
    id: uuid.UUID | None = None
