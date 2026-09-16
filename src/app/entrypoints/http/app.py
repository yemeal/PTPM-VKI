from typing import Annotated

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import ValidationError

from app.application.use_cases.register_user import (
    RegisterUserCommand,
    RegisterUserUseCase,
)
from app.domain.exceptions import LoginAlreadyTakenError
from app.entrypoints.http.dependencies import get_register_use_case
from app.entrypoints.http.schemas import UserRegisterRequest
from app.logging import setup_logging
from app.middleware import request_logging_middleware

setup_logging()


def create_app() -> FastAPI:
    """Фабрика создания экземпляра приложения FastAPI."""
    app = FastAPI()
    app.middleware("http")(request_logging_middleware)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> PlainTextResponse:
        message = exc.errors()[0]["msg"]
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        request.state.error_message = message
        return PlainTextResponse(
            content=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    @app.exception_handler(ValidationError)
    async def domain_validation_error_handler(
        request: Request,
        exc: ValidationError,
    ) -> PlainTextResponse:
        message = exc.errors()[0]["msg"]
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        request.state.error_message = message
        return PlainTextResponse(
            content=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    @app.exception_handler(LoginAlreadyTakenError)
    async def login_already_taken_handler(
        request: Request,
        exc: LoginAlreadyTakenError,
    ) -> PlainTextResponse:
        request.state.error_message = exc.message
        return PlainTextResponse(
            content=exc.message,
            status_code=status.HTTP_409_CONFLICT,
        )

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
        use_case.execute(
            RegisterUserCommand(login=data.login, password=data.password)
        )
        return PlainTextResponse(content="OK")

    return app


app = create_app()
