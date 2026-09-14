import pytest
from pydantic import ValidationError

from app.schemas import UserLogin


@pytest.mark.parametrize(
    "login",
    [
        "example@example.com",
        "+7-999-123-4567",
        "user_123",
        "abc_1",
    ],
)
def test_valid_login(login: str, valid_password: str) -> None:
    user_login = UserLogin(
        login=login,
        password=valid_password,
        confirm_password=valid_password,
    )

    assert user_login.model_dump() == {
        "login": login,
        "password": valid_password,
        "confirm_password": valid_password,
    }


def test_login_empty(valid_password: str) -> None:
    with pytest.raises(ValidationError, match="Логин не может быть пустым"):
        UserLogin(
            login="",
            password=valid_password,
            confirm_password=valid_password,
        )


@pytest.mark.parametrize(
    "login",
    [
        "admin",
        "ADMIN",  # регистронезависимый
        "moderator",
        "hacker",
    ],
)
def test_login_blacklisted(login: str, valid_password: str) -> None:
    with pytest.raises(ValidationError, match="Логин запрещен"):
        UserLogin(
            login=login,
            password=valid_password,
            confirm_password=valid_password,
        )


@pytest.mark.parametrize(
    "login",
    [
        "example@",
        "example@example",
        "example@example.c",
    ],
)
def test_login_invalid_email(login: str, valid_password: str) -> None:
    with pytest.raises(ValidationError, match="Некорректный формат email"):
        UserLogin(
            login=login,
            password=valid_password,
            confirm_password=valid_password,
        )


@pytest.mark.parametrize(
    "login",
    [
        "+79991234567",
        "+7-999-123-456",
    ],
)
def test_login_invalid_phone(login: str, valid_password: str) -> None:
    with pytest.raises(
        ValidationError, match="Телефон должен соответствовать формату"
    ):
        UserLogin(
            login=login,
            password=valid_password,
            confirm_password=valid_password,
        )


@pytest.mark.parametrize(
    "login",
    [
        "a",
        "ab",
        "abc",
        "abcd",
    ],
)
def test_login_too_short(login: str, valid_password: str) -> None:
    with pytest.raises(
        ValidationError, match="Логин должен содержать минимум 5 символов"
    ):
        UserLogin(
            login=login,
            password=valid_password,
            confirm_password=valid_password,
        )


@pytest.mark.parametrize(
    "login",
    [
        "user-test",
        "user!test",
        "пользователь",
        "пользователь1",
        "пользователь1!",
    ],
)
def test_login_invalid_characters(login: str, valid_password: str) -> None:
    with pytest.raises(
        ValidationError,
        match="Логин может содержать только латинские буквы, цифры и _",
    ):
        UserLogin(
            login=login,
            password=valid_password,
            confirm_password=valid_password,
        )
