"""Automated accessibility checks with axe-core (FR-018, SC-005)."""

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page

_AXE = Axe()
_BLOCKING_IMPACTS = {"serious", "critical"}


@pytest.mark.parametrize("path", ["/", "/about", "/does-not-exist"])
@pytest.mark.parametrize("drawer_open", [False, True], ids=["drawer-closed", "drawer-open"])
def test_no_serious_violations(page: Page, path: str, *, drawer_open: bool) -> None:
    """Pages have no serious or critical axe violations, with the drawer open or closed."""
    page.goto(path)
    if drawer_open:
        page.get_by_role("button", name="Menu").click()
    results = _AXE.run(page)
    blocking = [v for v in results.response["violations"] if v.get("impact") in _BLOCKING_IMPACTS]
    assert not blocking, results.generate_report()
