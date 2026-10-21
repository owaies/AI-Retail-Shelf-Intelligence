import asyncio

from app.main import BodySizeLimitMiddleware


def test_rejects_oversized_chunked_body_before_dispatch():
    downstream_called = False
    sent = []

    async def downstream(scope, receive, send):
        nonlocal downstream_called
        downstream_called = True
        message = await receive()
        if message["type"] == "http.disconnect":
            return
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def receive():
        return {"type": "http.request", "body": b"12345", "more_body": False}

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
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
    }

    asyncio.run(BodySizeLimitMiddleware(downstream, 4)(scope, receive, send))

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
    assert downstream_called is False
