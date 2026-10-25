import ssl
from dataclasses import dataclass

import httpx

from app.infrastructure.exceptions import ForumFetchError

__all__ = [
    "DEFAULT_HEADERS",
    "FetchedPage",
    "create_forum_ssl_context",
    "fetch_url",
]

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": (
        '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"'
    ),
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass(frozen=True, slots=True)
class FetchedPage:
    """содержимое загруженной страницы или фида"""

    content: str
    content_type: str | None = None


def create_forum_ssl_context() -> ssl.SSLContext:
    """ssl-контекст с post_handshake_auth для обхода блокировок cloudflare"""
    ctx = ssl.create_default_context()
    ctx.post_handshake_auth = True
    return ctx


async def _send_request(client: httpx.AsyncClient, url: str) -> FetchedPage:
    """выполнение http get с трансляцией сетевых ошибок"""
    try:
        response = await client.get(url)
        response.raise_for_status()
        return FetchedPage(
            content=response.text,
            content_type=response.headers.get("Content-Type"),
        )
    except httpx.HTTPStatusError as err:
        raise ForumFetchError(
            f"Forum returned HTTP status {err.response.status_code} "
            f"for URL: {url}",
            status_code=400,
            upstream_status_code=err.response.status_code,
        ) from err
    except httpx.RequestError as err:
        raise ForumFetchError(
            f"Failed to fetch forum page from {url}: {err}",
            status_code=502,
        ) from err


async def fetch_url(
    url: str, client: httpx.AsyncClient | None = None
) -> FetchedPage:
    """загрузка страницы или фида с обработкой ssl и антифрода"""
    if client is not None:
        return await _send_request(client, url)

    ssl_ctx = create_forum_ssl_context()
    try:
        async with httpx.AsyncClient(
            verify=ssl_ctx,
            http2=False,
            headers=DEFAULT_HEADERS,
            timeout=15.0,
            follow_redirects=True,
        ) as default_client:
            return await _send_request(default_client, url)
    except ForumFetchError as err:
        # fallback к обычному ssl-контексту при кодах ошибок антифрода 403 и 419
        if err.upstream_status_code in (403, 419):
            async with httpx.AsyncClient(
                http2=False,
                headers=DEFAULT_HEADERS,
                timeout=15.0,
                follow_redirects=True,
            ) as fallback_client:
                return await _send_request(fallback_client, url)
        raise
