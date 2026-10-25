import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from app.domain.aggregates.comment import Comment
from app.infrastructure.parsers.utils import build_comment, clean_external_id

DATE_OR_NUMBER_PATTERN: re.Pattern[str] = re.compile(r"^[\d.:\s]+$")
QUOTE_HEADER_PATTERN: re.Pattern[str] = re.compile(r"quoteheader|codeheader")


def sanitize_cdata_html(raw_html: str) -> str:
    """очистка html-разметки и цитат внутри cdata фида"""
    desc_soup = BeautifulSoup(raw_html, "lxml")
    for qh in desc_soup.find_all(class_=QUOTE_HEADER_PATTERN):
        qh.decompose()
    for br in desc_soup.find_all("br"):
        br.replace_with("\n")
    for p in desc_soup.find_all(["p", "div", "li"]):
        p.append("\n")
    lines = [
        line.strip()
        for line in desc_soup.get_text().splitlines()
        if line.strip()
    ]
    return "\n".join(lines)


class XmlFeedExtractor:
    """извлечение комментариев из rss и atom лент"""

    def extract(
        self,
        soup: BeautifulSoup,
        source_url: str,
        now: datetime,
    ) -> list[Comment]:
        """извлечение списка валидных комментариев из xml-фида"""
        items = soup.find_all(["item", "entry"])
        comments: list[Comment] = []
        seen_ids: set[int | str] = set()

        for item in items:
            comment = self.extract_comment(
                item, source_url=source_url, now=now
            )
            if comment is not None:
                if comment.external_id is not None:
                    if comment.external_id in seen_ids:
                        continue
                    seen_ids.add(comment.external_id)
                comments.append(comment)

        return comments

    def extract_comment(
        self,
        item: Tag,
        source_url: str,
        now: datetime,
    ) -> Comment | None:
        """извлечение комментария из элемента item или entry"""
        comment_id = self._extract_item_id(item)
        if comment_id is None:
            return None

        author_text = self._extract_author(item)
        message_text = self._extract_message_text(item)
        if not message_text:
            return None

        return build_comment(
            source_url=source_url,
            external_id=comment_id,
            author=author_text,
            text=message_text,
            created_at=now,
        )

    def _extract_item_id(self, item: Tag) -> int | str | None:
        raw_id = None
        guid_elem = item.find(["guid", "id"])
        if guid_elem:
            raw_id = guid_elem.get_text(strip=True)
        elif (link := item.find("link")) is not None:
            raw_id = link.get("href") or link.get_text(strip=True)
        return clean_external_id(raw_id)

    def _extract_author(self, item: Tag) -> str:
        author_elem = item.find(["dc:creator", "creator", "author"])
        if author_elem:
            name_elem = author_elem.find("name")
            text = (
                name_elem.get_text(strip=True)
                if name_elem
                else author_elem.get_text(strip=True)
            )
            if text:
                return text

        title_elem = item.find("title")
        if title_elem:
            parts = title_elem.get_text(strip=True).split()
            if parts and not DATE_OR_NUMBER_PATTERN.match(parts[-1]):
                return parts[-1]

        return "Anonymous"

    def _extract_message_text(self, item: Tag) -> str | None:
        content_elem = item.find(
            ["description", "content:encoded", "content", "summary"]
        )
        if not content_elem:
            return None

        sanitized = sanitize_cdata_html(content_elem.get_text())
        return sanitized or None
