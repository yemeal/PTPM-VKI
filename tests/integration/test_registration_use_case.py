from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from app.domain.exceptions import LoginAlreadyTakenError
from app.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from app.infrastructure.repositories.sqlite_user_repo import (
    SqliteUserRepository,
)


async def test_scenario_1_successful_registration_flow(
    register_use_case: RegisterUserUseCase,
    sqlite_repo: SqliteUserRepository,
    event_bus: InMemoryEventBus,
    mock_notifier: AsyncMock,
    valid_user_credentials: dict[str, str],
) -> None:
    """Сценарий 1 (Сквозная успешная регистрация):

    RegisterUserUseCase + реальная SQLite :memory: + шина событий +
    заглушка (Mock) для INotificationService.
    Проверяем:
    - пользователь сохранился в SQLite;
    - шина доставила событие;
    - нотификатор был вызван ровно 1 раз с сообщением об успехе.
    """
    login = valid_user_credentials["login"]
    password = valid_user_credentials["password"]
    command = RegisterUserCommand(login=login, password=password)

    registered_user = await register_use_case.execute(command)

    # Дожидаемся завершения фоновых задач шины событий
    await event_bus.wait_until_idle()

    # 1. Проверяем возвращенную сущность
    assert registered_user.login == login
    assert registered_user.password == password

    # 2. Проверяем, что пользователь сохранился в SQLite БД
    user_in_db = await sqlite_repo.get_by_login(login)
    assert user_in_db is not None
    assert user_in_db.login == login
    assert user_in_db.password == password

    # 3. Проверяем, что нотификатор был вызван ровно 1 раз с успехом
    mock_notifier.notify.assert_awaited_once_with(
        f"User '{login}' successfully registered"
    )


async def test_scenario_2_duplicate_login_conflict(
    register_use_case: RegisterUserUseCase,
    sqlite_repo: SqliteUserRepository,
    event_bus: InMemoryEventBus,
    mock_notifier: AsyncMock,
    valid_user_credentials: dict[str, str],
) -> None:
    """Сценарий 2 (Конфликт дубликата логина):

    Попытка повторной регистрации через RegisterUserUseCase с реальной SQLite.
    Проверяем:
    - выбрасывается LoginAlreadyTakenError;
    - в БД не перезаписались данные;
    - нотификатор не вызывался повторно (assert_not_called).
    """
    login = valid_user_credentials["login"]
    initial_password = valid_user_credentials["password"]

    # 1. Первичная успешная регистрация
    await register_use_case.execute(
        RegisterUserCommand(login=login, password=initial_password)
    )
    await event_bus.wait_until_idle()
    assert mock_notifier.notify.await_count == 1

    # Сбрасываем мок перед второй попыткой
    mock_notifier.reset_mock()

    # 2. Попытка повторной регистрации с тем же логином и другим паролем
    duplicate_command = RegisterUserCommand(
        login=login, password="ДругойПароль2!"
    )

    with pytest.raises(
        LoginAlreadyTakenError, match=f"Логин '{login}' уже занят"
    ):
        await register_use_case.execute(duplicate_command)

    await event_bus.wait_until_idle()

    # 3. Проверяем, что данные в БД не перезаписались
    user_in_db = await sqlite_repo.get_by_login(login)
    assert user_in_db is not None
    assert user_in_db.password == initial_password

    # 4. Проверяем, что нотификатор не вызывался
    mock_notifier.notify.assert_not_called()


async def test_scenario_3_full_crud_cycle_with_use_case(
    register_use_case: RegisterUserUseCase,
    sqlite_repo: SqliteUserRepository,
    valid_user_credentials: dict[str, str],
) -> None:
    """Сценарий 3 (Полный цикл CRUD в связке с юзкейсом):

    Регистрация пользователя ->
    проверка наличия в БД ->
    удаление через repo.delete() ->
    успешная повторная регистрация под тем же логином.
    """
    login = valid_user_credentials["login"]
    first_password = valid_user_credentials["password"]
    second_password = "НовыйПароль9#"

    # 1. Регистрация пользователя через Use Case
    user = await register_use_case.execute(
        RegisterUserCommand(login=login, password=first_password)
    )
    assert user.login == login

    # 2. Проверка наличия в БД
    saved_user = await sqlite_repo.get_by_login(login)
    assert saved_user is not None
    assert saved_user.login == login
    assert saved_user.password == first_password

    # 3. Удаление через repo.delete()
    deleted = await sqlite_repo.delete(login)
    assert deleted is True

    # Проверяем, что пользователя действительно больше нет в БД
    assert await sqlite_repo.get_by_login(login) is None

    # Повторное удаление возвращает False
    assert await sqlite_repo.delete(login) is False

    # 4. Успешная повторная регистрация под тем же логином
    re_registered_user = await register_use_case.execute(
        RegisterUserCommand(login=login, password=second_password)
    )
    assert re_registered_user.login == login
    assert re_registered_user.password == second_password

    # Проверка нового состояния в БД
    current_db_user = await sqlite_repo.get_by_login(login)
    assert current_db_user is not None
    assert current_db_user.password == second_password
