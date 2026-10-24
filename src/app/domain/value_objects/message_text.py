import unicodedata
from typing import Annotated, Any, Self

from pydantic import Field, field_validator

from app.domain.base import DomainModel
from app.domain.exceptions.comments import InvalidMessageTextError
from app.domain.limits import MAX_MESSAGE_TEXT_LENGTH


class MessageText(DomainModel):
    """нормализованный текст комментария"""

    value: Annotated[
        str,
        Field(
            description=(
                f"Нормализованный текст комментария (1-{MAX_MESSAGE_TEXT_LENGTH} символов)."
            ),
        ),
    ]

    @field_validator("value", mode="before")
    @classmethod
    def _normalize_and_validate(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise InvalidMessageTextError()

        normalized = unicodedata.normalize("NFC", value)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        normalized = normalized.strip()

        if not normalized:
            raise InvalidMessageTextError()

        if len(normalized) > MAX_MESSAGE_TEXT_LENGTH:
            raise InvalidMessageTextError()

        return normalized

    @classmethod
    def from_str(cls, value: str) -> Self:
        """создание объекта текста сообщения из строки"""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)

    def __repr__(self) -> str:
        return f"MessageText({self.value!r})"
