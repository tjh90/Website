"""Browser tests for in-place navigation keeping the Dark mode switch (feature 002, US3)."""

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, Route, expect

from tests.e2e.theme_helpers import (
    active_scheme,
    assert_nothing_stored,
    dark_mode_switch,
    is_drawer_open,
    is_same_document,
    mark_document,
    open_drawer,
)
from website.content import ABOUT, EXTERNAL_LINKS, HOME, tab_title


@pytest.fixture
def light_page(browser: Browser, base_url: str) -> Iterator[Page]:
    """A page in a fresh context whose device prefers the light theme."""
    context = browser.new_context(base_url=base_url, color_scheme="light")
    yield context.new_page()
    context.close()


def _switch_to_dark(page: Page) -> None:
    """Turn Dark mode on from the drawer."""
    open_drawer(page)
    dark_mode_switch(page).click()
    assert active_scheme(page) == "dark"


def _follow_drawer_link(page: Page, label: str, path: str) -> None:
    """Follow a drawer link and wait for the URL to change."""
    open_drawer(page)
    page.locator("#nav-drawer").get_by_role("link", name=label).click()
    page.wait_for_url(f"**{path}")
    expect(page.locator("h1")).to_have_text(ABOUT.title if path == ABOUT.path else HOME.title)


@pytest.mark.firefox
def test_switch_kept_when_following_link(light_page: Page) -> None:
    """Following a drawer link swaps the page in place and keeps the switch (FR-011, FR-021)."""
    page = light_page
    page.goto("/")
    mark_document(page)
    _switch_to_dark(page)
    _follow_drawer_link(page, ABOUT.nav_label, ABOUT.path)

    assert is_same_document(page)
    assert active_scheme(page) == "dark"
    expect(page).to_have_title(tab_title(ABOUT.title))
    drawer = page.locator("#nav-drawer")
    expect(drawer.locator(f'a[href="{ABOUT.path}"]')).to_have_attribute("aria-current", "page")
    expect(drawer.locator(f'a[href="{HOME.path}"]')).not_to_have_attribute("aria-current", "page")
    assert not is_drawer_open(page)
    expect(page.locator("h1")).to_be_focused()
    open_drawer(page)
    expect(dark_mode_switch(page)).to_be_checked()


@pytest.mark.firefox
def test_switch_kept_on_back_and_forward(light_page: Page) -> None:
    """Back and Forward show the right pages and keep the switch (FR-013)."""
    page = light_page
    page.goto("/")
    mark_document(page)
    _switch_to_dark(page)
    _follow_drawer_link(page, ABOUT.nav_label, ABOUT.path)

    page.go_back()
    page.wait_for_url(f"**{HOME.path}")
    expect(page.locator("h1")).to_have_text(HOME.title)
    assert active_scheme(page) == "dark"

    page.go_forward()
    page.wait_for_url(f"**{ABOUT.path}")
    expect(page.locator("h1")).to_have_text(ABOUT.title)
    assert active_scheme(page) == "dark"
    assert is_same_document(page)
    assert_nothing_stored(page)


@pytest.mark.firefox
def test_reload_returns_to_device_preference(light_page: Page) -> None:
    """A reload shows the device preference again (FR-014)."""
    page = light_page
    page.goto("/")
    _switch_to_dark(page)
    page.reload()
    assert active_scheme(page) == "light"
    open_drawer(page)
    expect(dark_mode_switch(page)).not_to_be_checked()


def test_typed_address_returns_to_device_preference(light_page: Page) -> None:
    """Opening an address directly shows the device preference (FR-014)."""
    page = light_page
    page.goto("/")
    _switch_to_dark(page)
    page.goto(ABOUT.path)
    assert active_scheme(page) == "light"


def test_links_without_javascript_load_in_full(browser: Browser, base_url: str) -> None:
    """Without JavaScript, links load whole pages showing the device preference (FR-015)."""
    context = browser.new_context(
        base_url=base_url, color_scheme="light", java_script_enabled=False
    )
    page = context.new_page()
    page.goto("/")
    _switch_to_dark(page)
    page.locator("#nav-drawer").get_by_role("link", name=ABOUT.nav_label).click()
    page.wait_for_url(f"**{ABOUT.path}")
    assert active_scheme(page) == "light"
    context.close()


def test_external_links_are_not_boosted(light_page: Page) -> None:
    """External links still open in a new tab and leave the site page alone."""
    page = light_page

    def fulfil_empty(route: Route) -> None:
        route.fulfill(status=200, body="", content_type="text/html")

    page.context.route("https://**/*", fulfil_empty)
    page.goto("/")
    mark_document(page)
    link = EXTERNAL_LINKS[0]
    with page.expect_popup() as popup_info:
        page.get_by_role("link", name=link.text).click()
    popup_info.value.close()
    assert is_same_document(page)
    assert page.url.endswith(HOME.path)


def test_switch_kept_when_leaving_not_found_page(light_page: Page) -> None:
    """Following the home link from the 404 page keeps the switch."""
    page = light_page
    page.goto("/does-not-exist")
    _switch_to_dark(page)
    page.keyboard.press("Escape")
    page.locator("main").get_by_role("link", name="Go to the home page").click()
    page.wait_for_url(f"**{HOME.path}")
    expect(page.locator("h1")).to_have_text(HOME.title)
    assert active_scheme(page) == "dark"
