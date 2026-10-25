from app.application.commands.parse_page.command import ParsePageCommand
from app.application.commands.parse_page.result import ParsePageResult
from app.application.dtos import CommentDTO
from app.application.ports.comment_repository import (
    CommentRepositoryProtocol,
)
from app.application.ports.forum_parser import ForumParserProtocol
from app.domain.aggregates.comment import Comment
from app.domain.clock import Clock, utc_now


class ParsePageHandler:
    """обработчик парсинга страницы и сохранения комментариев"""

    def __init__(
        self,
        parser: ForumParserProtocol,
        comments: CommentRepositoryProtocol,
        clock: Clock = utc_now,
    ) -> None:
        self._parser = parser
        self._comments = comments
        self._clock = clock

    async def __call__(self, command: ParsePageCommand) -> ParsePageResult:
        parsed_comments = await self._parser.parse_page(command.url)
        saved_count = 0
        persisted_comments: list[Comment] = []

        external_ids = [
            c.external_id for c in parsed_comments if c.external_id is not None
        ]
        existing_map = (
            await self._comments.find_by_source_and_external_ids(
                command.url, external_ids
            )
            if external_ids
            else {}
        )

        for parsed in parsed_comments:
            if (
                parsed.external_id is not None
                and parsed.external_id in existing_map
            ):
                existing = existing_map[parsed.external_id]
                if existing.edit_text(parsed.text, now=self._clock()):
                    await self._comments.update(existing)
                    saved_count += 1
                persisted_comments.append(existing)
            else:
                await self._comments.add(parsed)
                saved_count += 1
                persisted_comments.append(parsed)

        return ParsePageResult(
            total_parsed=len(parsed_comments),
            saved_count=saved_count,
            comments=[CommentDTO.from_domain(c) for c in persisted_comments],
        )
