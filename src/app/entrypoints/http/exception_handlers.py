from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError

from app.domain.exceptions import (
    DomainValidationError,
    LoginAlreadyTakenError,
)


def _extract_validation_message(
    exc: RequestValidationError | ValidationError,
) -> str:
    errors = exc.errors()
    if not errors:
        return "Ошибка валидации данных"

    first_err = errors[0]
    original_exc = first_err.get("ctx", {}).get("error")
    if original_exc is not None:
        return str(original_exc)

    msg = first_err.get("msg", "Ошибка валидации данных")
    if msg.startswith("Value error, "):
        return msg.removeprefix("Value error, ")
    return msg


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError | ValidationError,
) -> PlainTextResponse:
    message = _extract_validation_message(exc)
    request.state.error_message = message
    return PlainTextResponse(
        content=message,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def domain_validation_error_handler(
    request: Request,
    exc: DomainValidationError,
) -> PlainTextResponse:
    request.state.error_message = exc.message
    return PlainTextResponse(
        content=exc.message,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


async def login_already_taken_handler(
    request: Request,
    exc: LoginAlreadyTakenError,
) -> PlainTextResponse:
    request.state.error_message = exc.message
    return PlainTextResponse(
        content=exc.message,
        status_code=status.HTTP_409_CONFLICT,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Регистрация обработчиков исключений в приложении FastAPI."""
    app.exception_handler(RequestValidationError)(validation_error_handler)
    app.exception_handler(ValidationError)(validation_error_handler)
    app.exception_handler(DomainValidationError)(
        domain_validation_error_handler
    )
    app.exception_handler(LoginAlreadyTakenError)(login_already_taken_handler)
