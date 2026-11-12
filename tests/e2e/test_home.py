"""Browser tests for the home page."""

import re

import pytest
from playwright.sync_api import Browser, Page, Route, expect

from website.content import EXTERNAL_LINKS, PAINTING_ALT, SITE_TITLE, ExternalLink


def _stub_external(route: Route) -> None:
    """Answer outbound requests locally so tests do not depend on third parties."""
    route.fulfill(status=200, content_type="text/html", body="<p>stub</p>")


def test_home_loads(page: Page) -> None:
    """The home page loads with the site title."""
    response = page.goto("/")
    assert response is not None
    assert response.ok
    expect(page).to_have_title(SITE_TITLE)


@pytest.mark.parametrize("link", EXTERNAL_LINKS, ids=lambda link: link.text)
def test_link_href(page: Page, link: ExternalLink) -> None:
    """Each link points at its destination."""
    page.goto("/")
    expect(page.get_by_role("link", name=link.text)).to_have_attribute("href", link.url)


@pytest.mark.parametrize("link", EXTERNAL_LINKS, ids=lambda link: link.text)
def test_link_opens_in_new_tab(page: Page, link: ExternalLink) -> None:
    """Clicking a link opens a popup and leaves the site open."""
    page.context.route("https://**", _stub_external)
    page.goto("/")
    original_url = page.url
    with page.expect_popup() as popup_info:
        page.get_by_role("link", name=link.text).click()
    # Sites may redirect www to the bare domain (as the reference tests allowed for).
    expected = re.compile(re.escape(link.url).replace(r"www\.", r"(www\.)?"))
    popup_info.value.wait_for_url(expected, wait_until="commit")
    assert page.url == original_url


def test_painting_visible(page: Page) -> None:
    """The painting is shown with its alt text."""
    page.goto("/")
    expect(page.get_by_role("img", name=PAINTING_ALT)).to_be_visible()


@pytest.mark.parametrize(
    ("width", "height", "side_by_side"),
    [(1920, 1080, True), (1280, 800, True), (320, 640, False)],
)
def test_layout(
    browser: Browser, base_url: str, width: int, height: int, *, side_by_side: bool
) -> None:
    """Links and painting sit side by side on wide screens and stack on narrow ones."""
    context = browser.new_context(viewport={"width": width, "height": height}, base_url=base_url)
    page = context.new_page()
    page.goto("/")
    links_box = page.locator(".links").bounding_box()
    image_box = page.get_by_role("img", name=PAINTING_ALT).bounding_box()
    assert links_box is not None
    assert image_box is not None
    if side_by_side:
        assert image_box["x"] >= links_box["x"] + links_box["width"] - 1
    else:
        assert image_box["y"] >= links_box["y"] + links_box["height"] - 1
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    context.close()
