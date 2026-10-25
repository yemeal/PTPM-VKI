import uuid

from app.application.commands.base import BaseCommand


class DeleteCommentCommand(BaseCommand[bool]):
    """команда удаления комментария по id"""

    id: uuid.UUID
