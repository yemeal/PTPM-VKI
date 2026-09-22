from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.application.ports.event_bus import IEventPublisher
from app.application.ports.repository import IUserRepository
from app.application.use_cases.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from app.domain.events import UserRegisteredEvent
from app.domain.exceptions import BlacklistedLoginError, LoginAlreadyTakenError
from app.domain.user import User


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    """Изолированный мок репозитория пользователей."""
    return AsyncMock(spec=IUserRepository)


@pytest.fixture
def mock_event_publisher() -> AsyncMock:
    """Изолированный мок издателя событий."""
    return AsyncMock(spec=IEventPublisher)


@pytest.fixture
def use_case(
    mock_user_repo: AsyncMock,
    mock_event_publisher: AsyncMock,
) -> RegisterUserUseCase:
    """Экземпляр RegisterUserUseCase с поддельными зависимостями."""
    return RegisterUserUseCase(
        user_repo=mock_user_repo,
        event_publisher=mock_event_publisher,
    )


async def test_register_user_success_isolated(
    use_case: RegisterUserUseCase,
    mock_user_repo: AsyncMock,
    mock_event_publisher: AsyncMock,
) -> None:
    """Успешная регистрация без реальной БД и шины."""
    login = "unique_user@example.com"
    password = "Пароль1!"
    mock_user_repo.get_by_login.return_value = None

    command = RegisterUserCommand(login=login, password=password)
    result = await use_case.execute(command)

    # Проверка вызова проверки существования логина
    mock_user_repo.get_by_login.assert_awaited_once_with(login)

    # Проверка сохранения пользователя
    mock_user_repo.add.assert_awaited_once()
    added_user = mock_user_repo.add.call_args[0][0]
    assert isinstance(added_user, User)
    assert added_user.login == login
    assert added_user.password == password

    # Проверка отправки события
    mock_event_publisher.publish.assert_awaited_once()
    published_event = mock_event_publisher.publish.call_args[0][0]
    assert isinstance(published_event, UserRegisteredEvent)
    assert published_event.login == login

    # Проверка возвращаемого значения
    assert result == added_user


async def test_register_user_duplicate_login_isolated(
    use_case: RegisterUserUseCase,
    mock_user_repo: AsyncMock,
    mock_event_publisher: AsyncMock,
) -> None:
    """Попытка регистрации дубликата логина не вызывает add и publish."""
    login = "existing@example.com"
    password = "Пароль1!"
    existing_user = User(login=login, password=password)
    mock_user_repo.get_by_login.return_value = existing_user

    command = RegisterUserCommand(login=login, password=password)

    with pytest.raises(
        LoginAlreadyTakenError, match=f"Логин '{login}' уже занят"
    ):
        await use_case.execute(command)

    mock_user_repo.get_by_login.assert_awaited_once_with(login)
    mock_user_repo.add.assert_not_called()
    mock_event_publisher.publish.assert_not_called()


async def test_register_user_domain_validation_failure_prevents_persistence(
    use_case: RegisterUserUseCase,
    mock_user_repo: AsyncMock,
    mock_event_publisher: AsyncMock,
) -> None:
    """Ошибка валидации домена останавливает процесс до сохранения."""
    login = "admin"  # Запрещенный правилами черный список
    password = "Пароль1!"
    mock_user_repo.get_by_login.return_value = None

    command = RegisterUserCommand(login=login, password=password)

    with pytest.raises(ValidationError, match="Логин запрещен") as exc_info:
        await use_case.execute(command)

    assert any(
        isinstance(err.get("ctx", {}).get("error"), BlacklistedLoginError)
        for err in exc_info.value.errors()
    )

    mock_user_repo.get_by_login.assert_awaited_once_with(login)
    mock_user_repo.add.assert_not_called()
    mock_event_publisher.publish.assert_not_called()
