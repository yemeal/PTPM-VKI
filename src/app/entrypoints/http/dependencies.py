from typing import Annotated

from fastapi import Depends, Request

from app.application.ports.notifier import IExternalNotifier
from app.application.ports.repository import IUserRepository
from app.application.use_cases.register_user import RegisterUserUseCase
from app.infrastructure.notifiers.email_notifier import EmailNotifier
from app.infrastructure.repositories.sqlite_user_repo import (
    SqliteUserRepository,
)

default_user_repo = SqliteUserRepository(":memory:")
default_notifier = EmailNotifier()


def get_user_repository(request: Request) -> IUserRepository:
    """Получить репозиторий пользователей из состояния приложения."""
    return getattr(request.app.state, "user_repo", default_user_repo)


def get_notifier(request: Request) -> IExternalNotifier:
    """Получить сервис уведомлений из состояния приложения."""
    return getattr(request.app.state, "notifier", default_notifier)


def get_register_use_case(
    repo: Annotated[IUserRepository, Depends(get_user_repository)],
    notifier: Annotated[IExternalNotifier, Depends(get_notifier)],
) -> RegisterUserUseCase:
    """Получить сценарий регистрации пользователя."""
    return RegisterUserUseCase(user_repo=repo, notifier=notifier)
