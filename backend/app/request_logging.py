"""Structured, low-cardinality HTTP request logging.

The middleware deliberately works with the ASGI scope instead of reading a
``Request`` body.  This keeps customer-provided data out of access logs and
avoids consuming the body before FastAPI can validate it.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from collections.abc import Callable, MutableMapping
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, TextIO

from fastapi import FastAPI

REQUEST_LOGGER_NAME = "booking.http"
UNMATCHED_ROUTE = "<unmatched>"

_LOG_FIELDS = (
    "method",
    "route",
    "status",
    "duration_ms",
    "trace_id",
    "span_id",
    "release",
    "commit_sha",
)
_TRACEPARENT_PATTERN = re.compile(
    r"^(?P<version>[0-9a-f]{2})-"
    r"(?P<trace_id>[0-9a-f]{32})-"
    r"(?P<span_id>[0-9a-f]{16})-"
    r"(?P<flags>[0-9a-f]{2})$",
    re.IGNORECASE,
)


class JsonLogFormatter(logging.Formatter):
    """Serialize request log records as one compact JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for field in _LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_request_logger(
    *,
    stream: TextIO | None = None,
    level: int = logging.INFO,
    logger_name: str = REQUEST_LOGGER_NAME,
) -> logging.Logger:
    """Configure the dedicated request logger to emit JSON to stdout.

    Repeated calls are safe: handlers previously installed by this function
    are replaced instead of duplicated.  Other application loggers and the
    root logger are left untouched.
    """

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, "_booking_request_handler", False):
            logger.removeHandler(handler)
            handler.close()

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    handler._booking_request_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    return logger


class RequestLoggingMiddleware:
    """Log one sanitized JSON event after each HTTP request completes."""

    def __init__(
        self,
        app: Callable[..., Any],
        *,
        release: str,
        commit_sha: str,
        logger: logging.Logger | None = None,
    ) -> None:
        self.app = app
        self.release = release
        self.commit_sha = commit_sha
        self.logger = logger or logging.getLogger(REQUEST_LOGGER_NAME)

    async def __call__(
        self,
        scope: MutableMapping[str, Any],
        receive: Callable[..., Any],
        send: Callable[..., Any],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started_at = perf_counter()
        response_status = 500
        trace_id, span_id = _trace_identifiers(scope)
        logged = False

        def emit_request_log() -> None:
            nonlocal logged
            if logged:
                return

            active_trace_id, active_span_id = _trace_identifiers(scope)
            fields: dict[str, object] = {
                "method": str(scope.get("method", "UNKNOWN")),
                "route": _route_template(scope),
                "status": response_status,
                "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                "release": self.release,
                "commit_sha": self.commit_sha,
            }

            resolved_trace_id = active_trace_id or trace_id
            resolved_span_id = active_span_id or span_id
            if resolved_trace_id is not None:
                fields["trace_id"] = resolved_trace_id
            if resolved_span_id is not None:
                fields["span_id"] = resolved_span_id

            self.logger.info("http_request", extra=fields)
            logged = True

        async def capture_status(message: MutableMapping[str, Any]) -> None:
            nonlocal response_status, trace_id, span_id
            if message["type"] == "http.response.start":
                response_status = int(message["status"])
                active_trace_id, active_span_id = _trace_identifiers(scope)
                if active_trace_id is not None:
                    trace_id = active_trace_id
                if active_span_id is not None:
                    span_id = active_span_id
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                # Emit while the inner OpenTelemetry server span is still current so
                # the exported log record receives the same native trace context.
                emit_request_log()

        try:
            await self.app(scope, receive, capture_status)
        finally:
            # Exception paths might not send a complete response body. They still
            # receive exactly one sanitized access-log event.
            emit_request_log()


def install_request_logging(
    application: FastAPI,
    *,
    release: str,
    commit_sha: str,
    logger: logging.Logger | None = None,
) -> None:
    """Configure JSON output and attach request logging to a FastAPI app."""

    request_logger = logger or configure_request_logger()
    application.add_middleware(
        RequestLoggingMiddleware,
        release=release,
        commit_sha=commit_sha,
        logger=request_logger,
    )


def _route_template(scope: MutableMapping[str, Any]) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path.startswith("/"):
        return path
    return UNMATCHED_ROUTE


def _trace_identifiers(
    scope: MutableMapping[str, Any],
) -> tuple[str | None, str | None]:
    active_context = _active_opentelemetry_context()
    if active_context != (None, None):
        return active_context
    return _traceparent_context(scope)


def _active_opentelemetry_context() -> tuple[str | None, str | None]:
    try:
        from opentelemetry import trace
    except ImportError:
        return None, None

    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None, None
    return f"{span_context.trace_id:032x}", f"{span_context.span_id:016x}"


def _traceparent_context(
    scope: MutableMapping[str, Any],
) -> tuple[str | None, str | None]:
    for raw_name, raw_value in scope.get("headers", []):
        if raw_name.lower() != b"traceparent":
            continue
        try:
            traceparent = raw_value.decode("ascii")
        except UnicodeDecodeError:
            return None, None
        match = _TRACEPARENT_PATTERN.fullmatch(traceparent)
        if match is None or match["version"].lower() == "ff":
            return None, None
        trace_id = match["trace_id"].lower()
        span_id = match["span_id"].lower()
        if trace_id == "0" * 32 or span_id == "0" * 16:
            return None, None
        return trace_id, span_id
    return None, None
