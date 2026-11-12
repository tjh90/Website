"""Application factory and middleware."""

from pathlib import Path
from typing import Final

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from website import routes
from website.config import Settings, get_settings
from website.content import NOT_FOUND_TITLE
from website.templating import templates

_STATIC_DIR: Final = Path(__file__).parent / "static"

SECURITY_HEADERS: Final[dict[str, str]] = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'none'; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


class SecurityHeadersMiddleware:
    """Pure ASGI middleware that adds security headers to every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap an ASGI application.

        Args:
            app: The application to wrap.
        """
        self.app = app
        self._headers = [(k.lower().encode(), v.encode()) for k, v in SECURITY_HEADERS.items()]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle an ASGI call, adding headers to HTTP response starts.

        Args:
            scope: The ASGI connection scope.
            receive: The ASGI receive channel.
            send: The ASGI send channel.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                message["headers"] = [*message.get("headers", []), *self._headers]
            await send(message)

        await self.app(scope, receive, send_with_headers)


async def _handle_http_exception(request: Request, exc: Exception) -> Response:
    """Render a site-styled page for 404s and defer to FastAPI for other errors.

    Args:
        request: The request that failed.
        exc: The raised HTTP exception.

    Returns:
        The error response.
    """
    if not isinstance(exc, StarletteHTTPException):  # Only registered for HTTP exceptions.
        raise exc
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request, "not_found.html", {"not_found_title": NOT_FOUND_TITLE}, status_code=404
        )
    return await http_exception_handler(request, exc)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the website application.

    Args:
        settings: Settings to use; defaults to those loaded from the environment.

    Returns:
        The configured FastAPI application.
    """
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings or get_settings()
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
    app.include_router(routes.router)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_middleware(SecurityHeadersMiddleware)
    return app
