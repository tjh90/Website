"""Browser tests for the navigation drawer and 404 page."""

import pytest
from playwright.sync_api import Browser, Locator, Page, expect

from website.content import ABOUT, ANASCRAMBLE, HOME, NOT_FOUND_TITLE, PAGES
from website.content import Page as SitePage

_TESTED_PAGES = (HOME, ANASCRAMBLE, ABOUT)
_PAGE_PARAMS = [pytest.param(p, id=p.name) for p in _TESTED_PAGES]


def menu_button(page: Page) -> Locator:
    """Return the drawer's menu button."""
    return page.get_by_role("button", name="Menu")


def drawer(page: Page) -> Locator:
    """Return the navigation drawer."""
    return page.locator("#nav-drawer")


def is_drawer_open(page: Page) -> bool:
    """Report whether the popover drawer is showing."""
    return bool(drawer(page).evaluate("el => el.matches(':popover-open')"))


def _navigate_via_drawer(page: Page, target: SitePage) -> None:
    """Open the drawer from the current page and follow the link to ``target``."""
    menu_button(page).click()
    drawer(page).get_by_role("link", name=target.nav_label).click()
    # Navigation may happen in place (htmx), so wait for the new page rather than a load event.
    page.wait_for_url(f"**{target.path}")
    expect(page.locator("h1")).to_have_text(target.title)


def test_drawer_closed_on_load(page: Page) -> None:
    """The drawer starts closed."""
    page.goto("/")
    assert not is_drawer_open(page)


def test_drawer_toggles_and_dismisses(page: Page) -> None:
    """The menu button toggles the drawer; Escape and outside clicks close it."""
    page.goto("/")
    menu_button(page).click()
    assert is_drawer_open(page)
    menu_button(page).click()
    assert not is_drawer_open(page)

    menu_button(page).click()
    page.keyboard.press("Escape")
    assert not is_drawer_open(page)

    menu_button(page).click()
    viewport = page.viewport_size
    assert viewport is not None
    page.mouse.click(viewport["width"] - 10, viewport["height"] - 10)
    assert not is_drawer_open(page)


def test_keyboard_operation_and_focus_return(page: Page) -> None:
    """Enter opens the drawer; Escape closes it and returns focus to the button."""
    page.goto("/")
    menu_button(page).focus()
    page.keyboard.press("Enter")
    assert is_drawer_open(page)
    page.keyboard.press("Escape")
    assert not is_drawer_open(page)
    expect(menu_button(page)).to_be_focused()


def _menu_expanded_state(page: Page) -> bool | None:
    """Read the menu button's expanded state from the browser's accessibility tree."""
    cdp = page.context.new_cdp_session(page)
    try:
        nodes = cdp.send("Accessibility.getFullAXTree")["nodes"]
    finally:
        cdp.detach()
    for node in nodes:
        if node.get("role", {}).get("value") == "button" and (
            node.get("name", {}).get("value") == "Menu"
        ):
            for prop in node.get("properties", []):
                if prop["name"] == "expanded":
                    return bool(prop["value"]["value"])
            return None
    return None


def test_expanded_state_is_exposed(page: Page) -> None:
    """Assistive technology is told whether the drawer is open (FR-009).

    Chromium-based browsers derive the expanded state of a ``popovertarget`` button natively,
    without an ``aria-expanded`` attribute. Playwright's ARIA snapshot only reads attributes, so
    the browser's own accessibility tree is queried over CDP instead.
    """
    page.goto("/")
    assert _menu_expanded_state(page) is False
    menu_button(page).click()
    assert _menu_expanded_state(page) is True


@pytest.mark.parametrize("target", _PAGE_PARAMS)
def test_navigate_to_each_page(page: Page, target: SitePage) -> None:
    """Choosing a page in the drawer navigates there with the drawer closed."""
    page.goto("/")
    _navigate_via_drawer(page, target)
    assert page.url.endswith(target.path)
    expect(page.locator("h1")).to_have_text(target.title)
    # Wait for the in-place swap: re-choosing the current page changes neither URL nor heading.
    expect(page.locator("#nav-drawer:popover-open")).to_have_count(0)
    # The closed drawer is hidden, so select by href rather than accessible role.
    expect(drawer(page).locator(f'a[href="{target.path}"]')).to_have_attribute(
        "aria-current", "page"
    )


def test_mobile_navigation(browser: Browser, base_url: str) -> None:
    """Navigation works on a phone-sized viewport without horizontal scroll."""
    context = browser.new_context(viewport={"width": 375, "height": 812}, base_url=base_url)
    page = context.new_page()
    page.goto("/")
    _navigate_via_drawer(page, ABOUT)
    assert page.url.endswith(ABOUT.path)
    assert not is_drawer_open(page)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    context.close()


@pytest.mark.parametrize("target", _PAGE_PARAMS)
def test_navigation_without_javascript(browser: Browser, base_url: str, target: SitePage) -> None:
    """The drawer and links work with JavaScript disabled (FR-010)."""
    context = browser.new_context(java_script_enabled=False, base_url=base_url)
    page = context.new_page()
    page.goto("/")
    menu_button(page).click()
    expect(drawer(page)).to_be_visible()
    menu_button(page).click()
    expect(drawer(page)).to_be_hidden()
    _navigate_via_drawer(page, target)
    assert page.url.endswith(target.path)
    context.close()


def test_not_found_page(page: Page, base_url: str) -> None:
    """The 404 page keeps the layout and links home."""
    response = page.goto("/does-not-exist")
    assert response is not None
    assert response.status == 404
    expect(page.locator("h1")).to_have_text(NOT_FOUND_TITLE)
    page.locator("main").get_by_role("link").first.click()
    page.wait_for_url(f"{base_url}/")
    expect(page.locator("h1")).to_have_text(HOME.title)


def test_every_page_in_registry_is_tested() -> None:
    """Guard: the parametrised pages match the registry."""
    assert {p.name for p in PAGES} == {p.name for p in _TESTED_PAGES}
