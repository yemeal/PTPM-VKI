import pytest
from pydantic import ValidationError

from app.domain.exceptions import (
    BlacklistedLoginError,
    EmptyLoginError,
    InvalidEmailFormatError,
    InvalidLoginCharactersError,
    InvalidPhoneFormatError,
    LoginTooShortError,
)
from app.domain.user import User


@pytest.mark.parametrize(
    "login",
    [
        "example@example.com",
        "   example@example.com   ",
        "+7-999-123-4567",
        "   +7-999-123-4567   ",
        "user_123",
        "  user_123  ",
        "abc_1",
    ],
)
def test_valid_login(login: str, valid_password: str) -> None:
    user = User(
        login=login,
        password=valid_password,
    )

    assert user.model_dump() == {
        "login": login.strip(),
        "password": valid_password,
    }


def test_login_empty(valid_password: str) -> None:
    with pytest.raises(
        ValidationError, match="Логин не может быть пустым"
    ) as exc_info:
        User(
            login="",
            password=valid_password,
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), EmptyLoginError)
        for err in exc_info.value.errors()
    )


@pytest.mark.parametrize(
    "login",
    [
        "admin",
        "ADMIN",  # регистронезависимый
        "moderator",
        "hacker",
        " admin",
        " ADMIN",
        "admin ",
        "ADMIN ",
    ],
)
def test_login_blacklisted(login: str, valid_password: str) -> None:
    with pytest.raises(ValidationError, match="Логин запрещен") as exc_info:
        User(
            login=login,
            password=valid_password,
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), BlacklistedLoginError)
        for err in exc_info.value.errors()
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
    with pytest.raises(
        ValidationError, match="Некорректный формат email"
    ) as exc_info:
        User(
            login=login,
            password=valid_password,
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), InvalidEmailFormatError)
        for err in exc_info.value.errors()
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
    ) as exc_info:
        User(
            login=login,
            password=valid_password,
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), InvalidPhoneFormatError)
        for err in exc_info.value.errors()
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
    ) as exc_info:
        User(
            login=login,
            password=valid_password,
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), LoginTooShortError)
        for err in exc_info.value.errors()
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
    ) as exc_info:
        User(
            login=login,
            password=valid_password,
        )
    assert any(
        isinstance(
            err.get("ctx", {}).get("error"), InvalidLoginCharactersError
        )
        for err in exc_info.value.errors()
    )
