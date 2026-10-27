from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

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
    """di-контейнер со sqlite в памяти и заглушкой форума"""
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
    """асинхронный клиент fastapi с контекстом lifespan для интеграционных тестов"""
    app = create_app(container=test_container)

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as ac:
            yield ac


@pytest.fixture
def client_factory() -> Callable[
    [Provider], AbstractAsyncContextManager[httpx.AsyncClient]
]:
    """фабрика клиентов с кастомными тестовыми провайдерами dishka"""

    @asynccontextmanager
    async def _factory(
        provider: Provider,
    ) -> AsyncGenerator[httpx.AsyncClient]:
        settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")
        container = create_container(settings, provider)
        app = create_app(container=container)
        try:
            async with app.router.lifespan_context(app):
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://test"
                ) as ac:
                    yield ac
        finally:
            await container.close()

    return _factory
