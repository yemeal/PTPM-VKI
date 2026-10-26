import pytest

from app.application.commands.comments.add.handler import AddCommentHandler
from app.application.commands.parse_page.handler import ParsePageHandler
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.application.ports.forum_parser import ForumParserProtocol
from app.core.settings import Settings
from app.infrastructure.di import create_container


@pytest.mark.integration
async def test_di_container_resolves_dependencies() -> None:
    settings = Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:")
    container = create_container(settings=settings)

    async with container() as request_container:
        repo = await request_container.get(CommentRepositoryProtocol)
        parser = await request_container.get(ForumParserProtocol)
        add_handler = await request_container.get(AddCommentHandler)
        parse_handler = await request_container.get(ParsePageHandler)

        assert repo is not None
        assert parser is not None
        assert add_handler is not None
        assert parse_handler is not None

    await container.close()
