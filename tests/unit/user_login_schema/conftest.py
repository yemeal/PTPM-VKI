import pytest

from app.schemas import UserLogin


@pytest.fixture
def valid_login() -> str:
    return "example@example.com"


@pytest.fixture
def valid_password() -> str:
    return "Пароль1!"


@pytest.fixture
def valid_user_login_schema(
    valid_login: str,
    valid_password: str,
) -> UserLogin:
    return UserLogin(
        login=valid_login,
        password=valid_password,
        confirm_password=valid_password,
    )
