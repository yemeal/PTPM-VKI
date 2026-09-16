import pytest
from pydantic import ValidationError

from app.domain.exceptions import PasswordMismatchError
from app.entrypoints.http.schemas import UserRegisterRequest


def test_password_match_success() -> None:
    schema = UserRegisterRequest(
        login="example@example.com",
        password="Пароль1!",
        confirm_password="Пароль1!",
    )
    assert schema.login == "example@example.com"
    assert schema.password == "Пароль1!"
    assert schema.confirm_password == "Пароль1!"


def test_password_mismatch() -> None:
    with pytest.raises(
        ValidationError,
        match="Пароль и подтверждение пароля не совпадают",
    ) as exc_info:
        UserRegisterRequest(
            login="example@example.com",
            password="Пароль1!",
            confirm_password="Другой1!",
        )
    assert any(
        isinstance(err.get("ctx", {}).get("error"), PasswordMismatchError)
        for err in exc_info.value.errors()
    )


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        UserRegisterRequest.model_validate(
            {
                "login": "example@example.com",
                "password": "Пароль1!",
                "confirm_password": "Пароль1!",
                "extra": "field",
            }
        )


def test_camel_case_alias() -> None:
    schema = UserRegisterRequest.model_validate(
        {
            "login": "example@example.com",
            "password": "Пароль1!",
            "confirmPassword": "Пароль1!",
        }
    )
    assert schema.confirm_password == "Пароль1!"
