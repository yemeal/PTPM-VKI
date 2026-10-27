import uuid

import httpx
import pytest

from app.domain.limits import MAX_MESSAGE_TEXT_LENGTH, MAX_USERNAME_LENGTH


@pytest.mark.integration
async def test_create_comment_empty_author_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/comments",
        json={"author": "", "text": "Valid text"},
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_comment_whitespace_author_returns_422(
    client: httpx.AsyncClient,
) -> None:
    # Пробелы проходят схему Pydantic (len > 0), но отвергаются доменным инвариантом
    resp = await client.post(
        "/api/v1/comments",
        json={"author": "     ", "text": "Valid text"},
    )
    assert resp.status_code == 422
    assert "Invalid username" in resp.json()["detail"]


@pytest.mark.integration
async def test_create_comment_empty_text_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/comments",
        json={"author": "alice", "text": ""},
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_comment_whitespace_text_returns_422(
    client: httpx.AsyncClient,
) -> None:
    # Пробелы и переводы строк в тексте отвергаются доменным инвариантом
    resp = await client.post(
        "/api/v1/comments",
        json={"author": "alice", "text": "   \n\t   "},
    )
    assert resp.status_code == 422
    assert "Invalid message text" in resp.json()["detail"]


@pytest.mark.integration
async def test_create_comment_oversized_author_returns_422(
    client: httpx.AsyncClient,
) -> None:
    too_long = "u" * (MAX_USERNAME_LENGTH + 1)
    resp = await client.post(
        "/api/v1/comments",
        json={"author": too_long, "text": "Valid text"},
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_comment_oversized_text_returns_422(
    client: httpx.AsyncClient,
) -> None:
    too_long = "m" * (MAX_MESSAGE_TEXT_LENGTH + 1)
    resp = await client.post(
        "/api/v1/comments",
        json={"author": "alice", "text": too_long},
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_create_comment_forbids_extra_field_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/comments",
        json={
            "author": "alice",
            "text": "Valid text",
            "malicious_extra_field": "hacked",
        },
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_comment_whitespace_text_returns_422(
    client: httpx.AsyncClient,
) -> None:
    created = await client.post(
        "/api/v1/comments",
        json={"author": "alice", "text": "Initial text"},
    )
    comment_id = created.json()["id"]

    resp = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"text": "   \r\n   ", "expected_version": 1},
    )
    assert resp.status_code == 422
    assert "Invalid message text" in resp.json()["detail"]


@pytest.mark.integration
@pytest.mark.parametrize("invalid_version", [0, -1, -99])
async def test_update_comment_invalid_version_returns_422(
    client: httpx.AsyncClient, invalid_version: int
) -> None:
    resp = await client.patch(
        f"/api/v1/comments/{uuid.uuid4()}",
        json={"text": "New text", "expected_version": invalid_version},
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_update_comment_forbids_extra_field_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.patch(
        f"/api/v1/comments/{uuid.uuid4()}",
        json={
            "text": "New text",
            "expected_version": 1,
            "disallowed_extra": "value",
        },
    )
    assert resp.status_code == 422
