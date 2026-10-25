import uuid
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from app.infrastructure.exceptions import ForumFetchError
from app.infrastructure.parsers.soup_forum_parser import (
    BeautifulSoupForumParser,
)


@pytest.fixture
def forum_html() -> str:
    fixture_path = Path(__file__).parents[2] / "fixtures" / "forum_thread.html"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def parser(now: datetime) -> BeautifulSoupForumParser:
    return BeautifulSoupForumParser(clock=lambda: now)


def test_parse_html_fixture(
    forum_html: str, parser: BeautifulSoupForumParser, now: datetime
) -> None:
    comments = parser.parse_content(forum_html)

    assert len(comments) == 3

    c1 = comments[0]
    assert isinstance(c1.id, uuid.UUID)
    assert c1.external_id == 101
    assert c1.author.value == "tech_guru"
    assert "Welcome to the discussion forum!" in c1.text.value
    assert c1.created_at == now

    c2 = comments[1]
    assert isinstance(c2.id, uuid.UUID)
    assert c2.id != c1.id
    assert c2.external_id == 102
    assert c2.author.value == "code_ninja"
    assert "Great topic." in c2.text.value

    c3 = comments[2]
    assert isinstance(c3.id, uuid.UUID)
    assert c3.external_id == 103
    assert c3.author.value == "alex_e"
    assert "Testing parser and storage service." in c3.text.value


async def test_parse_page_with_mock_transport(
    forum_html: str, now: datetime
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://forum.example.com/threads/123"
        return httpx.Response(200, text=forum_html)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        comments = await parser.parse_page(
            "https://forum.example.com/threads/123"
        )

        assert len(comments) == 3
        assert isinstance(comments[0].id, uuid.UUID)
        assert comments[0].external_id == 101
        assert (
            comments[0].source_url == "https://forum.example.com/threads/123"
        )


def test_parse_html_skips_invalid_elements(
    parser: BeautifulSoupForumParser,
) -> None:
    html = """
    <div>
        <!-- Нет ID -->
        <article class="post">
            <span class="author">john</span>
            <div class="content">No ID here</div>
        </article>
        <!-- Нет автора -->
        <article class="post" id="post-201">
            <div class="content">No author here</div>
        </article>
        <!-- Пустой контент -->
        <article class="post" id="post-202">
            <span class="author">john</span>
            <div class="content">   </div>
        </article>
        <!-- Валидный -->
        <article class="post" id="post-203">
            <span class="author">valid_user</span>
            <div class="content">Valid comment</div>
        </article>
    </div>
    """
    comments = parser.parse_content(html)

    assert len(comments) == 1
    assert comments[0].external_id == 203
    assert comments[0].author.value == "valid_user"
    assert comments[0].text.value == "Valid comment"


def test_parse_html_empty_string(parser: BeautifulSoupForumParser) -> None:
    comments = parser.parse_content("")
    assert comments == []


async def test_parse_page_raises_on_http_error(now: datetime) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="Not Found")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        with pytest.raises(ForumFetchError) as exc_info:
            await parser.parse_page("https://forum.example.com/not-found")
        assert "HTTP status 404" in str(exc_info.value)


async def test_parse_page_raises_on_request_error(now: datetime) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        with pytest.raises(ForumFetchError) as exc_info:
            await parser.parse_page("https://forum.example.com/unreachable")
        assert "Failed to fetch forum page" in str(exc_info.value)


