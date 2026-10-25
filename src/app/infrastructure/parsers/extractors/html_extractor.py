from datetime import datetime

from bs4 import BeautifulSoup, Tag

from app.domain.aggregates.comment import Comment
from app.infrastructure.parsers.utils import build_comment, clean_external_id

CONTAINER_SELECTORS: tuple[str, ...] = (
    "#comments",
    "#comment-box",
    ".comment-box",
    ".comments-area",
    "#comments-list",
    ".comment-list",
    ".comments",
    "table.comment-tree",
    "ol.comments",
    "#forumposts",
    ".thread-container",
)

POST_SELECTORS: tuple[str, ...] = (
    "[id^='comment-']",
    "[id^='post-']",
    "[id^='post_']",
    "[id^='msg_']",
    "[data-post]",
    "[data-id]",
    "[data-comment-id]",
    "article.post",
    "article.comment",
    "article.msg",
    ".post_wrapper",
    ".blockpost",
    "tr.comtr",
    ".message--post",
    ".cPost",
    "li.comments_subtree",
    "div.comment",
    ".post",
    ".comment",
)

AUTHOR_SELECTORS: tuple[str, ...] = (
    ".nickname",
    ".author",
    ".post-author",
    ".username",
    ".user-name",
    "[itemprop='author']",
    ".normalname",
    ".creator",
    ".hnuser",
    ".poster h4",
    "dt strong",
    ".message-name",
    ".cAuthorPane_author",
    "a.u-url",
    ".u-author",
)

AUTHOR_HREF_SELECTORS: tuple[str, ...] = (
    'a[href*="showuser="]',
    'a[href*="/user/"]',
    'a[href*="/member/"]',
    'a[href*="/u/"]',
    'a[href*="/people/"]',
    'a[href^="/~"]',
    'a[href*="action=profile"]',
)

POST_ID_LINK_SELECTORS: tuple[str, ...] = (
    'a[href*="#entry"]',
    'a[href*="#p"]',
    'a[href*="#post-"]',
    'a[href*="#comment"]',
    'a[href*="#msg"]',
)

CONTENT_SELECTORS: tuple[str, ...] = (
    ".content",
    ".post_body",
    ".postmsg",
    ".bbWrapper",
    ".commtext",
    "[itemprop='text']",
    ".post-content",
    ".text",
    ".message",
    ".comment-body",
    ".msg_body",
    ".msg-text",
    ".comment_text",
    ".post .inner",
    ".messageText",
    ".messageContent",
    ".cPost_contentWrap",
)

COMBINED_POSTS_SELECTOR: str = ", ".join(POST_SELECTORS)
COMBINED_POST_ID_LINK_SELECTOR: str = ", ".join(POST_ID_LINK_SELECTORS)
COMBINED_AUTHOR_SELECTOR: str = ", ".join(AUTHOR_SELECTORS)
COMBINED_AUTHOR_HREF_SELECTOR: str = ", ".join(AUTHOR_HREF_SELECTORS)
COMBINED_CONTENT_SELECTOR: str = ", ".join(CONTENT_SELECTORS)


def is_inside_sidebar_or_nav(elem: Tag) -> bool:
    """проверка нахождения элемента в сайдбаре, навигации или футере"""
    for parent in elem.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name in ("aside", "nav", "footer", "header"):
            return True
        parent_classes = parent.get("class")
        class_str = (
            " ".join(parent_classes).lower()
            if isinstance(parent_classes, list)
            else str(parent_classes or "").lower()
        )
        if any(
            term in class_str
            for term in (
                "sidebar",
                "related",
                "recommend",
                "more-box",
                "widget",
            )
        ):
            return True
    return False


def is_inside_quote(elem: Tag) -> bool:
    """проверка нахождения элемента внутри цитаты или кода"""
    for parent in elem.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name in ("blockquote", "code"):
            return True
        parent_classes = parent.get("class")
        class_str = (
            " ".join(parent_classes).lower()
            if isinstance(parent_classes, list)
            else str(parent_classes or "").lower()
        )
        if any(
            term in class_str
            for term in (
                "quote",
                "bbcodequote",
                "codeheader",
                "quoteheader",
                "citation",
            )
        ):
            return True
    return False


class HtmlForumExtractor:
    """извлечение комментариев из html-разметки форумов по эвристикам"""

    @staticmethod
    def find_comments_container(
        soup: BeautifulSoup,
    ) -> Tag | BeautifulSoup:
        """поиск контейнера комментариев на странице"""
        for sel in CONTAINER_SELECTORS:
            container = soup.select_one(sel)
            if container is not None:
                return container
        return soup

    def extract(
        self,
        soup: BeautifulSoup,
        source_url: str,
        now: datetime,
    ) -> list[Comment]:
        """извлечение списка валидных комментариев из html"""
        target_container = self.find_comments_container(soup)
        post_elements = target_container.select(COMBINED_POSTS_SELECTOR)

        comments: list[Comment] = []
        seen_ids: set[int | str] = set()

        for post in post_elements:
            comment = self.extract_comment(
                post, source_url=source_url, now=now
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
        post: Tag,
        source_url: str,
        now: datetime,
    ) -> Comment | None:
        """извлечение одного комментария из блока поста"""
        if is_inside_sidebar_or_nav(post):
            return None

        comment_id = self._extract_post_id(post)
        if comment_id is None:
            return None

        author_text = self._extract_author(post)
        if not author_text:
            return None

        message_text = self._extract_message_text(post)
        if not message_text:
            return None

        return build_comment(
            source_url=source_url,
            external_id=comment_id,
            author=author_text,
            text=message_text,
            created_at=now,
        )

    def _extract_post_id(self, post: Tag) -> int | str | None:
        raw_id = (
            post.get("data-post")
            or post.get("data-id")
            or post.get("data-comment-id")
            or post.get("id")
        )
        if not raw_id:
            anchor = post.select_one(COMBINED_POST_ID_LINK_SELECTOR)
            if anchor:
                raw_id = anchor.get("href", "")
        return clean_external_id(raw_id)

    def _extract_author(self, post: Tag) -> str | None:
        for candidate in post.select(COMBINED_AUTHOR_SELECTOR):
            if not is_inside_quote(candidate) and candidate.get_text(
                strip=True
            ):
                return candidate.get_text(strip=True)

        for candidate in post.select(COMBINED_AUTHOR_HREF_SELECTOR):
            if not is_inside_quote(candidate) and candidate.get_text(
                strip=True
            ):
                return candidate.get_text(strip=True)

        return None

    def _extract_message_text(self, post: Tag) -> str | None:
        content_elem = post.select_one(COMBINED_CONTENT_SELECTOR)
        if not content_elem:
            content_elem = post.select_one("p")
        if not content_elem:
            return None
        return content_elem.get_text(separator="\n", strip=True) or None
