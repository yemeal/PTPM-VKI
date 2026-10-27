from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

import httpx
import pytest
from dishka import Provider, Scope, provide

from app.application.ports.forum_parser import ForumParserProtocol
from app.infrastructure.parsers.soup_forum_parser import (
    BeautifulSoupForumParser,
)


@pytest.mark.integration
async def test_parse_page_success_and_idempotency(
    client: httpx.AsyncClient,
) -> None:
    parse_payload = {"url": "https://forum.example.com/topic/10"}
    resp = await client.post("/api/v1/comments/parse", json=parse_payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_parsed"] == 3
    assert data["saved_count"] == 3
    assert len(data["comments"]) == 3

    # Проверка сохранения первого комментария
    c1_id = data["comments"][0]["id"]
    c1_resp = await client.get(f"/api/v1/comments/{c1_id}")
    assert c1_resp.status_code == 200
    assert c1_resp.json()["author"] == "tech_guru"
    assert c1_resp.json()["external_id"] == 101

    # Повторный вызов парсинга страницы (идемпотентность: повторно не сохраняет)
    resp2 = await client.post("/api/v1/comments/parse", json=parse_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total_parsed"] == 3
    assert data2["saved_count"] == 0


@pytest.mark.integration
async def test_parse_page_invalid_url_scheme_returns_422(
    client: httpx.AsyncClient,
) -> None:
    invalid_payload = {"url": "hts://habr.com/ru/articles/750312/"}
    resp = await client.post("/api/v1/comments/parse", json=invalid_payload)
    assert resp.status_code == 422
    assert "detail" in resp.json()


@pytest.mark.integration
async def test_parse_page_malformed_url_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/comments/parse", json={"url": "not-a-valid-url"}
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_parse_page_empty_body_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post("/api/v1/comments/parse", json={})
    assert resp.status_code == 422


@pytest.mark.integration
async def test_parse_page_forbids_extra_fields_returns_422(
    client: httpx.AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/comments/parse",
        json={
            "url": "https://example.com/topic/1",
            "extra_field": "disallowed",
        },
    )
    assert resp.status_code == 422


@pytest.mark.integration
async def test_parse_page_unreachable_upstream_returns_400(
    client_factory: Callable[
        [Provider], AbstractAsyncContextManager[httpx.AsyncClient]
    ],
) -> None:
    class FailingForumAppProvider(Provider):
        __test__ = False

        @provide(scope=Scope.REQUEST)
        def provide_forum_parser(self) -> ForumParserProtocol:
            transport = httpx.MockTransport(
                lambda _req: httpx.Response(500, text="Internal Server Error")
            )
            return BeautifulSoupForumParser(
                client=httpx.AsyncClient(transport=transport)
            )

    async with client_factory(FailingForumAppProvider()) as c:
        resp = await c.post(
            "/api/v1/comments/parse",
            json={"url": "https://example.com/topic"},
        )
        assert resp.status_code == 400
        assert "HTTP status 500" in resp.json()["detail"]


@pytest.mark.integration
async def test_parse_page_connection_failure_returns_502(
    client_factory: Callable[
        [Provider], AbstractAsyncContextManager[httpx.AsyncClient]
    ],
) -> None:
    class ConnectErrorForumAppProvider(Provider):
        __test__ = False

        @provide(scope=Scope.REQUEST)
        def provide_forum_parser(self) -> ForumParserProtocol:
            def handler(_req: httpx.Request) -> httpx.Response:
                raise httpx.ConnectError("Connection refused")

            transport = httpx.MockTransport(handler)
            return BeautifulSoupForumParser(
                client=httpx.AsyncClient(transport=transport)
            )

    async with client_factory(ConnectErrorForumAppProvider()) as c:
        resp = await c.post(
            "/api/v1/comments/parse",
            json={"url": "https://example.com/topic"},
        )
        assert resp.status_code == 502
        assert "Failed to fetch forum page" in resp.json()["detail"]
