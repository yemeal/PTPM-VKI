from typing import Annotated

from fastapi import Depends, Request

from app.application.event_handlers.user_registered import (
    UserRegisteredNotificationHandler,
)
from app.application.ports.event_bus import IEventPublisher
from app.application.ports.notifier import INotificationService
from app.application.ports.repository import IUserRepository
from app.application.use_cases.register_user import RegisterUserUseCase
from app.domain.events import UserRegisteredEvent
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.infrastructure.notifiers.email_notifier import (
    EmailNotificationService,
)
from app.infrastructure.repositories.sqlite_user_repo import (
    SqliteUserRepository,
)

default_user_repo = SqliteUserRepository(":memory:")
default_notifier = EmailNotificationService()


def get_user_repository(request: Request) -> IUserRepository:
    """Получить репозиторий пользователей из состояния приложения."""
    return getattr(request.app.state, "user_repo", default_user_repo)


def get_notifier(request: Request) -> INotificationService:
    """Получить сервис уведомлений из состояния приложения."""
    return getattr(request.app.state, "notifier", default_notifier)


def get_event_bus(
    request: Request,
    notifier: Annotated[INotificationService, Depends(get_notifier)],
) -> IEventPublisher:
    """Получить или сконфигурировать шину событий с подписчиками."""
    if hasattr(request.app.state, "event_bus"):
        return request.app.state.event_bus

    bus = InMemoryEventBus()
    bus.subscribe(
        UserRegisteredEvent,
        UserRegisteredNotificationHandler(notification_service=notifier),
    )
    return bus


def get_register_use_case(
    repo: Annotated[IUserRepository, Depends(get_user_repository)],
    event_publisher: Annotated[IEventPublisher, Depends(get_event_bus)],
) -> RegisterUserUseCase:
    """Получить сценарий регистрации пользователя."""
    return RegisterUserUseCase(user_repo=repo, event_publisher=event_publisher)
