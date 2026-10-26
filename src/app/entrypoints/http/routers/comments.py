import uuid
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Query, status

from app.application.commands.comments.add.command import AddCommentCommand
from app.application.commands.comments.add.handler import AddCommentHandler
from app.application.commands.comments.delete.command import (
    DeleteCommentCommand,
)
from app.application.commands.comments.delete.handler import (
    DeleteCommentHandler,
)
from app.application.commands.comments.update.command import (
    UpdateCommentCommand,
)
from app.application.commands.comments.update.handler import (
    UpdateCommentHandler,
)
from app.application.commands.parse_page.command import ParsePageCommand
from app.application.commands.parse_page.handler import ParsePageHandler
from app.application.pagination import PaginationParams
from app.application.queries.comments.get.handler import (
    GetCommentQueryHandler,
)
from app.application.queries.comments.get.query import GetCommentQuery
from app.application.queries.comments.list.handler import (
    GetCommentsQueryHandler,
)
from app.application.queries.comments.list.query import GetCommentsQuery
from app.entrypoints.http.schemas import (
    AddCommentRequest,
    CommentResponse,
    PaginatedResponse,
    ParsePageRequest,
    ParsePageResponse,
    UpdateCommentRequest,
)

router = APIRouter(prefix="/api/v1/comments", tags=["Comments"])


@router.post(
    "/parse",
    response_model=ParsePageResponse,
    status_code=status.HTTP_200_OK,
    summary="Собрать комментарии с веб-страницы по URL",
)
@inject
async def parse_page(
    body: ParsePageRequest,
    handler: FromDishka[ParsePageHandler],
) -> ParsePageResponse:
    result = await handler(ParsePageCommand(url=str(body.url)))
    return ParsePageResponse(
        total_parsed=result.total_parsed,
        saved_count=result.saved_count,
        comments=[CommentResponse.from_dto(c) for c in result.comments],
    )


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый комментарий",
)
@inject
async def add_comment(
    body: AddCommentRequest,
    handler: FromDishka[AddCommentHandler],
) -> CommentResponse:
    comment_dto = await handler(
        AddCommentCommand(
            author=body.author,
            text=body.text,
            source_url=body.source_url,
            external_id=body.external_id,
        )
    )
    return CommentResponse.from_dto(comment_dto)


@router.get(
    "/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить комментарий по ID",
)
@inject
async def get_comment(
    comment_id: uuid.UUID,
    handler: FromDishka[GetCommentQueryHandler],
) -> CommentResponse:
    comment_dto = await handler(GetCommentQuery(id=comment_id))
    return CommentResponse.from_dto(comment_dto)


@router.get(
    "",
    response_model=PaginatedResponse[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Получить комментарии по имени автора или источнику с пагинацией",
)
@inject
async def get_comments(
    handler: FromDishka[GetCommentsQueryHandler],
    author: Annotated[
        str | None, Query(description="Фильтр по имени автора")
    ] = None,
    source_url: Annotated[
        str | None, Query(description="Фильтр по источнику URL")
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Количество элементов на странице"),
    ] = 50,
    offset: Annotated[int, Query(ge=0, description="Смещение выборки")] = 0,
) -> PaginatedResponse[CommentResponse]:
    result = await handler(
        GetCommentsQuery(
            author=author,
            source_url=source_url,
            pagination=PaginationParams(limit=limit, offset=offset),
        )
    )
    return PaginatedResponse[CommentResponse](
        items=[CommentResponse.from_dto(c) for c in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить текст комментария (PATCH)",
)
@router.put(
    "/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Обновить текст комментария (PUT)",
)
@inject
async def update_comment(
    comment_id: uuid.UUID,
    body: UpdateCommentRequest,
    handler: FromDishka[UpdateCommentHandler],
) -> CommentResponse:
    comment_dto = await handler(
        UpdateCommentCommand(
            id=comment_id,
            text=body.text,
            expected_version=body.expected_version,
        )
    )
    return CommentResponse.from_dto(comment_dto)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить комментарий по ID",
)
@inject
async def delete_comment(
    comment_id: uuid.UUID,
    handler: FromDishka[DeleteCommentHandler],
) -> None:
    await handler(DeleteCommentCommand(id=comment_id))
