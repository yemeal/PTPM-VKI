from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest

from app.application.event_handlers.user_registered import (
    UserRegisteredNotificationHandler,
)
from app.application.ports.notifier import INotificationService
from app.application.use_cases.register_user import RegisterUserUseCase
from app.domain.events import UserRegisteredEvent
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.infrastructure.repositories.sqlite_user_repo import (
    SqliteUserRepository,
)


@pytest.fixture
def sqlite_repo() -> Generator[SqliteUserRepository]:
    """Реальный SQLite репозиторий в памяти."""
    repo = SqliteUserRepository(":memory:")
    yield repo
    repo.close()


@pytest.fixture
def mock_notifier() -> AsyncMock:
    """Заглушка (Mock) сервиса уведомлений."""
    return AsyncMock(spec=INotificationService)


@pytest.fixture
def event_bus(mock_notifier: AsyncMock) -> InMemoryEventBus:
    """Реальная шина событий с зарегистрированным обработчиком."""
    bus = InMemoryEventBus()
    handler = UserRegisteredNotificationHandler(
        notification_service=mock_notifier
    )
    bus.subscribe(UserRegisteredEvent, handler)
    return bus


@pytest.fixture
def register_use_case(
    sqlite_repo: SqliteUserRepository,
    event_bus: InMemoryEventBus,
) -> RegisterUserUseCase:
    """Экземпляр RegisterUserUseCase со связкой реальных компонентов."""
    return RegisterUserUseCase(
        user_repo=sqlite_repo,
        event_publisher=event_bus,
    )


@pytest.fixture
def valid_user_credentials() -> dict[str, str]:
    """Валидные учетные данные пользователя."""
    return {
        "login": "new_user@example.com",
        "password": "Пароль1!",
    }
