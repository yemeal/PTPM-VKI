import pytest


@pytest.fixture
def valid_weight() -> float:
    return 5.0


@pytest.fixture
def valid_distance() -> int:
    return 100


@pytest.fixture
def valid_package_type() -> str:
    return "обычный"


@pytest.fixture
def valid_is_express() -> bool:
    return False


@pytest.fixture
def invalid_result() -> tuple[int, str]:
    return -1, "0000-00-00"
