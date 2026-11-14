"""Browser tests for the navigation drawer's slide animations (feature 002, US4)."""

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, expect

from tests.e2e.theme_helpers import is_drawer_open, open_drawer
from website.content import ABOUT

_DRAWER = "#nav-drawer"

# Records, from the next animation frame on, whether any animation matched the predicate.
_WATCH_ANIMATIONS = """
(pseudoPrefix) => {
  window.__sawAnimation = false;
  const tick = () => {
    const seen = document.getAnimations().some(
      (a) => (a.effect?.pseudoElement ?? "").startsWith(pseudoPrefix)
    );
    if (seen) { window.__sawAnimation = true; } else { requestAnimationFrame(tick); }
  };
  requestAnimationFrame(tick);
}
"""

_DRAWER_TRANSITION_RUNNING = """
() => {
  const drawer = document.getElementById("nav-drawer");
  return document.getAnimations().some(
    (a) => a.transitionProperty === "translate" && a.effect?.target === drawer
  );
}
"""


@pytest.fixture
def reduced_motion_page(browser: Browser, base_url: str) -> Iterator[Page]:
    """A page in a context that prefers reduced motion."""
    context = browser.new_context(base_url=base_url, reduced_motion="reduce")
    yield context.new_page()
    context.close()


def _style(page: Page, prop: str, pseudo: str | None = None) -> str:
    """Return a computed style property of the drawer (or one of its pseudo-elements)."""
    return str(
        page.locator(_DRAWER).evaluate(
            "(el, [prop, pseudo]) => getComputedStyle(el, pseudo)[prop]", [prop, pseudo]
        )
    )


def _transition(page: Page, prop: str, pseudo: str | None = None) -> tuple[str, str]:
    """Return the computed (duration, timing function) of the drawer's transition for ``prop``."""
    names = [v.strip() for v in _style(page, "transitionProperty", pseudo).split(",")]
    durations = [v.strip() for v in _style(page, "transitionDuration", pseudo).split(",")]
    timings = [v.strip() for v in _style(page, "transitionTimingFunction", pseudo).split(",")]
    index = names.index(prop)
    return durations[index], timings[index]


@pytest.mark.firefox
def test_drawer_timings(page: Page) -> None:
    """The drawer opens over 350 ms easing out and closes over 300 ms easing in (FR-023)."""
    page.goto("/")
    root = page.locator(":root")
    assert (
        root.evaluate("el => getComputedStyle(el).getPropertyValue('--drawer-open-duration')")
        .strip()
        .lower()
        == "350ms"
    )
    assert (
        root.evaluate("el => getComputedStyle(el).getPropertyValue('--drawer-close-duration')")
        .strip()
        .lower()
        == "300ms"
    )

    open_drawer(page)
    assert _transition(page, "translate") == ("0.35s", "ease-out")
    assert _transition(page, "opacity", "::backdrop") == ("0.35s", "ease-out")

    page.get_by_role("button", name="Menu").click()
    assert _transition(page, "translate") == ("0.3s", "ease-in")


@pytest.mark.firefox
@pytest.mark.parametrize("method", ["menu-button", "escape", "outside-click"])
def test_drawer_slides_out_however_closed(page: Page, method: str) -> None:
    """Closing by any method runs the slide-out transition (FR-022)."""
    page.goto("/")
    open_drawer(page)
    page.wait_for_timeout(500)  # Let the slide-in finish.
    match method:
        case "menu-button":
            page.get_by_role("button", name="Menu").click()
        case "escape":
            page.keyboard.press("Escape")
        case _:
            viewport = page.viewport_size
            assert viewport is not None
            page.mouse.click(viewport["width"] - 10, viewport["height"] - 10)
    assert page.evaluate(_DRAWER_TRANSITION_RUNNING)
    expect(page.locator(f"{_DRAWER}:popover-open")).to_have_count(0)


def test_drawer_slides_out_when_choosing_a_page(page: Page) -> None:
    """Choosing a page slides the old drawer out in a view transition (FR-022, FR-024).

    Chromium only: Playwright's Firefox does not expose view-transition animations the same way.
    """
    page.goto("/")
    open_drawer(page)
    page.evaluate(_WATCH_ANIMATIONS, "::view-transition-old(nav-drawer)")
    page.locator(_DRAWER).get_by_role("link", name=ABOUT.nav_label).click()
    page.wait_for_url(f"**{ABOUT.path}")
    page.wait_for_function("() => window.__sawAnimation === true", timeout=2000)
    expect(page.locator("h1")).to_have_text(ABOUT.title)
    expect(page.locator(f"{_DRAWER}:popover-open")).to_have_count(0)


@pytest.mark.firefox
def test_no_drawer_motion_when_reduced(reduced_motion_page: Page) -> None:
    """With reduced motion the drawer neither slides nor animates on navigation (FR-025)."""
    page = reduced_motion_page
    page.goto("/")
    open_drawer(page)
    assert not page.evaluate(_DRAWER_TRANSITION_RUNNING)
    page.get_by_role("button", name="Menu").click()
    assert not page.evaluate(_DRAWER_TRANSITION_RUNNING)

    open_drawer(page)
    page.evaluate(_WATCH_ANIMATIONS, "::view-transition")
    page.locator(_DRAWER).get_by_role("link", name=ABOUT.nav_label).click()
    page.wait_for_url(f"**{ABOUT.path}")
    expect(page.locator("h1")).to_have_text(ABOUT.title)
    page.wait_for_timeout(300)
    assert page.evaluate("window.__sawAnimation") is False


@pytest.mark.firefox
def test_rapid_toggle_ends_closed(page: Page) -> None:
    """Toggling twice mid-slide reverses smoothly and ends fully closed."""
    page.goto("/")
    menu = page.get_by_role("button", name="Menu")
    menu.click()
    menu.click()
    page.wait_for_timeout(500)
    assert not is_drawer_open(page)
    expect(page.locator(_DRAWER)).to_be_hidden()
