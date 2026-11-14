"""Browser tests for the light and dark themes and the Dark mode switch (feature 002)."""

from collections.abc import Iterator
from typing import Literal, Protocol

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect

from tests.e2e.theme_helpers import (
    DARK_BG,
    LIGHT_BG,
    active_scheme,
    assert_nothing_stored,
    body_background,
    dark_mode_switch,
    is_drawer_open,
    is_same_document,
    mark_document,
    open_drawer,
)

type ColorScheme = Literal["light", "dark", "no-preference"]

_PATHS = ["/", "/about", "/does-not-exist"]
_EXPECTED: dict[ColorScheme, tuple[str, str]] = {
    "dark": ("dark", DARK_BG),
    "light": ("light", LIGHT_BG),
    "no-preference": ("light", LIGHT_BG),
}


class PageFactory(Protocol):
    """Creates a page in a fresh browser context."""

    def __call__(self, color_scheme: ColorScheme, *, java_script_enabled: bool = True) -> Page:
        """Create a page with the given colour scheme and JavaScript setting."""
        ...


@pytest.fixture
def make_page(browser: Browser, base_url: str) -> Iterator[PageFactory]:
    """Create pages in fresh contexts with a given colour scheme and JavaScript setting.

    Yields:
        A factory ``(color_scheme, java_script_enabled=True) -> Page``.
    """
    contexts: list[BrowserContext] = []

    def factory(color_scheme: ColorScheme, *, java_script_enabled: bool = True) -> Page:
        context = browser.new_context(
            base_url=base_url,
            color_scheme=color_scheme,
            java_script_enabled=java_script_enabled,
        )
        contexts.append(context)
        return context.new_page()

    yield factory
    for context in contexts:
        context.close()


# --- User Story 1: the site matches the device preference -------------------------------------


@pytest.mark.firefox
@pytest.mark.parametrize("color_scheme", list(_EXPECTED))
@pytest.mark.parametrize("path", _PATHS)
def test_theme_follows_device_preference(
    make_page: PageFactory, path: str, color_scheme: ColorScheme
) -> None:
    """Every page uses the theme matching the device preference (FR-001, FR-002)."""
    page = make_page(color_scheme)
    page.goto(path)
    scheme, background = _EXPECTED[color_scheme]
    assert active_scheme(page) == scheme
    assert body_background(page) == background


@pytest.mark.firefox
def test_theme_follows_live_preference_change(make_page: PageFactory) -> None:
    """Changing the device preference updates the open page without a reload (FR-004)."""
    page = make_page("light")
    page.goto("/")
    mark_document(page)
    page.emulate_media(color_scheme="dark")
    assert active_scheme(page) == "dark"
    assert body_background(page) == DARK_BG
    page.emulate_media(color_scheme="light")
    assert active_scheme(page) == "light"
    assert is_same_document(page)


@pytest.mark.firefox
@pytest.mark.parametrize("color_scheme", list(_EXPECTED))
def test_theme_follows_device_preference_without_javascript(
    make_page: PageFactory, color_scheme: ColorScheme
) -> None:
    """The default theme needs no JavaScript (FR-005)."""
    page = make_page(color_scheme, java_script_enabled=False)
    page.goto("/")
    scheme, background = _EXPECTED[color_scheme]
    assert active_scheme(page) == scheme
    assert body_background(page) == background


@pytest.mark.firefox
def test_default_theme_stores_nothing(make_page: PageFactory) -> None:
    """Viewing the site stores nothing in the browser (FR-016)."""
    page = make_page("dark")
    page.goto("/")
    assert_nothing_stored(page)


# --- User Story 2: the Dark mode switch -------------------------------------------------------


@pytest.mark.firefox
@pytest.mark.parametrize("color_scheme", ["light", "dark"])
def test_switch_state_matches_theme(make_page: PageFactory, color_scheme: ColorScheme) -> None:
    """Exactly one "Dark mode" switch is exposed and it is On iff dark is shown (FR-007)."""
    page = make_page(color_scheme)
    page.goto("/")
    open_drawer(page)
    switch = dark_mode_switch(page)
    expect(switch).to_have_count(1)
    expect(switch).to_be_visible()
    assert switch.is_checked() == (active_scheme(page) == "dark")


