import json
import logging
from typing import Any

from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from src.app.masking import mask_sensitive

logger = logging.getLogger("http")


async def get_request_parameters(
    request: Request,
) -> dict[str, Any]:
    parameters: dict[str, Any] = {}

    if request.query_params:
        parameters["query"] = mask_sensitive(dict(request.query_params))

    body = await request.body()

    if body:
        try:
            data = json.loads(body)
            parameters["body"] = mask_sensitive(data)
        except json.JSONDecodeError, UnicodeDecodeError:
            parameters["body"] = "<invalid json>"

    return parameters


async def request_logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    parameters = await get_request_parameters(request)

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Request crashed | method=%s | path=%s | parameters=%s",
            request.method,
            request.url.path,
            parameters,
        )
        raise

    if response.status_code < 400:
        logger.info(
            "Request successful | method=%s | path=%s | parameters=%s | result=True",
            request.method,
            request.url.path,
            parameters,
        )
    else:
        error = getattr(
            request.state,
            "error_message",
            f"HTTP {response.status_code}",
        )

        logger.warning(
            "Request failed | method=%s | path=%s | parameters=%s | result=False | error=%s",
            request.method,
            request.url.path,
            parameters,
            error,
        )

    return response
