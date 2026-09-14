import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_login() -> str:
    return "example@example.com"


@pytest.fixture
def valid_password() -> str:
    return "Пароль1!"


@pytest.fixture
def valid_payload(
    valid_login: str,
    valid_password: str,
) -> dict[str, str]:
    return {
        "login": valid_login,
        "password": valid_password,
        "confirmPassword": valid_password,
    }
