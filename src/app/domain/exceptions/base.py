from typing import ClassVar


class DomainError(Exception):
    """ожидаемое нарушение правила предметной области"""

    default_message: ClassVar[str] = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class InvalidDomainTimestampError(DomainError):
    """время домена требует явно заданного часового пояса"""

    default_message: ClassVar[str] = "Domain timestamp must be timezone-aware"


class EntityIdentityImmutableError(DomainError):
    """идентичность сущности и время создания неизменяемы"""

    default_message: ClassVar[str] = (
        "Entity identity and creation timestamp cannot be modified"
    )
