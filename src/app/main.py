from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, RedirectResponse

from app.logging import setup_logging
from app.middleware import request_logging_middleware
from app.schemas import UserRegister

setup_logging()

app = FastAPI()
app.middleware("http")(request_logging_middleware)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> PlainTextResponse:
    message = exc.errors()[0]["msg"]

    request.state.error_message = message

    return PlainTextResponse(
        content=message,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(
        "/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT
    )


@app.post("/v1/auth/register", status_code=status.HTTP_200_OK)
async def register(data: UserRegister) -> PlainTextResponse:
    return PlainTextResponse(content="OK")
