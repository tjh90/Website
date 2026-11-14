"""Shared helpers for browser tests of themes, the Dark mode switch and in-place navigation."""

from typing import Final

from playwright.sync_api import Locator, Page

LIGHT_BG: Final = "rgb(255, 255, 255)"
DARK_BG: Final = "rgb(18, 20, 23)"


def active_scheme(page: Page) -> str:
    """Return the colour scheme applied to the root element.

    Args:
        page: The page to inspect.

    Returns:
        ``"dark"`` if the root element computes a dark ``color-scheme``, otherwise ``"light"``.
    """
    scheme = str(page.evaluate("getComputedStyle(document.documentElement).colorScheme"))
    return "dark" if scheme.strip() == "dark" else "light"


def body_background(page: Page) -> str:
    """Return the computed background colour of ``body``.

    Args:
        page: The page to inspect.

    Returns:
        The CSS ``background-color`` value, e.g. ``"rgb(255, 255, 255)"``.
    """
    return str(page.evaluate("getComputedStyle(document.body).backgroundColor"))


def dark_mode_switch(page: Page) -> Locator:
    """Return the visible "Dark mode" switch.

    Args:
        page: The page to search.

    Returns:
        A locator for the switch exposed to assistive technology.
    """
    return page.get_by_role("switch", name="Dark mode")


def is_drawer_open(page: Page) -> bool:
    """Report whether the navigation drawer is showing.

    Args:
        page: The page to inspect.

    Returns:
        Whether ``#nav-drawer`` matches ``:popover-open``.
    """
    return bool(page.locator("#nav-drawer").evaluate("el => el.matches(':popover-open')"))


def open_drawer(page: Page) -> None:
    """Open the navigation drawer with the menu button, unless it is already open.

    Args:
        page: The page to act on.
    """
    if not is_drawer_open(page):
        page.get_by_role("button", name="Menu").click()


def assert_nothing_stored(page: Page) -> None:
    """Assert that the site has set no cookies and written nothing to browser storage.

    Args:
        page: The page whose context and storage are checked.
    """
    assert page.context.cookies() == []
    assert page.evaluate("localStorage.length") == 0
    assert page.evaluate("sessionStorage.length") == 0


def mark_document(page: Page) -> None:
    """Tag the current document so a later full page load can be detected.

    Args:
        page: The page to tag.
    """
    page.evaluate("window.__sameDocument = true")


def is_same_document(page: Page) -> bool:
    """Report whether the document tagged by :func:`mark_document` is still loaded.

    A full page load (reload, typed address or ordinary link) discards the tag; in-place
    navigation and CSS-only changes keep it.

    Args:
        page: The page to inspect.

    Returns:
        Whether no full page load has happened since the tag was set.
    """
    return bool(page.evaluate("window.__sameDocument === true"))