@pytest.mark.firefox
@pytest.mark.parametrize("color_scheme", ["light", "dark"])
@pytest.mark.parametrize("java_script_enabled", [True, False], ids=["js", "no-js"])
def test_switch_flips_theme_in_place(
    make_page: PageFactory, color_scheme: ColorScheme, *, java_script_enabled: bool
) -> None:
    """Toggling the switch flips the theme without leaving the page (FR-008, FR-010)."""
    page = make_page(color_scheme, java_script_enabled=java_script_enabled)
    page.goto("/about")
    url = page.url
    open_drawer(page)
    before = active_scheme(page)
    if java_script_enabled:
        mark_document(page)
    dark_mode_switch(page).click()
    after = active_scheme(page)
    assert after != before
    assert dark_mode_switch(page).is_checked() == (after == "dark")
    assert body_background(page) == (DARK_BG if after == "dark" else LIGHT_BG)
    assert page.url == url
    assert is_drawer_open(page)
    if java_script_enabled:
        assert is_same_document(page)


@pytest.mark.firefox
def test_switch_toggles_from_label(make_page: PageFactory) -> None:
    """Clicking the "Dark mode" label text toggles the switch (FR-009)."""
    page = make_page("light")
    page.goto("/")
    open_drawer(page)
    page.locator("#nav-drawer label:visible", has_text="Dark mode").click(position={"x": 5, "y": 5})
    assert active_scheme(page) == "dark"
    expect(dark_mode_switch(page)).to_be_checked()


@pytest.mark.firefox
def test_switch_is_keyboard_operable(make_page: PageFactory) -> None:
    """The switch can be reached and toggled with the keyboard alone (FR-009)."""
    page = make_page("light")
    page.goto("/")
    page.get_by_role("button", name="Menu").focus()
    page.keyboard.press("Enter")
    for _ in range(10):
        page.keyboard.press("Tab")
        if dark_mode_switch(page).evaluate("el => el === document.activeElement"):
            break
    expect(dark_mode_switch(page)).to_be_focused()
    page.keyboard.press("Space")
    assert active_scheme(page) == "dark"
    expect(dark_mode_switch(page)).to_be_checked()


@pytest.mark.firefox
def test_switch_after_device_preference_change(make_page: PageFactory) -> None:
    """After a device change the switch for the new preference applies (FR-004 behaviour)."""
    page = make_page("dark")
    page.goto("/")
    open_drawer(page)
    dark_mode_switch(page).click()
    assert active_scheme(page) == "light"
    page.emulate_media(color_scheme="light")
    expect(page.locator("#dark-mode-light-device")).to_be_visible()
    expect(dark_mode_switch(page)).not_to_be_checked()
    assert active_scheme(page) == "light"


@pytest.mark.firefox
def test_switch_row_meets_target_size(make_page: PageFactory) -> None:
    """The switch row is at least 44 px tall (FR-009)."""
    page = make_page("light")
    page.goto("/")
    open_drawer(page)
    box = page.locator("#nav-drawer label:visible", has_text="Dark mode").bounding_box()
    assert box is not None
    assert box["height"] >= 44


@pytest.mark.firefox
def test_switch_stores_nothing(make_page: PageFactory) -> None:
    """Using the switch stores nothing in the browser (FR-016)."""
    page = make_page("light")
    page.goto("/")
    open_drawer(page)
    dark_mode_switch(page).click()
    assert_nothing_stored(page)


def test_switch_sits_directly_above_about(make_page: PageFactory) -> None:
    """The Dark mode item is at the bottom of the drawer, directly above About (FR-006)."""
    page = make_page("light")
    page.goto("/")
    open_drawer(page)
    drawer = page.locator("#nav-drawer")
    page.wait_for_timeout(500)  # Let the slide-in finish.
    item = drawer.locator(".theme-item").bounding_box()
    about = drawer.get_by_role("link", name="About").bounding_box()
    home = drawer.get_by_role("link", name="Home").bounding_box()
    panel = drawer.bounding_box()
    assert item is not None
    assert about is not None
    assert home is not None
    assert panel is not None
    assert abs((item["y"] + item["height"]) - about["y"]) <= 1
    assert abs((about["y"] + about["height"]) - (panel["y"] + panel["height"])) <= 1
    assert item["y"] > home["y"] + home["height"] + 100
