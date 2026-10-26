from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions.base import DomainError
from app.domain.exceptions.comments import (
    CommentAlreadyExistsError,
    CommentNotFoundError,
    ConcurrencyError,
)
from app.infrastructure.exceptions import ForumFetchError


def register_exception_handlers(app: FastAPI) -> None:
    """регистрация обработчиков исключений fastapi"""

    @app.exception_handler(ForumFetchError)
    async def forum_fetch_error_handler(
        _request: Request, exc: ForumFetchError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc)},
        )

    @app.exception_handler(CommentNotFoundError)
    async def comment_not_found_handler(
        _request: Request, exc: CommentNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(CommentAlreadyExistsError)
    async def comment_already_exists_handler(
        _request: Request, exc: CommentAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ConcurrencyError)
    async def concurrency_error_handler(
        _request: Request, exc: ConcurrencyError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        _request: Request, exc: DomainError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )
