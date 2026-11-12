"""Jinja2 template configuration."""

from pathlib import Path
from typing import Final

from fastapi import Request
from fastapi.templating import Jinja2Templates

from website.content import PAGES, SITE_TITLE, BuildInfo, tab_title


def site_context(request: Request) -> dict[str, object]:
    """Provide values shared by every template.

    Args:
        request: The current request.

    Returns:
        Navigation pages, the site title, the tab-title helper and build information.
    """
    return {
        "nav_pages": PAGES,
        "site_title": SITE_TITLE,
        "tab_title": tab_title,
        "build_info": BuildInfo.from_settings(request.app.state.settings),
    }


templates: Final[Jinja2Templates] = Jinja2Templates(
    directory=Path(__file__).parent / "templates",
    context_processors=[site_context],
)
