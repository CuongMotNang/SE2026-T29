import asyncio
import json
import logging
from io import StringIO
from types import SimpleNamespace
from typing import Any

from app.request_logging import (
    RequestLoggingMiddleware,
    configure_request_logger,
)


def _json_logger(stream: StringIO) -> logging.Logger:
    return configure_request_logger(stream=stream)


def _run_request(
    middleware: RequestLoggingMiddleware,
    *,
    path: str,
    route_template: str | None,
    method: str = "GET",
    headers: list[tuple[bytes, bytes]] | None = None,
    body: bytes = b"",
) -> list[dict[str, Any]]:
    scope: dict[str, Any] = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"customer_name=QuerySecret",
        "headers": headers or [],
    }
    if route_template is not None:
        scope["route"] = SimpleNamespace(path=route_template)

    messages: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    asyncio.run(middleware(scope, receive, send))
    return messages


def _responding_app(status: int = 200):
    async def application(scope, receive, send) -> None:
        await send({"type": "http.response.start", "status": status, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    return application


def test_request_log_uses_route_template_and_excludes_customer_data() -> None:
    stream = StringIO()
    middleware = RequestLoggingMiddleware(
        _responding_app(),
        release="v0.2.0",
        commit_sha="abc123",
        logger=_json_logger(stream),
    )

    _run_request(
        middleware,
        path="/appointments/private-id",
        route_template="/appointments/{appointment_id}",
        method="POST",
        body=b'{"customer_name":"BodySecret"}',
    )

    raw_log = stream.getvalue().strip()
    event = json.loads(raw_log)
    assert event["event"] == "http_request"
    assert event["method"] == "POST"
    assert event["route"] == "/appointments/{appointment_id}"
    assert event["status"] == 200
    assert isinstance(event["duration_ms"], float)
    assert event["duration_ms"] >= 0
    assert event["release"] == "v0.2.0"
    assert event["commit_sha"] == "abc123"
    assert "private-id" not in raw_log
    assert "QuerySecret" not in raw_log
    assert "BodySecret" not in raw_log
    assert "customer_name" not in raw_log


def test_request_log_includes_valid_traceparent_ids() -> None:
    stream = StringIO()
    middleware = RequestLoggingMiddleware(
        _responding_app(),
        release="dev",
        commit_sha="unknown",
        logger=_json_logger(stream),
    )
    trace_id = "0af7651916cd43dd8448eb211c80319c"
    span_id = "b7ad6b7169203331"

    _run_request(
        middleware,
        path="/health",
        route_template="/health",
        headers=[(b"traceparent", f"00-{trace_id}-{span_id}-01".encode())],
    )

    event = json.loads(stream.getvalue())
    assert event["trace_id"] == trace_id
    assert event["span_id"] == span_id


def test_unmatched_path_has_fixed_low_cardinality_route() -> None:
    stream = StringIO()
    middleware = RequestLoggingMiddleware(
        _responding_app(status=404),
        release="dev",
        commit_sha="unknown",
        logger=_json_logger(stream),
    )

    _run_request(
        middleware,
        path="/does-not-exist/private-value",
        route_template=None,
    )

    raw_log = stream.getvalue().strip()
    event = json.loads(raw_log)
    assert event["route"] == "<unmatched>"
    assert event["status"] == 404
    assert "private-value" not in raw_log


def test_invalid_traceparent_is_not_logged() -> None:
    stream = StringIO()
    middleware = RequestLoggingMiddleware(
        _responding_app(),
        release="dev",
        commit_sha="unknown",
        logger=_json_logger(stream),
    )

    _run_request(
        middleware,
        path="/health",
        route_template="/health",
        headers=[
            (
                b"traceparent",
                b"00-00000000000000000000000000000000-0000000000000000-01",
            )
        ],
    )

    event = json.loads(stream.getvalue())
    assert "trace_id" not in event
    assert "span_id" not in event
