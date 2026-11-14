"""Site content and domain values.

This module is the single source of truth for pages, links and credits; templates and tests
both read from it.
"""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final, Self

from website.config import Settings

SITE_TITLE: Final = "Tim's Page"
NOT_FOUND_TITLE: Final = "Page not found"
ICONS_DIR: Final = Path(__file__).parent / "templates" / "icons"
PAINTING_ALT: Final = "Sisley - Lady's Cove (1897)"


@dataclass(frozen=True, slots=True)
class Page:
    """An addressable page listed in the navigation.

    Attributes:
        name: Route name, unique, ``snake_case``.
        path: URL path, starting with ``/``.
        title: Title shown in the header and browser tab.
        nav_label: Text of the navigation link.
    """

    name: str
    path: str
    title: str
    nav_label: str


HOME: Final = Page(name="home", path="/", title=SITE_TITLE, nav_label="Home")
ANASCRAMBLE: Final = Page(
    name="anascramble", path="/anascramble", title="Anascramble", nav_label="Anascramble"
)
ABOUT: Final = Page(name="about", path="/about", title="About", nav_label="About")
# Navigation order. The last page (About) is pinned to the bottom of the drawer, so add new
# pages before it.
PAGES: Final[tuple[Page, ...]] = (HOME, ANASCRAMBLE, ABOUT)


def tab_title(title: str) -> str:
    """Build the browser tab title for a page.

    Args:
        title: The page title.

    Returns:
        The site title for the home page, otherwise ``"{title} · {site title}"``.
    """
    return SITE_TITLE if title == SITE_TITLE else f"{title} · {SITE_TITLE}"


@dataclass(frozen=True, slots=True)
class BuildInfo:
    """Source information about the running build, shown on the About page.

    Attributes:
        repository_url: Public source repository, without a trailing slash.
        revision: Full revision the site was built from, if known.
        short_revision: First 7 characters of ``revision``, if known.
        revision_url: Link to ``revision`` in the repository, if known.
    """

    repository_url: str
    revision: str | None
    short_revision: str | None
    revision_url: str | None

    @classmethod
    def from_settings(cls, settings: Settings) -> Self:
        """Derive build information from the application settings.

        Args:
            settings: The application settings.

        Returns:
            The build information for templates.
        """
        repository_url = str(settings.repository_url).rstrip("/")
        revision = settings.revision
        if revision is None:
            return cls(repository_url, None, None, None)
        return cls(repository_url, revision, revision[:7], f"{repository_url}/tree/{revision}")


class Icon(StrEnum):
    """Font Awesome Free icons shipped as SVG partials in ``templates/icons``."""

    GITHUB = "github.svg"
    BOOK = "book.svg"
    FILE_LINES = "file-lines.svg"
    BARS = "bars.svg"


@dataclass(frozen=True, slots=True)
class ExternalLink:
    """A link to an external site, shown on the home page.

    Attributes:
        text: Visible link text, unique.
        url: Absolute ``https://`` URL.
        icon: Icon shown before the text.
    """

    text: str
    url: str
    icon: Icon


EXTERNAL_LINKS: Final[tuple[ExternalLink, ...]] = (
    ExternalLink("GitHub", "https://www.github.com/tjh90", Icon.GITHUB),
    ExternalLink("PhD Thesis", "https://eprints.soton.ac.uk/404274/", Icon.BOOK),
    ExternalLink("Paper", "https://ieeexplore.ieee.org/document/7029130", Icon.FILE_LINES),
)

LICENCE_NAME: Final = "GNU Affero General Public License v3.0"
LICENCE_URL: Final = "https://www.gnu.org/licenses/agpl-3.0.html"
COOKIE_STATEMENT: Final = "This site does not use cookies."


@dataclass(frozen=True, slots=True)
class Credit:
    """A third-party work credited on the About page.

    Attributes:
        work: Name of the work.
        author: Author or owner.
        work_url: Link to the work or its project, if any.
        licence: Licence name, e.g. "CC BY 4.0", "Public domain".
        licence_url: Link to the licence text; ``None`` for the public domain.
    """

    work: str
    author: str
    work_url: str | None
    licence: str
    licence_url: str | None


CREDITS: Final[tuple[Credit, ...]] = (
    Credit(
        work="Font Awesome Free icons",
        author="Fonticons, Inc.",
        work_url="https://fontawesome.com",
        licence="CC BY 4.0",
        licence_url="https://creativecommons.org/licenses/by/4.0/",
    ),
    Credit(
        work="Lady's Cove (1897)",
        author="Alfred Sisley",
        work_url=None,
        licence="Public domain",
        licence_url=None,
    ),
    Credit(
        work="htmx",
        author="Big Sky Software",
        work_url="https://htmx.org",
        licence="BSD Zero Clause License",
        licence_url="https://opensource.org/license/0bsd",
    ),
    Credit(
        work="Rock Salt font",
        author="Sideshow",
        work_url="https://fonts.google.com/specimen/Rock+Salt",
        licence="Apache License 2.0",
        licence_url="https://www.apache.org/licenses/LICENSE-2.0",
    ),
)
