"""HTTP routes."""

from pathlib import Path
from typing import Final, Literal

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from website.content import (
    COOKIE_STATEMENT,
    CREDITS,
    EXTERNAL_LINKS,
    LICENCE_NAME,
    LICENCE_URL,
    PAINTING_ALT,
)
from website.templating import render

_FAVICON: Final = Path(__file__).parent / "static" / "favicon.ico"

router: Final[APIRouter] = APIRouter()


class HealthStatus(BaseModel):
    """Health check response body.

    Attributes:
        status: Always ``"ok"`` when the application can serve requests.
    """

    status: Literal["ok"] = "ok"


@router.get("/healthz", include_in_schema=False)
def healthz() -> HealthStatus:
    """Report that the application is running.

    Returns:
        A healthy status.
    """
    return HealthStatus()


@router.api_route(
    "/", methods=["GET", "HEAD"], name="home", response_class=HTMLResponse, include_in_schema=False
)
def home(request: Request) -> HTMLResponse:
    """Render the home page.

    Args:
        request: The current request.

    Returns:
        The rendered page.
    """
    return render(
        request, "home.html", {"external_links": EXTERNAL_LINKS, "painting_alt": PAINTING_ALT}
    )


@router.api_route(
    "/about",
    methods=["GET", "HEAD"],
    name="about",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def about(request: Request) -> HTMLResponse:
    """Render the About page with licence, source and credits.

    Args:
        request: The current request.

    Returns:
        The rendered page.
    """
    return render(
        request,
        "about.html",
        {
            "credits": CREDITS,
            "licence_name": LICENCE_NAME,
            "licence_url": LICENCE_URL,
            "cookie_statement": COOKIE_STATEMENT,
        },
    )


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    """Serve the site icon.

    Returns:
        The favicon file.
    """
    return FileResponse(_FAVICON, media_type="image/vnd.microsoft.icon")
