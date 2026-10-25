from pydantic import BaseModel, ConfigDict

from app.application.dtos import CommentDTO


class ParsePageResult(BaseModel):
    """результат парсинга страницы форума"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_parsed: int
    saved_count: int
    comments: list[CommentDTO]
