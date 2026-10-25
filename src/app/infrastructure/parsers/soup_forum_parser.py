import httpx
from bs4 import BeautifulSoup

from app.domain.aggregates.comment import Comment
from app.domain.clock import Clock, utc_now
from app.infrastructure.parsers.extractors import (
    HtmlForumExtractor,
    XmlFeedExtractor,
    find_feed_url,
    is_xml_content,
)
from app.infrastructure.parsers.http_client import fetch_url

__all__ = ["BeautifulSoupForumParser"]


class BeautifulSoupForumParser:
    """парсер страниц форумов и xml лент"""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._client = client
        self._clock = clock
        self._html_extractor = HtmlForumExtractor()
        self._xml_extractor = XmlFeedExtractor()

    async def parse_page(
        self,
        url: str,
        visited_urls: set[str] | None = None,
        original_url: str | None = None,
    ) -> list[Comment]:
        """загрузка страницы или фида по сети и парсинг комментариев"""
        visited = visited_urls if visited_urls is not None else set()
        if url in visited or len(visited) >= 2:
            return []  # защита от циклической рекурсии
        visited.add(url)

        target_source = original_url or url
        page = await fetch_url(url, self._client)

        comments = self.parse_content(
            page.content,
            content_type=page.content_type,
            source_url=target_source,
        )
        if not comments and not is_xml_content(
            page.content, page.content_type
        ):
            soup = BeautifulSoup(page.content, "lxml")
            feed_url = find_feed_url(soup, base_url=url)
            if feed_url and feed_url != url:
                return await self.parse_page(
                    feed_url, visited_urls=visited, original_url=target_source
                )

        return comments

    def parse_content(
        self,
        content: str,
        content_type: str | None = None,
        source_url: str = "",
    ) -> list[Comment]:
        """разбор html или xml контента по эвристикам"""
        if not content or not content.strip():
            return []

        is_xml = is_xml_content(content, content_type)
        parser_type = "xml" if is_xml else "lxml"
        soup = BeautifulSoup(content, features=parser_type)

        now = self._clock()
        if is_xml:
            return self._xml_extractor.extract(
                soup, source_url=source_url, now=now
            )
        return self._html_extractor.extract(
            soup, source_url=source_url, now=now
        )
