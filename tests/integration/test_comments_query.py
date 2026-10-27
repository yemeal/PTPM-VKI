import httpx
import pytest


@pytest.mark.integration
async def test_list_comments_pagination_pages(
    client: httpx.AsyncClient,
) -> None:
    source_url = "https://forum.example.com/topic/paged"
    for i in range(5):
        await client.post(
            "/api/v1/comments",
            json={
                "author": f"user_{i}",
                "text": f"Page item {i}",
                "source_url": source_url,
                "external_id": i + 1,
            },
        )

    # Страница 1 (limit=2, offset=0)
    p1 = await client.get(
        f"/api/v1/comments?source_url={source_url}&limit=2&offset=0"
    )
    assert p1.status_code == 200
    d1 = p1.json()
    assert d1["total"] == 5
    assert len(d1["items"]) == 2
    assert d1["items"][0]["text"] == "Page item 0"
    assert d1["items"][1]["text"] == "Page item 1"

    # Страница 2 (limit=2, offset=2)
    p2 = await client.get(
        f"/api/v1/comments?source_url={source_url}&limit=2&offset=2"
    )
    assert p2.status_code == 200
    d2 = p2.json()
    assert d2["total"] == 5
    assert len(d2["items"]) == 2
    assert d2["items"][0]["text"] == "Page item 2"
    assert d2["items"][1]["text"] == "Page item 3"

    # Страница 3 (limit=2, offset=4)
    p3 = await client.get(
        f"/api/v1/comments?source_url={source_url}&limit=2&offset=4"
    )
    assert p3.status_code == 200
    d3 = p3.json()
    assert d3["total"] == 5
    assert len(d3["items"]) == 1
    assert d3["items"][0]["text"] == "Page item 4"


@pytest.mark.integration
async def test_list_comments_filter_by_author(
    client: httpx.AsyncClient,
) -> None:
    author = "special_author"
    await client.post(
        "/api/v1/comments",
        json={"author": author, "text": "Msg 1"},
    )
    await client.post(
        "/api/v1/comments",
        json={"author": "other_author", "text": "Msg 2"},
    )
    await client.post(
        "/api/v1/comments",
        json={"author": author, "text": "Msg 3"},
    )

    resp = await client.get(f"/api/v1/comments?author={author}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(c["author"] == author for c in data["items"])


@pytest.mark.integration
async def test_list_comments_filter_by_source_url(
    client: httpx.AsyncClient,
) -> None:
    src1 = "https://example.com/topic/source_filter_1"
    src2 = "https://example.com/topic/source_filter_2"
    await client.post(
        "/api/v1/comments",
        json={"author": "user_a", "text": "A1", "source_url": src1},
    )
    await client.post(
        "/api/v1/comments",
        json={"author": "user_b", "text": "B1", "source_url": src2},
    )

    resp = await client.get(f"/api/v1/comments?source_url={src1}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["source_url"] == src1


@pytest.mark.integration
async def test_list_comments_filter_combined_author_and_source(
    client: httpx.AsyncClient,
) -> None:
    target_src = "https://example.com/topic/combined"
    other_src = "https://example.com/topic/other"
    target_author = "target_user"

    # Совпадает и автор, и источник
    await client.post(
        "/api/v1/comments",
        json={
            "author": target_author,
            "text": "Match",
            "source_url": target_src,
        },
    )
    # Совпадает только автор
    await client.post(
        "/api/v1/comments",
        json={
            "author": target_author,
            "text": "Diff src",
            "source_url": other_src,
        },
    )
    # Совпадает только источник
    await client.post(
        "/api/v1/comments",
        json={
            "author": "other_user",
            "text": "Diff author",
            "source_url": target_src,
        },
    )

    resp = await client.get(
        f"/api/v1/comments?author={target_author}&source_url={target_src}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["text"] == "Match"


@pytest.mark.integration
async def test_list_comments_empty_results(client: httpx.AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/comments?author=completely_nonexistent_user"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.integration
@pytest.mark.parametrize("invalid_limit", [-5, 0, 101])
async def test_list_comments_invalid_limit_returns_422(
    client: httpx.AsyncClient, invalid_limit: int
) -> None:
    resp = await client.get(f"/api/v1/comments?limit={invalid_limit}")
    assert resp.status_code == 422


@pytest.mark.integration
async def test_list_comments_negative_offset_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.get("/api/v1/comments?offset=-1")
    assert resp.status_code == 422
