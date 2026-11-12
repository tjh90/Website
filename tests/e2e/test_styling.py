"""Browser tests for layout and styling requirements."""

from playwright.sync_api import FloatRect, Page

from website.content import EXTERNAL_LINKS


def _box(page: Page, selector: str) -> FloatRect:
    """Return the bounding box of the first element matching ``selector``."""
    box = page.locator(selector).first.bounding_box()
    assert box is not None, selector
    return box


def _style(page: Page, selector: str, prop: str) -> str:
    """Return a computed style property of the first element matching ``selector``."""
    return str(page.locator(selector).first.evaluate(f"el => getComputedStyle(el).{prop}"))


def test_header_title_is_centred(page: Page) -> None:
    """The page title is centred in the header bar."""
    page.goto("/")
    header, title = _box(page, "header"), _box(page, "header h1")
    header_centre = header["x"] + header["width"] / 2
    title_centre = title["x"] + title["width"] / 2
    assert abs(header_centre - title_centre) <= 1


def test_link_icons_are_black(page: Page) -> None:
    """The home page link icons are black, whatever the link colour."""
    page.goto("/")
    for link in EXTERNAL_LINKS:
        icon = page.get_by_role("link", name=link.text).locator("svg")
        assert icon.evaluate("el => getComputedStyle(el).color") == "rgb(0, 0, 0)"


def test_links_are_indented_from_heading(page: Page) -> None:
    """The link list starts to the right of the "Links:" heading."""
    page.goto("/")
    assert _box(page, ".links li")["x"] > _box(page, ".links h2")["x"]


def test_section_headings_share_indentation(page: Page) -> None:
    """Headings on the About page line up with the home page's "Links:" heading."""
    page.goto("/")
    home_x = _box(page, "main h2")["x"]
    page.goto("/about")
    for heading in page.locator("main h2").all():
        box = heading.bounding_box()
        assert box is not None
        assert box["x"] == home_x


def test_menu_current_and_hover_highlights(page: Page) -> None:
    """The current menu item has a blue background; hovered items a lighter one, no underline."""
    page.goto("/")
    page.get_by_role("button", name="Menu").click()
    current = '#nav-drawer a[aria-current="page"]'
    other = "#nav-drawer a:not([aria-current])"
    assert _style(page, current, "backgroundColor") == "rgb(26, 79, 191)"
    assert _style(page, other, "backgroundColor") == "rgba(0, 0, 0, 0)"
    page.locator(other).hover()
    assert _style(page, other, "backgroundColor") == "rgb(219, 230, 255)"
    assert "underline" not in _style(page, other, "textDecorationLine")


def test_menu_items_span_drawer_width(page: Page) -> None:
    """Menu item highlights run edge to edge across the drawer."""
    page.emulate_media(reduced_motion="reduce")  # Measure the drawer without its slide-in.
    page.goto("/")
    page.get_by_role("button", name="Menu").click()
    drawer = _box(page, "#nav-drawer")
    for link in page.locator("#nav-drawer a").all():
        box = link.bounding_box()
        assert box is not None
        assert box["x"] == drawer["x"]
        assert box["width"] == drawer["width"]


def test_menu_items_pinned_to_top_and_bottom(page: Page) -> None:
    """Home sits flush at the top of the drawer and About flush at the bottom."""
    page.emulate_media(reduced_motion="reduce")  # Measure the drawer without its slide-in.
    page.goto("/")
    page.get_by_role("button", name="Menu").click()
    drawer = _box(page, "#nav-drawer")
    home = _box(page, '#nav-drawer a[href="/"]')
    about = _box(page, '#nav-drawer a[href="/about"]')
    assert home["y"] == drawer["y"]
    assert about["y"] + about["height"] == drawer["y"] + drawer["height"]
