from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.responses import Response

from app.api.routes.analyses import router as analyses_router
from app.api.routes.health import router as health_router
from app.core.config import settings


class BodySizeLimitMiddleware:
    """Reject oversized HTTP bodies before FastAPI parses multipart uploads."""

    def __init__(self, app: ASGIApp, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        raw_length = headers.get(b"content-length")
        if raw_length is not None:
            try:
                if int(raw_length) > self.max_bytes:
                    response = Response("Request body too large", status_code=413)
                    await response(scope, receive, send)
                    return
            except ValueError:
                response = Response("Invalid Content-Length", status_code=400)
                await response(scope, receive, send)
                return

        received = 0
        exhausted = False

        async def limited_receive() -> Message:
            nonlocal received, exhausted
            message = await receive()
            if message["type"] != "http.request":
                return message
            body = message.get("body", b"")
            received += len(body)
            if received > self.max_bytes:
                exhausted = True
                return {"type": "http.disconnect"}
            if not message.get("more_body", False):
                exhausted = True
            return message

        try:
            await self.app(scope, limited_receive, send)
        except Exception:
            if exhausted and received > self.max_bytes:
                response = Response("Request body too large", status_code=413)
                await response(scope, receive, send)
                return
            raise


app = FastAPI(title=settings.app_name, version="0.2.0")
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_request_body_bytes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https://ai-retail-shelf-intelligence(?:-[a-z0-9-]+)?-owaies-projects\.vercel\.app$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Accept", "Content-Type", "Authorization"],
)

app.include_router(health_router, prefix="/api")
app.include_router(analyses_router, prefix="/api")
