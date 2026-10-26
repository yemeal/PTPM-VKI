import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
from dishka import AsyncContainer, Provider, Scope, provide

from app.application.ports.forum_parser import ForumParserProtocol
from app.core.settings import Settings
from app.entrypoints.http.main import create_app
from app.infrastructure.di import create_container
from app.infrastructure.parsers.soup_forum_parser import (
    BeautifulSoupForumParser,
)


@pytest.fixture
def forum_html() -> str:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "forum_thread.html"
    return fixture_path.read_text(encoding="utf-8")


class MockForumAppProvider(Provider):
    """тестовый di-провайдер с моком http-клиента для парсера"""

    __test__ = False

    def __init__(self, html_content: str) -> None:
        super().__init__()
        self._html_content = html_content

    @provide(scope=Scope.REQUEST)
    def provide_forum_parser(self) -> ForumParserProtocol:
        transport = httpx.MockTransport(
            lambda _req: httpx.Response(200, text=self._html_content)
        )
        return BeautifulSoupForumParser(
            client=httpx.AsyncClient(transport=transport)
        )


@pytest.fixture
async def test_container(
    forum_html: str,
) -> AsyncGenerator[AsyncContainer]:
    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")
    container = create_container(
        settings, MockForumAppProvider(html_content=forum_html)
    )
    yield container
    await container.close()


@pytest.fixture
async def client(
    test_container: AsyncContainer,
) -> AsyncGenerator[httpx.AsyncClient]:
    app = create_app(container=test_container)

    # запуск lifespan и создание таблиц
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as ac:
            yield ac


@pytest.mark.integration
async def test_health_endpoints(client: httpx.AsyncClient) -> None:
    live_resp = await client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json() == {"status": "ok"}

    ready_resp = await client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json() == {"status": "ready"}


