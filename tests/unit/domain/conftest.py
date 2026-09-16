import pytest

from app.domain.user import User


@pytest.fixture
def valid_login() -> str:
    return "example@example.com"


@pytest.fixture
def valid_password() -> str:
    return "Пароль1!"


@pytest.fixture
def valid_user(
    valid_login: str,
    valid_password: str,
) -> User:
    return User(
        login=valid_login,
        password=valid_password,
    )
