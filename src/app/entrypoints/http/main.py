from typing import Annotated

from fastapi import Depends, FastAPI, status
from fastapi.responses import PlainTextResponse, RedirectResponse

from app.application.use_cases.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from app.entrypoints.http.dependencies import get_register_use_case
from app.entrypoints.http.exception_handlers import setup_exception_handlers
from app.entrypoints.http.middleware import request_logging_middleware
from app.entrypoints.http.schemas import UserRegisterRequest
from app.logging import setup_logging

setup_logging()


def create_app() -> FastAPI:
    """Фабрика создания экземпляра приложения FastAPI."""
    app = FastAPI()
    app.middleware("http")(request_logging_middleware)
    setup_exception_handlers(app)

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(
            "/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT
        )

    @app.post("/v1/auth/register", status_code=status.HTTP_200_OK)
    async def register(
        data: UserRegisterRequest,
        use_case: Annotated[
            RegisterUserUseCase, Depends(get_register_use_case)
        ],
    ) -> PlainTextResponse:
        await use_case.execute(
            RegisterUserCommand(login=data.login, password=data.password)
        )
        return PlainTextResponse(content="OK")

    return app


app = create_app()
