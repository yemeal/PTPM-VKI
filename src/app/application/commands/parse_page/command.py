from app.application.commands.base import BaseCommand
from app.application.commands.parse_page.result import ParsePageResult


class ParsePageCommand(BaseCommand[ParsePageResult]):
    """команда парсинга страницы форума по url"""

    url: str
