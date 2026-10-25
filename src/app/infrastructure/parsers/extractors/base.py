from datetime import datetime
from typing import Protocol

from bs4 import BeautifulSoup

from app.domain.aggregates.comment import Comment


class ForumExtractor(Protocol):
    """протокол извлечения комментариев из документа beautifulsoup"""

    def extract(
        self,
        soup: BeautifulSoup,
        source_url: str,
        now: datetime,
    ) -> list[Comment]:
        """извлечение комментариев из распарсенного документа"""
        ...
