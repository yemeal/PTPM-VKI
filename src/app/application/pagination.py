from pydantic import BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    """параметры пагинации списков"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class PaginatedResult[T](BaseModel):
    """результат выборки с пагинацией"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    total: int
    limit: int
    offset: int
