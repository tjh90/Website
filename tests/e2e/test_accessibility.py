"""Automated accessibility checks with axe-core (FR-018, SC-005; feature 002 FR-017, FR-020)."""

from typing import Literal

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Browser, Page

_AXE = Axe()
_BLOCKING_IMPACTS = {"serious", "critical"}


def _assert_no_blocking_violations(page: Page) -> None:
    """Run axe on the page and fail on serious or critical violations."""
    results = _AXE.run(page)
    blocking = [v for v in results.response["violations"] if v.get("impact") in _BLOCKING_IMPACTS]
    assert not blocking, results.generate_report()


@pytest.mark.parametrize("color_scheme", ["light", "dark"])
@pytest.mark.parametrize("path", ["/", "/about", "/does-not-exist"])
@pytest.mark.parametrize("drawer_open", [False, True], ids=["drawer-closed", "drawer-open"])
def test_no_serious_violations(
    browser: Browser,
    base_url: str,
    path: str,
    color_scheme: Literal["light", "dark"],
    *,
    drawer_open: bool,
) -> None:
    """Pages have no serious or critical axe violations in either theme, drawer open or closed."""
    context = browser.new_context(base_url=base_url, color_scheme=color_scheme)
    page = context.new_page()
    page.goto(path)
    if drawer_open:
        page.get_by_role("button", name="Menu").click()
        page.wait_for_timeout(400)  # Let the slide-in finish so contrast is measured at rest.
    _assert_no_blocking_violations(page)
    context.close()


def test_no_serious_violations_after_manual_switch(browser: Browser, base_url: str) -> None:
    """The manually switched dark theme also has no serious or critical violations."""
    context = browser.new_context(base_url=base_url, color_scheme="light")
    page = context.new_page()
    page.goto("/")
    page.get_by_role("button", name="Menu").click()
    page.get_by_role("switch", name="Dark mode").click()
    page.wait_for_timeout(400)
    _assert_no_blocking_violations(page)
    context.close()


@pytest.mark.parametrize("color_scheme", ["light", "dark"])
@pytest.mark.parametrize("state", ["empty", "scrambled", "dimmed"])
def test_anascramble_no_serious_violations(
    browser: Browser, base_url: str, color_scheme: Literal["light", "dark"], state: str
) -> None:
    """The Anascramble page passes axe before and after scrambling and with dimmed letters.

    The colour-contrast rule stays on: dimmed letters are exempt because they are marked
    inactive with aria-disabled (feature 003 FR-012, FR-020).
    """
    context = browser.new_context(base_url=base_url, color_scheme=color_scheme)
    page = context.new_page()
    page.goto("/anascramble")
    if state != "empty":
        page.locator("#letters").press_sequentially("letter")
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="Scramble!").click()
        page.locator("#scramble text").first.wait_for()
    if state == "dimmed":
        page.locator("#solution").press_sequentially("tt")
        page.locator("#scramble text.dimmed").nth(1).wait_for()
    _assert_no_blocking_violations(page)
    context.close()
