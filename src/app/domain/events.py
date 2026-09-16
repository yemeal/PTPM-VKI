from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class DomainEvent(BaseModel):
    """Базовый класс доменного события"""

    model_config = ConfigDict(frozen=True)

    occurred_at: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(UTC))
    ]


class UserRegisteredEvent(DomainEvent):
    """Событие успешной регистрации пользователя"""

    login: str
