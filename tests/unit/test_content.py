"""Unit tests for :mod:`website.content`."""

import pytest

from website.config import Settings
from website.content import (
    ABOUT,
    COOKIE_STATEMENT,
    CREDITS,
    EXTERNAL_LINKS,
    HOME,
    ICONS_DIR,
    LICENCE_NAME,
    LICENCE_URL,
    PAGES,
    BuildInfo,
    Credit,
    Icon,
    tab_title,
)

_FULL_SHA = "0123456789abcdef0123456789abcdef01234567"


def test_pages_registry() -> None:
    """The navigation lists Home then About with the expected metadata."""
    assert [(p.name, p.path, p.title, p.nav_label) for p in PAGES] == [
        ("home", "/", "Tim's Page", "Home"),
        ("about", "/about", "About", "About"),
    ]


def test_page_names_and_paths_are_unique() -> None:
    """No two pages share a route name or path."""
    assert len({p.name for p in PAGES}) == len(PAGES)
    assert len({p.path for p in PAGES}) == len(PAGES)


@pytest.mark.parametrize(
    ("title", "expected"),
    [(HOME.title, "Tim's Page"), (ABOUT.title, "About · Tim's Page")],
)
def test_tab_title(title: str, expected: str) -> None:
    """The home tab shows the site title; other tabs are suffixed with it."""
    assert tab_title(title) == expected


def test_build_info_without_revision() -> None:
    """Without a revision only the repository URL is available."""
    info = BuildInfo.from_settings(Settings(revision=None))
    assert info.repository_url == "https://github.com/tjh90/website"
    assert info.revision is None
    assert info.short_revision is None
    assert info.revision_url is None


def test_build_info_with_revision() -> None:
    """A known revision yields a short form and a link to that revision."""
    info = BuildInfo.from_settings(Settings(revision=_FULL_SHA))
    assert info.short_revision == "0123456"
    assert info.revision_url == f"https://github.com/tjh90/website/tree/{_FULL_SHA}"


def test_build_info_strips_trailing_slash() -> None:
    """A repository URL with a trailing slash does not produce ``//`` in links."""
    settings = Settings(repository_url="https://example.com/repo/", revision="abcdef1")
    info = BuildInfo.from_settings(settings)
    assert info.repository_url == "https://example.com/repo"
    assert info.revision_url == "https://example.com/repo/tree/abcdef1"


def test_external_links() -> None:
    """The home page links match the reference site, in order."""
    assert [(link.text, link.url, link.icon) for link in EXTERNAL_LINKS] == [
        ("GitHub", "https://www.github.com/tjh90", Icon.GITHUB),
        ("PhD Thesis", "https://eprints.soton.ac.uk/404274/", Icon.BOOK),
        ("Paper", "https://ieeexplore.ieee.org/document/7029130", Icon.FILE_LINES),
    ]


def test_external_links_are_https_and_unique() -> None:
    """Every link is absolute HTTPS and link texts are unique."""
    assert all(link.url.startswith("https://") for link in EXTERNAL_LINKS)
    assert len({link.text for link in EXTERNAL_LINKS}) == len(EXTERNAL_LINKS)


def test_icon_members() -> None:
    """Each icon maps to its SVG partial."""
    assert {icon.name: icon.value for icon in Icon} == {
        "GITHUB": "github.svg",
        "BOOK": "book.svg",
        "FILE_LINES": "file-lines.svg",
        "BARS": "bars.svg",
    }


@pytest.mark.parametrize("icon", list(Icon))
def test_icon_files_keep_font_awesome_licence(icon: Icon) -> None:
    """Every shipped icon keeps Font Awesome's licence comment (FR-016b)."""
    svg = (ICONS_DIR / icon.value).read_text(encoding="utf-8")
    assert svg.lstrip().startswith("<!--!")
    comment = svg[: svg.index("-->")]
    assert "Font Awesome Free" in comment
    assert "License" in comment


def test_credits() -> None:
    """Credits cover every third-party asset shown to visitors (constitution VI)."""
    assert (
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
    ) == CREDITS


def test_licence_constants() -> None:
    """The licence and cookie statements match the data model."""
    assert LICENCE_NAME == "GNU Affero General Public License v3.0"
    assert LICENCE_URL == "https://www.gnu.org/licenses/agpl-3.0.html"
    assert COOKIE_STATEMENT == "This site does not use cookies."
