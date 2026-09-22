from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.entrypoints.http.dependencies import (
    get_event_bus,
    get_notifier,
    get_user_repository,
)
from app.entrypoints.http.main import app
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.infrastructure.repositories.sqlite_user_repo import (
    SqliteUserRepository,
)


@pytest.fixture
def http_client(
    sqlite_repo: SqliteUserRepository,
    event_bus: InMemoryEventBus,
    mock_notifier: AsyncMock,
) -> Generator[TestClient]:
    """TestClient с реальным SQLite репозиторием, шиной событий и моком почты."""
    app.dependency_overrides[get_user_repository] = lambda: sqlite_repo
    app.dependency_overrides[get_notifier] = lambda: mock_notifier
    app.dependency_overrides[get_event_bus] = lambda: event_bus

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


async def test_http_register_e2e_with_real_components_and_email_mock(
    http_client: TestClient,
    sqlite_repo: SqliteUserRepository,
    event_bus: InMemoryEventBus,
    mock_notifier: AsyncMock,
    valid_user_credentials: dict[str, str],
) -> None:
    """Вызов эндпоинта /v1/auth/register с реальной связкой компонентов и моком почты."""
    login = valid_user_credentials["login"]
    password = valid_user_credentials["password"]
    payload = {
        "login": login,
        "password": password,
        "confirmPassword": password,
    }

    response = http_client.post("/v1/auth/register", json=payload)

    # 1. Проверяем HTTP-ответ
    assert response.status_code == status.HTTP_200_OK
    assert response.text == "OK"

    # Дожидаемся завершения фоновых задач шины
    await event_bus.wait_until_idle()

    # 2. Проверяем наличие пользователя в реальной SQLite БД
    user_in_db = await sqlite_repo.get_by_login(login)
    assert user_in_db is not None
    assert user_in_db.login == login
    assert user_in_db.password == password

    # 3. Проверяем вызов мока нотификатора
    mock_notifier.notify.assert_awaited_once_with(
        f"User '{login}' successfully registered"
    )


async def test_http_register_duplicate_returns_conflict_status(
    http_client: TestClient,
    event_bus: InMemoryEventBus,
    mock_notifier: AsyncMock,
    valid_user_credentials: dict[str, str],
) -> None:
    """Повторный HTTP-запрос возвращает 409 Conflict и не вызывает нотификатор повторно."""
    login = valid_user_credentials["login"]
    password = valid_user_credentials["password"]
    payload = {
        "login": login,
        "password": password,
        "confirmPassword": password,
    }

    # Первый вызов успешен
    first_resp = http_client.post("/v1/auth/register", json=payload)
    assert first_resp.status_code == status.HTTP_200_OK

    await event_bus.wait_until_idle()
    assert mock_notifier.notify.await_count == 1
    mock_notifier.reset_mock()

    # Второй вызов приводит к ошибке 409
    second_resp = http_client.post("/v1/auth/register", json=payload)
    assert second_resp.status_code == status.HTTP_409_CONFLICT
    assert second_resp.text == f"Логин '{login}' уже занят"

    await event_bus.wait_until_idle()
    mock_notifier.notify.assert_not_called()
