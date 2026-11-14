"""Browser tests for the Recipes pages (feature 004)."""

import re

import pytest
from playwright.sync_api import Browser, Locator, Page, expect

_ALL = ["Aperol Spritz", "French 75", "Full English", "Moscow Mule"]


def _names(page: Page) -> Locator:
    """Return the recipe links in the results."""
    return page.locator("#recipe-results .recipe-list a")


def _no_page_scroll(page: Page, width: int) -> bool:
    """Report whether the page fits the viewport width."""
    return int(page.evaluate("document.documentElement.scrollWidth")) <= width


# --- Browse (US1) ----------------------------------------------------------------------------


def test_browse_to_a_recipe_and_back(page: Page) -> None:
    """The drawer leads to the list, a recipe opens, and "All recipes" returns."""
    page.goto("/")
    page.get_by_role("button", name="Menu").click()
    page.locator("#nav-drawer").get_by_role("link", name="Recipes").click()
    page.wait_for_url("**/recipes")
    expect(_names(page)).to_have_text(_ALL)

    page.get_by_role("link", name="French 75").click()
    page.wait_for_url("**/recipes/french-75")
    expect(page.locator("h1")).to_have_text("French 75")
    expect(page.locator(".method ol > li")).to_have_count(4)

    page.get_by_role("link", name="All recipes").click()
    page.wait_for_url("**/recipes")
    expect(_names(page)).to_have_text(_ALL)


@pytest.mark.firefox
def test_narrow_screens(browser: Browser, base_url: str) -> None:
    """At 320 px nothing scrolls sideways and the method sits below the ingredients."""
    context = browser.new_context(base_url=base_url, viewport={"width": 320, "height": 800})
    page = context.new_page()
    page.goto("/recipes")
    assert _no_page_scroll(page, 320)
    page.goto("/recipes/french-75")
    assert _no_page_scroll(page, 320)
    ingredients = page.locator(".recipe-ingredients").bounding_box()
    method = page.locator(".recipe-method").bounding_box()
    assert ingredients is not None
    assert method is not None
    assert method["y"] >= ingredients["y"] + ingredients["height"]
    context.close()


@pytest.mark.firefox
def test_wide_recipe_page_has_two_columns(browser: Browser, base_url: str) -> None:
    """At 1280 px the method is to the right of the ingredients card."""
    context = browser.new_context(base_url=base_url, viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.goto("/recipes/french-75")
    ingredients = page.locator(".recipe-ingredients").bounding_box()
    method = page.locator(".recipe-method").bounding_box()
    assert ingredients is not None
    assert method is not None
    assert method["x"] >= ingredients["x"] + ingredients["width"]
    assert abs(method["y"] - ingredients["y"]) < 40
    context.close()


# --- Filter (US3) ----------------------------------------------------------------------------


def test_typing_filters_live_and_keeps_focus(page: Page) -> None:
    """Typing in Name updates the list in place, keeps focus and updates the URL."""
    page.goto("/recipes")
    page.evaluate("window.__marker = true")
    name = page.get_by_label("Name")
    name.press_sequentially("spr")
    expect(_names(page)).to_have_text(["Aperol Spritz"])
    expect(page).to_have_url(re.compile(r"name=spr"))
    expect(name).to_be_focused()
    assert page.evaluate("window.__marker === true"), "the page was reloaded"


def test_type_checkbox_filters(page: Page) -> None:
    """Ticking a type shows only that type."""
    page.goto("/recipes")
    page.get_by_label("Breakfast").check()
    expect(_names(page)).to_have_text(["Full English"])


def test_unknown_ingredient_matches_nothing(page: Page) -> None:
    """An ingredient not in the master list finds nothing."""
    page.goto("/recipes")
    page.get_by_label("Ingredient").press_sequentially("limes")
    expect(page.get_by_role("status")).to_have_text("No matching recipes.")
    expect(_names(page)).to_have_count(0)


def test_filtered_url_restores_filters_and_clear_resets(page: Page) -> None:
    """A filtered URL shows its filters; "Clear filters" resets list and controls."""
    page.goto("/recipes?type=drink&ingredient=gin")
    expect(_names(page)).to_have_text(["French 75"])
    expect(page.get_by_label("Drink")).to_be_checked()
    expect(page.get_by_label("Ingredient")).to_have_value("gin")

    page.get_by_role("link", name="Clear filters").click()
    page.wait_for_url(re.compile(r"/recipes$"))
    expect(_names(page)).to_have_text(_ALL)
    expect(page.get_by_label("Drink")).not_to_be_checked()
    expect(page.get_by_label("Ingredient")).to_have_value("")


def test_fast_typing_ends_with_latest_results(page: Page) -> None:
    """Stale responses never win over the latest one."""
    page.goto("/recipes")
    page.get_by_label("Name").focus()
    page.keyboard.type("french", delay=20)
    expect(_names(page)).to_have_text(["French 75"])
    expect(page).to_have_url(re.compile(r"name=french"))


def test_filter_button_hidden_with_javascript(page: Page) -> None:
    """Live filtering makes the Filter button unnecessary, so it is hidden."""
    page.goto("/recipes")
    expect(page.get_by_role("button", name="Filter", exact=True)).to_be_hidden()


@pytest.mark.firefox
def test_filters_work_without_javascript(browser: Browser, base_url: str) -> None:
    """Without JavaScript the Filter button appears and submits the form."""
    context = browser.new_context(base_url=base_url, java_script_enabled=False)
    page = context.new_page()
    page.goto("/recipes")
    button = page.get_by_role("button", name="Filter", exact=True)
    expect(button).to_be_visible()
    page.get_by_label("Ingredient").fill("gin")
    button.click()
    page.wait_for_url(re.compile(r"ingredient=gin"))
    expect(_names(page)).to_have_text(["French 75"])
    context.close()


@pytest.mark.firefox
def test_phone_filters_collapse(browser: Browser, base_url: str) -> None:
    """On a phone the filters start collapsed behind a toggle that counts active filters."""
    context = browser.new_context(base_url=base_url, viewport={"width": 390, "height": 844})
    page = context.new_page()
    page.goto("/recipes")
    drink = page.get_by_label("Drink")
    expect(drink).to_be_hidden()
    toggle = page.locator(".recipe-filters-panel > summary")
    toggle.click()
    expect(drink).to_be_visible()
    drink.check()
    expect(_names(page)).to_have_text(["Aperol Spritz", "French 75", "Moscow Mule"])
    expect(toggle).to_have_text(re.compile(r"^\s*Filters · 1 active\s*$"))
    context.close()


@pytest.mark.firefox
def test_wide_filters_always_open(browser: Browser, base_url: str) -> None:
    """On a wide screen the filters are a sidebar with no toggle."""
    context = browser.new_context(base_url=base_url, viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.goto("/recipes")
    expect(page.get_by_label("Drink")).to_be_visible()
    expect(page.get_by_label("Name")).to_be_visible()
    expect(page.locator(".recipe-filters-panel > summary")).to_be_hidden()
    context.close()
