import pytest
from fastapi.testclient import TestClient

from app.entrypoints.http.dependencies import get_user_repository
from app.infrastructure.repositories.sqlite_user_repo import (
    SqliteUserRepository,
)
from app.main import app


@pytest.fixture(autouse=True)
def clean_db():
    """Изоляция БД: чистый in-memory SQLite репозиторий для каждого теста."""
    repo = SqliteUserRepository(":memory:")
    app.dependency_overrides[get_user_repository] = lambda: repo
    yield
    app.dependency_overrides.pop(get_user_repository, None)
    repo.close()


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
