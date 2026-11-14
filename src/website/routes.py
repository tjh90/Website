"""HTTP routes."""

from pathlib import Path
from typing import Annotated, Final, Literal

from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from website.anascramble import Puzzle, parse_intent
from website.content import (
    COOKIE_STATEMENT,
    CREDITS,
    EXTERNAL_LINKS,
    LICENCE_NAME,
    LICENCE_URL,
    PAINTING_ALT,
)
from website.templating import is_htmx_request, render

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


class AnascrambleForm(BaseModel):
    """Raw Anascramble form submission.

    Every field is a lenient string so that malformed or tampered input is sanitised by the domain
    layer instead of being rejected with a validation error.

    Attributes:
        letters: The letters field.
        solution: The solution field.
        seed: Hidden seed of the arrangement currently shown.
        arranged: Hidden letters the current arrangement was made from.
        intent: What triggered the request: ``letters``, ``solution`` or ``scramble``.
    """

    letters: str = ""
    solution: str = ""
    seed: str = ""
    arranged: str = ""
    intent: str = ""


@router.api_route(
    "/anascramble",
    methods=["GET", "HEAD"],
    name="anascramble",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def anascramble(request: Request) -> HTMLResponse:
    """Render the Anascramble page with an empty puzzle.

    Args:
        request: The current request.

    Returns:
        The rendered page.
    """
    return render(request, "anascramble.html", {"puzzle": Puzzle.empty()})


@router.post("/anascramble", response_class=HTMLResponse, include_in_schema=False)
def anascramble_submit(request: Request, form: Annotated[AnascrambleForm, Form()]) -> HTMLResponse:
    """Apply an Anascramble form submission.

    htmx requests get only the out-of-band fragments that changed (contracts/http.md); plain
    submissions (no JavaScript) get the whole page.

    Args:
        request: The current request.
        form: The submitted form.

    Returns:
        The fragments or the rendered page, never cached.
    """
    intent = parse_intent(form.intent)
    puzzle = Puzzle.from_form(
        letters=form.letters,
        solution=form.solution,
        seed=form.seed,
        arranged=form.arranged,
        intent=intent,
    )
    template = "anascramble/_fragments.html" if is_htmx_request(request) else "anascramble.html"
    response = render(request, template, {"puzzle": puzzle, "intent": intent})
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    """Serve the site icon.

    Returns:
        The favicon file.
    """
    return FileResponse(_FAVICON, media_type="image/vnd.microsoft.icon")
