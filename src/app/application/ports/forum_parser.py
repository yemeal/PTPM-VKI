from typing import Protocol

from app.domain.aggregates.comment import Comment


class ForumParserProtocol(Protocol):
    """порт парсера страниц форума"""

    async def parse_page(
        self, url: str, visited_urls: set[str] | None = None
    ) -> list[Comment]:
        """загрузка и парсинг страницы по url"""
        ...