@pytest.mark.integration
async def test_comments_crud_lifecycle(client: httpx.AsyncClient) -> None:
    # 1. создание комментария
    create_payload = {
        "author": "john_doe",
        "text": "Initial comment text",
        "source_url": "https://example.com/topic/1",
        "external_id": 1,
    }
    resp = await client.post("/api/v1/comments", json=create_payload)
    assert resp.status_code == 201
    created_data = resp.json()
    comment_id_str = created_data["id"]
    comment_id = uuid.UUID(comment_id_str)
    assert created_data["author"] == "john_doe"
    assert created_data["text"] == "Initial comment text"
    assert created_data["source_url"] == "https://example.com/topic/1"
    assert created_data["external_id"] == 1
    assert created_data["version"] == 1
    assert created_data["updated_at"] is None

    # 2. попытка создания дубликата с тем же source_url и external_id -> 409 conflict
    dup_resp = await client.post("/api/v1/comments", json=create_payload)
    assert dup_resp.status_code == 409

    # 3. получение комментария по uuid -> 200 ok
    get_resp = await client.get(f"/api/v1/comments/{comment_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == comment_id_str

    # 4. получение несуществующего комментария -> 404 not found
    random_uuid = uuid.uuid4()
    not_found_resp = await client.get(f"/api/v1/comments/{random_uuid}")
    assert not_found_resp.status_code == 404

    # 5. выборка по автору
    author_resp = await client.get("/api/v1/comments?author=john_doe")
    assert author_resp.status_code == 200
    author_data = author_resp.json()
    assert author_data["total"] == 1
    assert len(author_data["items"]) == 1
    assert author_data["items"][0]["author"] == "john_doe"

    # 6. выборка по source_url
    source_resp = await client.get(
        "/api/v1/comments?source_url=https://example.com/topic/1"
    )
    assert source_resp.status_code == 200
    source_data = source_resp.json()
    assert source_data["total"] == 1
    assert len(source_data["items"]) == 1
    assert (
        source_data["items"][0]["source_url"] == "https://example.com/topic/1"
    )

    # 7. попытка обновления с неверной версией -> 409 conflict occ
    conflict_resp = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"text": "Conflicting edit", "expected_version": 99},
    )
    assert conflict_resp.status_code == 409

    # 8. обновление комментария через patch -> 200 ok
    patch_resp = await client.patch(
        f"/api/v1/comments/{comment_id}",
        json={"text": "Updated content", "expected_version": 1},
    )
    assert patch_resp.status_code == 200
    updated_data = patch_resp.json()
    assert updated_data["text"] == "Updated content"
    assert updated_data["version"] == 2
    assert updated_data["updated_at"] is not None

    # 9. обновление комментария через put -> 200 ok
    put_resp = await client.put(
        f"/api/v1/comments/{comment_id}",
        json={"text": "Put updated content", "expected_version": 2},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["text"] == "Put updated content"
    assert put_resp.json()["version"] == 3

    # 10. обновление несуществующего комментария -> 404 not found
    patch_404 = await client.patch(
        f"/api/v1/comments/{random_uuid}",
        json={"text": "Updated content", "expected_version": 1},
    )
    assert patch_404.status_code == 404

    # 11. удаление комментария -> 204 no content
    del_resp = await client.delete(f"/api/v1/comments/{comment_id}")
    assert del_resp.status_code == 204

    # 12. повторное удаление -> 404 not found
    del_404 = await client.delete(f"/api/v1/comments/{comment_id}")
    assert del_404.status_code == 404


@pytest.mark.integration
async def test_comments_parse_endpoint(client: httpx.AsyncClient) -> None:
    # запрос на сбор комментариев со страницы
    parse_payload = {"url": "https://forum.example.com/topic/10"}
    resp = await client.post("/api/v1/comments/parse", json=parse_payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_parsed"] == 3
    assert data["saved_count"] == 3
    assert len(data["comments"]) == 3

    # проверка сохранения первого поста из фикстуры с валидным uuid
    c1_id = data["comments"][0]["id"]
    c1 = await client.get(f"/api/v1/comments/{c1_id}")
    assert c1.status_code == 200
    assert c1.json()["author"] == "tech_guru"
    assert c1.json()["external_id"] == 101
    assert c1.json()["source_url"] == "https://forum.example.com/topic/10"

    # повторный вызов парсинга (идемпотентность)
    resp2 = await client.post("/api/v1/comments/parse", json=parse_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total_parsed"] == 3
    assert data2["saved_count"] == 0


@pytest.mark.integration
async def test_comments_cross_source_same_external_id(
    client: httpx.AsyncClient,
) -> None:
    # создание комментария с external_id=101 из источника a
    res1 = await client.post(
        "/api/v1/comments",
        json={
            "author": "user_4pda",
            "text": "Comment on 4PDA",
            "source_url": "https://4pda.to/topic/1",
            "external_id": 101,
        },
    )
    assert res1.status_code == 201
    id1 = res1.json()["id"]

    # создание комментария с тем же external_id=101 из источника b
    res2 = await client.post(
        "/api/v1/comments",
        json={
            "author": "user_habr",
            "text": "Comment on Habr",
            "source_url": "https://habr.com/post/2",
            "external_id": 101,
        },
    )
    assert res2.status_code == 201
    id2 = res2.json()["id"]

    assert id1 != id2

    # получение обоих комментариев
    get1 = await client.get(f"/api/v1/comments/{id1}")
    get2 = await client.get(f"/api/v1/comments/{id2}")
    assert get1.status_code == 200
    assert get2.status_code == 200
    assert get1.json()["author"] == "user_4pda"
    assert get2.json()["author"] == "user_habr"


@pytest.mark.integration
async def test_comments_parse_invalid_url_scheme_returns_422(
    client: httpx.AsyncClient,
) -> None:
    # невалидная схема протокола (hts вместо http/https)
    invalid_payload = {"url": "hts://habr.com/ru/articles/750312/"}
    resp = await client.post("/api/v1/comments/parse", json=invalid_payload)

    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data
    # проверка ошибки валидации url
    assert any("url" in str(err) for err in data["detail"])
    assert any("url" in str(err) for err in data["detail"])


@pytest.mark.integration
async def test_comments_parse_unreachable_forum_returns_400() -> None:
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

    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")
    container = create_container(settings, FailingForumAppProvider())
    app = create_app(container=container)

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as c:
            resp = await c.post(
                "/api/v1/comments/parse",
                json={"url": "https://example.com/topic"},
            )
            assert resp.status_code == 400
            assert "HTTP status 500" in resp.json()["detail"]

    await container.close()


@pytest.mark.integration
async def test_comments_parse_connection_failure_returns_502() -> None:
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

    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")
    container = create_container(settings, ConnectErrorForumAppProvider())
    app = create_app(container=container)

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as c:
            resp = await c.post(
                "/api/v1/comments/parse",
                json={"url": "https://example.com/topic"},
            )
            assert resp.status_code == 502
            assert "Failed to fetch forum page" in resp.json()["detail"]

    await container.close()
