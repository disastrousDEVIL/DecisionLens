"""Privacy-safe request lifecycle logging."""

import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("decisionlens.http")


async def log_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Log request metadata only; never log bodies, prompts, or credentials."""
    request_id = request.headers.get("x-request-id") or uuid4().hex
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            (time.perf_counter() - started) * 1000,
        )
        raise
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1000,
    )
    return response
