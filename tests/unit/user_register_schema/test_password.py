import pytest
from pydantic import ValidationError

from app.schemas import UserRegister


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
    ):
        UserRegister(
            login=valid_login,
            password=password,
            confirm_password=password,
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
    ):
        UserRegister(
            login=valid_login,
            password=password,
            confirm_password=password,
        )


def test_password_no_lowercase(valid_login: str) -> None:
    with pytest.raises(ValidationError, match="минимум одну строчную букву"):
        UserRegister(
            login=valid_login,
            password="ПАРОЛЬ1!",
            confirm_password="ПАРОЛЬ1!",
        )


def test_password_no_uppercase(valid_login: str) -> None:
    with pytest.raises(ValidationError, match="минимум одну заглавную букву"):
        UserRegister(
            login=valid_login,
            password="пароль1!",
            confirm_password="пароль1!",
        )


def test_password_no_digit(valid_login: str) -> None:
    with pytest.raises(ValidationError, match="минимум одну цифру"):
        UserRegister(
            login=valid_login,
            password="Пароль!",
            confirm_password="Пароль!",
        )


def test_password_no_special(valid_login: str) -> None:
    with pytest.raises(ValidationError, match="минимум один спецсимвол"):
        UserRegister(
            login=valid_login,
            password="Пароль1",
            confirm_password="Пароль1",
        )


def test_password_mismatch(valid_login: str, valid_password: str) -> None:
    with pytest.raises(
        ValidationError,
        match="Пароль и подтверждение пароля не совпадают",
    ):
        UserRegister(
            login=valid_login,
            password=valid_password,
            confirm_password="Другой1!",
        )


def test_password_min_length(valid_login: str) -> None:
    password = "Парол1!"  # ровно 7 символов

    user_login = UserRegister(
        login=valid_login,
        password=password,
        confirm_password=password,
    )

    assert user_login.password == password
