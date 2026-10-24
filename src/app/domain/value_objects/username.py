from typing import Annotated, Any, Self

from pydantic import Field, field_validator

from app.domain.base import DomainModel
from app.domain.exceptions.comments import InvalidUsernameError
from app.domain.limits import MAX_USERNAME_LENGTH


class Username(DomainModel):
    """нормализованное имя автора комментария"""

    value: Annotated[
        str,
        Field(
            description=(
                f"Имя автора комментария (1-{MAX_USERNAME_LENGTH} символов)."
            ),
        ),
    ]

    @field_validator("value", mode="before")
    @classmethod
    def _normalize_and_validate(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise InvalidUsernameError()

        normalized = value.strip()
        if not normalized:
            raise InvalidUsernameError()

        if len(normalized) > MAX_USERNAME_LENGTH:
            raise InvalidUsernameError()

        return normalized

    @classmethod
    def from_str(cls, value: str) -> Self:
        """создание объекта имени автора из строки"""
        return cls(value=value)

    def __str__(self) -> str:
        return self.value

    def __len__(self) -> int:
        return len(self.value)

    def __repr__(self) -> str:
        return f"Username({self.value!r})"