def test_parse_xml_rss_feed(parser: BeautifulSoupForumParser) -> None:
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
      <channel>
        <title>Article Comments Feed</title>
        <item>
          <title>Comment 1 by Alice</title>
          <guid isPermaLink="true">https://example.com/articles/123/#comment_8801</guid>
          <dc:creator><![CDATA[alice_dev]]></dc:creator>
          <description><![CDATA[<p>First RSS comment text!</p>]]></description>
        </item>
        <item>
          <title>Comment 2 by Bob</title>
          <link>https://example.com/articles/123/#comment_8802</link>
          <author>bob_smith</author>
          <description><![CDATA[<p>Second RSS comment text with <b>html</b>.</p>]]></description>
        </item>
        <item>
          <title>26.10.2026 12:00:00</title>
          <guid>https://example.com/articles/123/#comment_8803</guid>
          <description><![CDATA[Anonymous author comment]]></description>
        </item>
      </channel>
    </rss>
    """
    comments = parser.parse_content(xml_data)

    assert len(comments) == 3
    assert comments[0].external_id == 8801
    assert comments[0].author.value == "alice_dev"
    assert "First RSS comment text!" in comments[0].text.value

    assert comments[1].external_id == 8802
    assert comments[1].author.value == "bob_smith"
    assert "Second RSS comment text with html." in comments[1].text.value

    assert comments[2].external_id == 8803
    assert comments[2].author.value == "Anonymous"
    assert "Anonymous author comment" in comments[2].text.value


def test_parse_4pda_html_structure(parser: BeautifulSoupForumParser) -> None:
    html = """
    <div class="comment-box" id="comments">
        <ul class="comment-list">
            <li data-author-id="100">
                <a class="link-anchor" id="comment99991"></a>
                <div id="comment-99991">
                    <span class="nickname">pro_user</span>
                    <div class="content">Comment from 4PDA topic</div>
                </div>
            </li>
        </ul>
    </div>
    """
    comments = parser.parse_content(html)

    assert len(comments) == 1
    assert comments[0].external_id == 99991
    assert comments[0].author.value == "pro_user"
    assert comments[0].text.value == "Comment from 4PDA topic"


async def test_parse_page_with_httpx_client(
    forum_html: str, now: datetime
) -> None:
    transport = httpx.MockTransport(
        lambda _req: httpx.Response(200, text=forum_html)
    )
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        comments = await parser.parse_page(
            "https://forum.example.com/threads/123"
        )

    assert len(comments) == 3
    assert comments[0].external_id == 101
    assert comments[0].source_url == "https://forum.example.com/threads/123"


async def test_parse_page_default_client(
    forum_html: str, now: datetime, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_get(
        _self: httpx.AsyncClient, url: str, **_kwargs: object
    ) -> httpx.Response:
        req = httpx.Request("GET", url)
        return httpx.Response(200, text=forum_html, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    parser = BeautifulSoupForumParser(client=None, clock=lambda: now)
    comments = await parser.parse_page("https://forum.example.com/topic/1")
    assert len(comments) == 3


async def test_parse_page_raises_on_http_status_error_status_code(
    now: datetime,
) -> None:
    transport = httpx.MockTransport(
        lambda _req: httpx.Response(403, text="Forbidden")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        with pytest.raises(ForumFetchError) as exc_info:
            await parser.parse_page("https://forum.example.com/blocked")
        assert "HTTP status 403" in str(exc_info.value)
        assert exc_info.value.status_code == 400


async def test_parse_page_raises_on_request_error_status_code(
    now: datetime,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        with pytest.raises(ForumFetchError) as exc_info:
            await parser.parse_page("https://forum.example.com/refused")
        assert "Failed to fetch forum page" in str(exc_info.value)
        assert exc_info.value.status_code == 502


async def test_parse_page_follows_rss_auto_discovery(now: datetime) -> None:
    html_page = """<!DOCTYPE html>
    <html>
      <head>
        <title>SPA Article</title>
        <link rel="alternate" type="application/rss+xml" href="/rss/comments/123" />
      </head>
      <body>
        <div id="publication-comments"></div>
      </body>
    </html>
    """
    rss_feed = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <item>
          <guid>https://example.com/#comment_777</guid>
          <author>discovered_author</author>
          <description>Discovered comment text</description>
        </item>
      </channel>
    </rss>
    """
    call_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if "/rss/" in str(request.url):
            return httpx.Response(
                200,
                text=rss_feed,
                headers={"Content-Type": "application/rss+xml"},
            )
        return httpx.Response(
            200, text=html_page, headers={"Content-Type": "text/html"}
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        comments = await parser.parse_page("https://example.com/articles/123")

    assert len(comments) == 1
    assert comments[0].external_id == 777
    assert comments[0].author.value == "discovered_author"
    assert comments[0].text.value == "Discovered comment text"
    assert call_count == 2


async def test_parse_page_cyclic_rss_redirect_protection(
    now: datetime,
) -> None:
    page_a = """
    <html>
      <head>
        <link rel="alternate" type="application/rss+xml" href="https://example.com/page_b" />
      </head>
      <body><div>No comments</div></body>
    </html>
    """
    page_b = """
    <html>
      <head>
        <link rel="alternate" type="application/rss+xml" href="https://example.com/page_a" />
      </head>
      <body><div>No comments</div></body>
    </html>
    """
    call_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        url = str(request.url)
        if "page_b" in url:
            return httpx.Response(
                200, text=page_b, headers={"Content-Type": "text/html"}
            )
        return httpx.Response(
            200, text=page_a, headers={"Content-Type": "text/html"}
        )

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        comments = await parser.parse_page("https://example.com/page_a")

    assert comments == []
    assert call_count <= 2


def test_parse_html_logs_malformed_comment(
    caplog: pytest.LogCaptureFixture, parser: BeautifulSoupForumParser
) -> None:
    from app.domain.limits import MAX_USERNAME_LENGTH

    too_long = "u" * (MAX_USERNAME_LENGTH + 10)
    html = f"""
    <article class="post" id="post-999">
        <span class="author">{too_long}</span>
        <div class="content">Comment content</div>
    </article>
    """
    with caplog.at_level("WARNING"):
        comments = parser.parse_content(html)
    assert comments == []
    assert "Skipping malformed comment" in caplog.text


def test_parse_html_alphanumeric_external_id(
    parser: BeautifulSoupForumParser,
) -> None:
    html = """
    <div class="comment" id="c_oy3w19">
        <a class="u-author" href="/~mhanberg">mhanberg</a>
        <div class="comment_text">Discussion text on Lobsters</div>
    </div>
    """
    comments = parser.parse_content(html)

    assert len(comments) == 1
    assert comments[0].external_id == "oy3w19"
    assert comments[0].author.value == "mhanberg"
    assert comments[0].text.value == "Discussion text on Lobsters"


def test_parse_html_ignores_author_inside_quote(
    parser: BeautifulSoupForumParser,
) -> None:
    html = """
    <div class="post_wrapper" id="msg_12345">
        <div class="poster">
            <h4>RealAuthor</h4>
        </div>
        <div class="post">
            <div class="inner">
                <div class="quoteheader">
                    <a href="/user/quoted_user" class="author">Quote by QuotedUser</a>
                </div>
                <blockquote>Quoted text here</blockquote>
                Actual reply message by RealAuthor.
            </div>
        </div>
    </div>
    """
    comments = parser.parse_content(html)

    assert len(comments) == 1
    assert comments[0].external_id == 12345
    assert comments[0].author.value == "RealAuthor"
    assert "Actual reply message by RealAuthor" in comments[0].text.value


def test_parse_html_truncates_oversized_text(
    parser: BeautifulSoupForumParser,
) -> None:
    from app.domain.limits import MAX_MESSAGE_TEXT_LENGTH

    oversized = "A" * (MAX_MESSAGE_TEXT_LENGTH + 500)
    html = f"""
    <article class="post" id="post-888">
        <span class="author">super_writer</span>
        <div class="content">{oversized}</div>
    </article>
    """
    comments = parser.parse_content(html)

    assert len(comments) == 1
    assert comments[0].external_id == 888
    assert comments[0].author.value == "super_writer"
    assert comments[0].text.value.endswith("... [truncated]")
    assert len(comments[0].text.value) <= MAX_MESSAGE_TEXT_LENGTH


def test_parse_lor_html_structure(
    parser: BeautifulSoupForumParser,
) -> None:
    html = """
    <article class="msg" id="comment-18408905">
        <div class="msg-container">
            <div class="userpic">
                <a href="/people/MoldAndLimeHoney/profile">MoldAndLimeHoney</a>
            </div>
            <div class="msg_body">
                <p>Hello from Linux.org.ru forum comment!</p>
            </div>
        </div>
    </article>
    """
    comments = parser.parse_content(html)

    assert len(comments) == 1
    assert comments[0].external_id == 18408905
    assert comments[0].author.value == "MoldAndLimeHoney"
    assert "Hello from Linux.org.ru forum comment!" in comments[0].text.value


def test_parse_html_ignores_sidebar_and_news_articles(
    parser: BeautifulSoupForumParser,
) -> None:
    html = """
    <div>
        <div id="comments">
            <div id="comment-101">
                <span class="nickname">real_user</span>
                <div class="content">Real discussion comment</div>
            </div>
        </div>
        <aside class="sidebar">
            <article class="post" id="news-999">
                <span class="author">News</span>
                <p>Related article teaser text</p>
            </article>
        </aside>
    </div>
    """
    comments = parser.parse_content(html)

    assert len(comments) == 1
    assert comments[0].external_id == 101
    assert comments[0].author.value == "real_user"
    assert comments[0].text.value == "Real discussion comment"


async def test_forum_fetch_error_preserves_upstream_status_code(
    now: datetime,
) -> None:
    transport = httpx.MockTransport(
        lambda _req: httpx.Response(403, text="Forbidden")
    )
    async with httpx.AsyncClient(transport=transport) as client:
        parser = BeautifulSoupForumParser(client=client, clock=lambda: now)
        with pytest.raises(ForumFetchError) as exc_info:
            await parser.parse_page("https://forum.example.com/blocked")
        assert exc_info.value.status_code == 400
        assert exc_info.value.upstream_status_code == 403


async def test_parse_page_fallback_client_on_403(
    forum_html: str, now: datetime, monkeypatch: pytest.MonkeyPatch
) -> None:
    attempts: list[dict[str, object]] = []

    async def mock_get(
        self: httpx.AsyncClient, url: str, **_kwargs: object
    ) -> httpx.Response:
        req = httpx.Request("GET", url)
        attempts.append({"verify": self._transport, "headers": self.headers})
        if len(attempts) == 1:
            return httpx.Response(
                403, text="Forbidden by Cloudflare", request=req
            )
        return httpx.Response(200, text=forum_html, request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    parser = BeautifulSoupForumParser(client=None, clock=lambda: now)
    comments = await parser.parse_page("https://forum.example.com/topic/1")

    assert len(attempts) == 2
    assert len(comments) == 3
