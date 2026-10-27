import uuid

import httpx
import pytest


@pytest.mark.integration
async def test_create_comment_success(client: httpx.AsyncClient) -> None:
    payload = {
        "author": "alice",
        "text": "Hello world from integration test",
        "source_url": "https://forum.example.com/topic/1",
        "external_id": 1001,
    }
    resp = await client.post("/api/v1/comments", json=payload)
    assert resp.status_code == 201

    data = resp.json()
    assert uuid.UUID(data["id"])
    assert data["author"] == "alice"
    assert data["text"] == "Hello world from integration test"
    assert data["source_url"] == "https://forum.example.com/topic/1"
    assert data["external_id"] == 1001
    assert data["version"] == 1
    assert data["updated_at"] is None
    assert data["created_at"] is not None


@pytest.mark.integration
async def test_create_comment_without_external_id(
    client: httpx.AsyncClient,
) -> None:
    payload = {
        "author": "bob",
        "text": "User created comment without external source ID",
    }
    resp = await client.post("/api/v1/comments", json=payload)
    assert resp.status_code == 201

    data = resp.json()
    assert data["author"] == "bob"
    assert data["external_id"] is None
    assert data["source_url"] == ""


@pytest.mark.integration
async def test_create_comment_duplicate_natural_key_returns_409(
    client: httpx.AsyncClient,
) -> None:
    payload = {
        "author": "charlie",
        "text": "Original comment",
        "source_url": "https://forum.example.com/topic/duplicate",
        "external_id": 500,
    }
    first_resp = await client.post("/api/v1/comments", json=payload)
    assert first_resp.status_code == 201

    dup_resp = await client.post("/api/v1/comments", json=payload)
    assert dup_resp.status_code == 409
    assert "already exists" in dup_resp.json()["detail"].lower()


@pytest.mark.integration
async def test_create_comment_same_external_id_different_sources(
    client: httpx.AsyncClient,
) -> None:
    res1 = await client.post(
        "/api/v1/comments",
        json={
            "author": "user_forum_a",
            "text": "Post on Forum A",
            "source_url": "https://site-a.com/thread/1",
            "external_id": 999,
        },
    )
    res2 = await client.post(
        "/api/v1/comments",
        json={
            "author": "user_forum_b",
            "text": "Post on Forum B",
            "source_url": "https://site-b.com/thread/1",
            "external_id": 999,
        },
    )
    assert res1.status_code == 201
    assert res2.status_code == 201

    id1 = res1.json()["id"]
    id2 = res2.json()["id"]
    assert id1 != id2


@pytest.mark.integration
async def test_get_comment_by_id_success(client: httpx.AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/comments",
        json={
            "author": "diana",
            "text": "Comment to fetch",
            "source_url": "https://example.com/topic/fetch",
            "external_id": 1,
        },
    )
    comment_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/comments/{comment_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == comment_id
    assert get_resp.json()["author"] == "diana"


@pytest.mark.integration
async def test_get_comment_not_found_returns_404(
    client: httpx.AsyncClient,
) -> None:
    random_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/comments/{random_id}")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.integration
async def test_get_comment_invalid_uuid_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.get("/api/v1/comments/not-a-valid-uuid")
    assert resp.status_code == 422


@pytest.mark.integration
async def test_patch_comment_success(client: httpx.AsyncClient) -> None:
    created = await client.post(
        "/api/v1/comments",
        json={"author": "eric", "text": "Initial text for patch"},
    )
    comment_id = created.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"text": "Patched content", "expected_version": 1},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["text"] == "Patched content"
    assert data["version"] == 2
    assert data["updated_at"] is not None


@pytest.mark.integration
async def test_put_comment_success(client: httpx.AsyncClient) -> None:
    created = await client.post(
        "/api/v1/comments",
        json={"author": "fiona", "text": "Initial text for put"},
    )
    comment_id = created.json()["id"]

    put_resp = await client.put(
        f"/api/v1/comments/{comment_id}",
        json={"text": "Put replaced content", "expected_version": 1},
    )
    assert put_resp.status_code == 200
    data = put_resp.json()
    assert data["text"] == "Put replaced content"
    assert data["version"] == 2


@pytest.mark.integration
async def test_update_comment_concurrency_conflict_returns_409(
    client: httpx.AsyncClient,
) -> None:
    created = await client.post(
        "/api/v1/comments",
        json={"author": "george", "text": "Concurrency test"},
    )
    comment_id = created.json()["id"]

    conflict_resp = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"text": "Conflict edit", "expected_version": 999},
    )
    assert conflict_resp.status_code == 409
    assert (
        "modified by another transaction"
        in conflict_resp.json()["detail"].lower()
    )


@pytest.mark.integration
async def test_update_comment_not_found_returns_404(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.patch(
        f"/api/v1/comments/{uuid.uuid4()}",
        json={"text": "Edit", "expected_version": 1},
    )
    assert resp.status_code == 404


@pytest.mark.integration
async def test_delete_comment_success(client: httpx.AsyncClient) -> None:
    created = await client.post(
        "/api/v1/comments",
        json={"author": "helen", "text": "Comment to delete"},
    )
    comment_id = created.json()["id"]

    del_resp = await client.delete(f"/api/v1/comments/{comment_id}")
    assert del_resp.status_code == 204

    # Повторная попытка чтения возвращает 404
    get_resp = await client.get(f"/api/v1/comments/{comment_id}")
    assert get_resp.status_code == 404


@pytest.mark.integration
async def test_delete_comment_not_found_returns_404(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.delete(f"/api/v1/comments/{uuid.uuid4()}")
    assert resp.status_code == 404
