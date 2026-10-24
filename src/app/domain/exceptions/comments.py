from typing import ClassVar

from app.domain.exceptions.base import DomainError


class InvalidUsernameError(DomainError):
    """имя пользователя не соответствует доменным ограничениям"""

    default_message: ClassVar[str] = "Invalid username"


class InvalidMessageTextError(DomainError):
    """текст сообщения не соответствует доменным ограничениям"""

    default_message: ClassVar[str] = "Invalid message text"


class CommentNotFoundError(DomainError):
    """комментарий с указанным идентификатором не найден"""

    default_message: ClassVar[str] = "Comment not found"


class CommentAlreadyExistsError(DomainError):
    """комментарий с указанным идентификатором уже существует"""

    default_message: ClassVar[str] = "Comment already exists"


class ConcurrencyError(DomainError):
    """конфликт версий при оптимистической блокировке occ"""

    default_message: ClassVar[str] = (
        "Comment was modified by another transaction"
    )
