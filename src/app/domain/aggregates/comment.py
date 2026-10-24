import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from app.domain.base import VersionedMutableEntity
from app.domain.clock import ensure_utc
from app.domain.value_objects.message_text import MessageText
from app.domain.value_objects.username import Username


class Comment(VersionedMutableEntity):
    """агрегат комментария к странице форума"""

    id: Annotated[
        uuid.UUID,
        Field(
            description="Уникальный суррогатный идентификатор комментария (UUID)",
        ),
    ]
    source_url: Annotated[
        str,
        Field(
            description="URL страницы источника комментария",
        ),
    ]
    external_id: Annotated[
        int | str | None,
        Field(
            default=None,
            description="Оригинальный идентификатор комментария на странице источника",
        ),
    ]
    author: Annotated[
        Username,
        Field(description="Автор комментария"),
    ]
    text: Annotated[
        MessageText,
        Field(description="Текст комментария"),
    ]

    @classmethod
    def create(
        cls,
        source_url: str,
        author: str | Username,
        text: str | MessageText,
        external_id: int | str | None = None,
        created_at: datetime | None = None,
        id: uuid.UUID | None = None,
    ) -> Self:
        """создание доменной сущности комментария"""
        comment_id = id if id is not None else uuid.uuid7()
        norm_ext_id = (
            int(external_id)
            if isinstance(external_id, str) and external_id.isdigit()
            else external_id
        )
        author_vo = (
            author
            if isinstance(author, Username)
            else Username.from_str(author)
        )
        text_vo = (
            text
            if isinstance(text, MessageText)
            else MessageText.from_str(text)
        )
        return cls(
            id=comment_id,
            source_url=source_url,
            external_id=norm_ext_id,
            author=author_vo,
            text=text_vo,
            created_at=ensure_utc(created_at),
        )

    def edit_text(self, new_text: str | MessageText, now: datetime) -> bool:
        """редактирование текста комментария с проверкой изменений"""
        text_vo = (
            new_text
            if isinstance(new_text, MessageText)
            else MessageText.from_str(new_text)
        )
        return self._apply_changes(now=now, text=text_vo)
