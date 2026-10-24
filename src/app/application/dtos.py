import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from app.domain.aggregates.comment import Comment


class CommentDTO(BaseModel):
    """dto комментария для передачи данных между слоями"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: uuid.UUID
    source_url: str
    external_id: int | str | None = None
    author: str
    text: str
    created_at: datetime
    updated_at: datetime | None = None
    version: int = 1

    @classmethod
    def from_domain(cls, comment: Comment) -> Self:
        """создание dto из доменной сущности комментария"""
        return cls(
            id=comment.id,
            source_url=comment.source_url,
            external_id=comment.external_id,
            author=comment.author.value,
            text=comment.text.value,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            version=comment.version,
        )
