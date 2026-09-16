import pytest
from pydantic import ValidationError

from app.domain.exceptions import (
    InvalidPasswordCharactersError,
    PasswordNoDigitError,
    PasswordNoLowercaseError,
    PasswordNoSpecialError,
    PasswordNoUppercaseError,
    PasswordTooShortError,
)
from app.domain.user import User


@pytest.mark.parametrize(
    "password",
    [
        "",
        "Пар1!",
        "Паро1!",
    ],
)
def test_password_too_short(password: str, valid_login: str) -> None:
    with pytest.raises(
        ValidationError, match="Пароль должен содержать минимум 7 символов"
    ) as exc_info:
        User(
            login=valid_login,
            password=password,
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), PasswordTooShortError)
        for err in exc_info.value.errors()
    )


@pytest.mark.parametrize(
    "password",
    [
        "Password1!",
        "Пароль1 ",
    ],
)
def test_password_invalid_characters(
    password: str,
    valid_login: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match="Пароль может содержать только кириллицу, цифры и спецсимволы",
    ) as exc_info:
        User(
            login=valid_login,
            password=password,
        )
    assert any(
        isinstance(
            err.get("ctx", {}).get("error"), InvalidPasswordCharactersError
        )
        for err in exc_info.value.errors()
    )


def test_password_no_lowercase(valid_login: str) -> None:
    with pytest.raises(
        ValidationError, match="минимум одну строчную букву"
    ) as exc_info:
        User(
            login=valid_login,
            password="ПАРОЛЬ1!",
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), PasswordNoLowercaseError)
        for err in exc_info.value.errors()
    )


def test_password_no_uppercase(valid_login: str) -> None:
    with pytest.raises(
        ValidationError, match="минимум одну заглавную букву"
    ) as exc_info:
        User(
            login=valid_login,
            password="пароль1!",
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), PasswordNoUppercaseError)
        for err in exc_info.value.errors()
    )


def test_password_no_digit(valid_login: str) -> None:
    with pytest.raises(
        ValidationError, match="минимум одну цифру"
    ) as exc_info:
        User(
            login=valid_login,
            password="Пароль!",
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), PasswordNoDigitError)
        for err in exc_info.value.errors()
    )


def test_password_no_special(valid_login: str) -> None:
    with pytest.raises(
        ValidationError, match="минимум один спецсимвол"
    ) as exc_info:
        User(
            login=valid_login,
            password="Пароль1",
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), PasswordNoSpecialError)
        for err in exc_info.value.errors()
    )


def test_password_min_length(valid_login: str) -> None:
    password = "Парол1!"  # ровно 7 символов

    user = User(
        login=valid_login,
        password=password,
    )

    assert user.password == password
