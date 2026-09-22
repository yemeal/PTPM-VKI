import sqlite3
from collections.abc import Generator

import pytest

from app.domain.user import User
from app.infrastructure.repositories.sqlite_user_repo import (
    SqliteUserRepository,
)


@pytest.fixture
def repo() -> Generator[SqliteUserRepository]:
    """Фикстура изолированного SQLite репозитория в памяти."""
    repository = SqliteUserRepository(":memory:")
    yield repository
    repository.close()


@pytest.fixture
def sample_user() -> User:
    """Фикстура валидного доменного пользователя."""
    return User(login="test_user@example.com", password="Пароль1!")


async def test_add_and_get_by_login_found(
    repo: SqliteUserRepository,
    sample_user: User,
) -> None:
    """Прямое тестирование: добавление пользователя и поиск по логину (найден)."""
    await repo.add(sample_user)

    fetched = await repo.get_by_login(sample_user.login)

    assert fetched is not None
    assert fetched.login == sample_user.login
    assert fetched.password == sample_user.password


async def test_get_by_login_not_found(repo: SqliteUserRepository) -> None:
    """Прямое тестирование: поиск несуществующего логина возвращает None."""
    fetched = await repo.get_by_login("not_found@example.com")
    assert fetched is None


async def test_delete_existing_user_returns_true(
    repo: SqliteUserRepository,
    sample_user: User,
) -> None:
    """Прямое тестирование: удаление существующего пользователя (успех)."""
    await repo.add(sample_user)

    deleted = await repo.delete(sample_user.login)
    assert deleted is True

    # Проверяем, что пользователь больше не существует
    assert await repo.get_by_login(sample_user.login) is None


async def test_delete_non_existent_user_returns_false(
    repo: SqliteUserRepository,
) -> None:
    """Прямое тестирование: удаление несуществующего пользователя (не найден)."""
    deleted = await repo.delete("ghost_user@example.com")
    assert deleted is False


async def test_add_duplicate_login_raises_integrity_error(
    repo: SqliteUserRepository,
    sample_user: User,
) -> None:
    """База данных предотвращает дублирование первичного ключа login."""
    await repo.add(sample_user)

    duplicate_user = User(
        login=sample_user.login,
        password="ДругойПароль2!",
    )

    with pytest.raises(sqlite3.IntegrityError):
        await repo.add(duplicate_user)


def test_context_manager_lifecycle() -> None:
    """Проверка корректной работы контекстного менеджера и закрытия соединения."""
    with SqliteUserRepository(":memory:") as repository:
        assert repository._connection is not None

    # Попытка выполнить запрос на закрытом соединении вызывает ошибку
    with pytest.raises(sqlite3.ProgrammingError):
        repository._connection.execute("SELECT 1;")
