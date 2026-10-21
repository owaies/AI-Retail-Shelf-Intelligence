import asyncio

from app.main import BodySizeLimitMiddleware


def run_middleware(content_length: bytes, max_bytes: int = 4):
    downstream_called = False
    sent = []

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/analyses",
        "raw_path": b"/api/analyses",
        "query_string": b"",
        "headers": [(b"content-length", content_length)],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }

    asyncio.run(BodySizeLimitMiddleware(downstream, max_bytes)(scope, receive, send))
    return sent, downstream_called


def test_rejects_declared_body_larger_than_limit_before_dispatch():
    sent, downstream_called = run_middleware(b"5")

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
    assert downstream_called is False


def test_rejects_malformed_content_length_before_dispatch():
    sent, downstream_called = run_middleware(b"not-a-number")

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 400
    assert downstream_called is False


def test_rejects_negative_content_length_before_dispatch():
    sent, downstream_called = run_middleware(b"-1")

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 400
    assert downstream_called is False


def test_non_http_scopes_pass_through_to_downstream():
    downstream_called = False

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True

    async def receive():
        return {"type": "websocket.disconnect"}

    async def send(message):
        raise AssertionError("HTTP responses must not be sent for a websocket scope")

    scope = {"type": "websocket"}
    asyncio.run(BodySizeLimitMiddleware(downstream, 4)(scope, receive, send))

    assert downstream_called is True
