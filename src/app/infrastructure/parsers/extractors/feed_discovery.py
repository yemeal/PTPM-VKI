from urllib.parse import urljoin

from bs4 import BeautifulSoup


def is_xml_content(content: str, content_type: str | None = None) -> bool:
    """проверка содержимого на xml или ленту новостей"""
    if content_type:
        ct = content_type.lower()
        if any(term in ct for term in ("xml", "rss", "atom")):
            return True
        if "html" in ct:
            return False

    stripped = content.lstrip()[:500].lower()
    return (
        stripped.startswith("<?xml")
        or "<rss" in stripped
        or "<feed" in stripped
    )


def find_feed_url(soup: BeautifulSoup, base_url: str) -> str | None:
    """поиск ссылки на rss или atom через автодискавери"""
    for link in soup.find_all("link"):
        rel = link.get("rel")
        type_attr = link.get("type")
        href = link.get("href")
        if not href or not rel or not type_attr:
            continue
        rel_str = " ".join(rel) if isinstance(rel, list) else str(rel)
        type_str = str(type_attr).lower()
        if "alternate" in rel_str and any(
            f in type_str for f in ("rss", "atom", "xml")
        ):
            return urljoin(base_url, str(href))
    return None
