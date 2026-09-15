import pytest

from app.schemas import UserRegister


@pytest.fixture
def valid_login() -> str:
    return "example@example.com"


@pytest.fixture
def valid_password() -> str:
    return "Пароль1!"


@pytest.fixture
def valid_user_register_schema(
    valid_login: str,
    valid_password: str,
) -> UserRegister:
    return UserRegister(
        login=valid_login,
        password=valid_password,
        confirm_password=valid_password,
    )
