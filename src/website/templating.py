"""Jinja2 template configuration and page rendering."""

from pathlib import Path
from typing import Final

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from website.content import PAGES, SITE_TITLE, BuildInfo, tab_title

HTMX_REQUEST_HEADER: Final = "HX-Request"


def is_htmx_request(request: Request) -> bool:
    """Report whether a request was made by htmx (in-place navigation or history restore).

    Args:
        request: The current request.

    Returns:
        Whether the ``HX-Request`` header is ``true``.
    """
    return request.headers.get(HTMX_REQUEST_HEADER) == "true"


def site_context(request: Request) -> dict[str, object]:
    """Provide values shared by every template.

    Args:
        request: The current request.

    Returns:
        Navigation pages, the site title, the tab-title helper, build information and whether
        the request came from htmx.
    """
    return {
        "nav_pages": PAGES,
        "site_title": SITE_TITLE,
        "tab_title": tab_title,
        "build_info": BuildInfo.from_settings(request.app.state.settings),
        "is_htmx_request": is_htmx_request(request),
    }


templates: Final[Jinja2Templates] = Jinja2Templates(
    directory=Path(__file__).parent / "templates",
    context_processors=[site_context],
)


def render(
    request: Request,
    name: str,
    context: dict[str, object] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    """Render a page template.

    The markup differs for htmx requests (the heading is focused after in-place navigation), so
    the response varies on the ``HX-Request`` header.

    Args:
        request: The current request.
        name: Template file name.
        context: Page-specific template values.
        status_code: HTTP status code of the response.

    Returns:
        The rendered page.
    """
    response = templates.TemplateResponse(request, name, context or {}, status_code=status_code)
    vary = [v.strip() for v in response.headers.get("vary", "").split(",") if v.strip()]
    if HTMX_REQUEST_HEADER.lower() not in (v.lower() for v in vary):
        vary.append(HTMX_REQUEST_HEADER)
    response.headers["vary"] = ", ".join(vary)
    return response
