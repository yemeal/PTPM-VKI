from collections.abc import AsyncGenerator

import httpx
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.application.ports.forum_parser import ForumParserProtocol
from app.domain.clock import Clock
from app.infrastructure.parsers.http_client import (
    DEFAULT_HEADERS,
    create_forum_ssl_context,
)
from app.infrastructure.parsers.soup_forum_parser import (
    BeautifulSoupForumParser,
)
from app.infrastructure.repositories.sqlalchemy_comment_repo import (
    SqlAlchemyCommentRepository,
)


class InfrastructureProvider(Provider):
    """провайдер инфраструктурных адаптеров, сетевых клиентов и репозиториев"""

    @provide(scope=Scope.APP)
    async def provide_http_client(self) -> AsyncGenerator[httpx.AsyncClient]:
        ssl_ctx = create_forum_ssl_context()
        async with httpx.AsyncClient(
            verify=ssl_ctx,
            http2=False,
            headers=DEFAULT_HEADERS,
            timeout=15.0,
            follow_redirects=True,
        ) as client:
            yield client

    @provide(scope=Scope.REQUEST)
    def provide_comment_repo(
        self, session: AsyncSession
    ) -> CommentRepositoryProtocol:
        return SqlAlchemyCommentRepository(session=session)

    @provide(scope=Scope.REQUEST)
    def provide_forum_parser(
        self, client: httpx.AsyncClient, clock: Clock
    ) -> ForumParserProtocol:
        return BeautifulSoupForumParser(client=client, clock=clock)
