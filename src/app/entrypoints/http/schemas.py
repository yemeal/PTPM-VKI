import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.application.dtos import CommentDTO
from app.domain.aggregates.comment import Comment
from app.domain.limits import MAX_MESSAGE_TEXT_LENGTH, MAX_USERNAME_LENGTH


class ParsePageRequest(BaseModel):
    """схема запроса парсинга страницы форума"""

    model_config = ConfigDict(extra="forbid")

    url: Annotated[
        HttpUrl,
        Field(description="Валидный HTTP/HTTPS URL страницы форума"),
    ]


class AddCommentRequest(BaseModel):
    """схема запроса добавления комментария"""

    model_config = ConfigDict(extra="forbid")

    author: Annotated[
        str,
        Field(
            min_length=1,
            max_length=MAX_USERNAME_LENGTH,
            description="Имя автора",
        ),
    ]
    text: Annotated[
        str,
        Field(
            min_length=1,
            max_length=MAX_MESSAGE_TEXT_LENGTH,
            description="Текст комментария",
        ),
    ]
    source_url: Annotated[
        str,
        Field(
            default="",
            description="URL источника комментария",
        ),
    ]
    external_id: Annotated[
        int | str | None,
        Field(
            default=None,
            description="Внешний ID комментария (при отсутствии генерируется автоматически)",
        ),
    ]


class UpdateCommentRequest(BaseModel):
    """схема запроса обновления текста комментария"""

    model_config = ConfigDict(extra="forbid")

    text: Annotated[
        str,
        Field(
            min_length=1,
            max_length=MAX_MESSAGE_TEXT_LENGTH,
            description="Новый текст комментария",
        ),
    ]
    expected_version: Annotated[
        int,
        Field(
            ge=1,
            description="Ожидаемая версия комментария для OCC",
        ),
    ]


class CommentResponse(BaseModel):
    """схема ответа с данными комментария"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_url: str
    external_id: int | str | None = None
    author: str
    text: str
    created_at: datetime
    updated_at: datetime | None = None
    version: int

    @classmethod
    def from_dto(cls, dto: CommentDTO) -> Self:
        """создание схемы ответа из dto"""
        return cls(
            id=dto.id,
            source_url=dto.source_url,
            external_id=dto.external_id,
            author=dto.author,
            text=dto.text,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            version=dto.version,
        )

    @classmethod
    def from_domain(cls, comment: Comment) -> Self:
        """создание схемы ответа из доменной сущности"""
        return cls.from_dto(CommentDTO.from_domain(comment))


class PaginatedResponse[T](BaseModel):
    """схема ответа с пагинацией"""

    items: list[T]
    total: int
    limit: int
    offset: int


class ParsePageResponse(BaseModel):
    """схема ответа парсинга страницы форума"""

    total_parsed: int
    saved_count: int
    comments: list[CommentResponse]


class ErrorResponse(BaseModel):
    """схема ответа с описанием ошибки"""

    detail: str
