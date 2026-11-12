"""Browser tests for the About page."""

from playwright.sync_api import Page, Route, expect

from tests.conftest import LIVE_REVISION
from website.content import ABOUT


def _stub_external(route: Route) -> None:
    """Answer outbound requests locally so tests do not depend on third parties."""
    route.fulfill(status=200, content_type="text/html", body="<p>stub</p>")


def test_reach_about_via_drawer(page: Page) -> None:
    """About is reachable from the home page in two clicks (SC-002)."""
    page.goto("/")
    page.get_by_role("button", name="Menu").click()
    page.locator("#nav-drawer").get_by_role("link", name=ABOUT.nav_label).click()
    page.wait_for_load_state()
    assert page.url.endswith(ABOUT.path)


def test_source_link_opens_in_new_tab(page: Page) -> None:
    """The source link points at the repository and opens a popup."""
    page.context.route("https://**", _stub_external)
    page.goto("/about")
    link = page.get_by_role("link", name="Source code on GitHub")
    expect(link).to_have_attribute("href", "https://github.com/tjh90/website")
    with page.expect_popup() as popup_info:
        link.click()
    popup_info.value.wait_for_url("https://github.com/tjh90/website**", wait_until="commit")


def test_revision_and_credits(page: Page) -> None:
    """The running revision and the credits are shown."""
    page.goto("/about")
    expect(page.get_by_role("link", name=LIVE_REVISION[:7])).to_have_attribute(
        "href", f"https://github.com/tjh90/website/tree/{LIVE_REVISION}"
    )
    expect(page.get_by_role("heading", name="Credits")).to_be_visible()


def test_no_cookies(page: Page) -> None:
    """Visiting the site stores no cookies (FR-016)."""
    page.goto("/")
    page.goto("/about")
    assert page.context.cookies() == []
