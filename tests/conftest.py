import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from app.domain.aggregates.comment import Comment


@pytest.fixture
def now() -> datetime:
    """фиксированная временная метка utc для детерминированных тестов"""
    return datetime(2026, 10, 26, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def forum_html() -> str:
    """содержимое страницы тестовой ветки форума"""
    fixture_path = Path(__file__).parent / "fixtures" / "forum_thread.html"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def make_comment(now: datetime) -> Callable[..., Comment]:
    """фабрика доменных сущностей комментариев для тестов"""

    def _factory(**overrides: Any) -> Comment:
        defaults: dict[str, Any] = {
            "id": uuid.uuid4(),
            "source_url": "https://forum.example.com/topic/1",
            "external_id": 1,
            "author": "alice",
            "text": "Default test comment text",
            "created_at": now,
        }
        return Comment.create(**(defaults | overrides))

    return _factory


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """автоматическая маркировка тестов по каталогам (unit / integration)"""
    for item in items:
        if "unit" in item.path.parts and not item.get_closest_marker("unit"):
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.path.parts and not item.get_closest_marker(
            "integration"
        ):
            item.add_marker(pytest.mark.integration)
