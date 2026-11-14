"""Integration tests for the Recipes pages (contracts/http.md, contracts/page-layout.md)."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Final

import pytest
from fastapi.testclient import TestClient

from tests.conftest import FIXTURE_RECIPES
from website.app import create_app
from website.config import Settings
from website.cookbook import RecipeCollectionError

_ALL: Final = ["Aperol Spritz", "French 75", "Full English", "Moscow Mule"]
_VOID: Final = frozenset({"input", "meta", "link", "br", "img", "hr", "source", "path"})


@dataclass
class Node:
    """A parsed element.

    Attributes:
        tag: Tag name.
        attrs: Attribute values; valueless attributes map to ``""``.
        children: Child elements.
        parts: Text and child elements in document order.
    """

    tag: str
    attrs: dict[str, str]
    children: list[Node] = field(default_factory=list)
    parts: list[str | Node] = field(default_factory=list)

    @property
    def text(self) -> str:
        """All text inside the element, with whitespace collapsed."""
        pieces = [part if isinstance(part, str) else part.text for part in self.parts]
        return " ".join(" ".join(pieces).split())

    @property
    def classes(self) -> set[str]:
        """The element's classes."""
        return set(self.attrs.get("class", "").split())

    def iter(self) -> list[Node]:
        """Return this element and every descendant, in document order."""
        nodes = [self]
        for child in self.children:
            nodes += child.iter()
        return nodes

    def select(self, selector: str) -> list[Node]:
        """Find descendants by a simple ``tag``, ``.class``, ``#id`` or ``tag.class`` selector."""
        tag, _, rest = selector.partition(".") if "#" not in selector else ("", "", "")
        if selector.startswith("#"):
            return [n for n in self.iter()[1:] if n.attrs.get("id") == selector[1:]]
        return [
            n
            for n in self.iter()[1:]
            if (not tag or n.tag == tag) and (not rest or rest in n.classes)
        ]

    def one(self, selector: str) -> Node:
        """Find exactly one descendant matching ``selector``."""
        found = self.select(selector)
        assert len(found) == 1, f"{selector}: {len(found)} matches"
        return found[0]


class _TreeBuilder(HTMLParser):
    """Build a :class:`Node` tree."""

    def __init__(self) -> None:
        """Start with an empty document."""
        super().__init__()
        self.root = Node("document", {})
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Open an element."""
        node = Node(tag, {k: v or "" for k, v in attrs})
        self._stack[-1].children.append(node)
        self._stack[-1].parts.append(node)
        if tag not in _VOID:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        """Close the innermost open element with this tag."""
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        """Record text."""
        self._stack[-1].parts.append(data)


def parse(html: str) -> Node:
    """Parse a document.

    Args:
        html: The markup.

    Returns:
        The document root.
    """
    builder = _TreeBuilder()
    builder.feed(html)
    return builder.root


def _results(client: TestClient, url: str) -> tuple[Node, list[str]]:
    """Fetch a list page and return the results section and the names listed.

    Args:
        client: The test client.
        url: The list URL with any query.

    Returns:
        ``#recipe-results`` and the linked recipe names in order.
    """
    response = client.get(url)
    assert response.status_code == 200
    results = parse(response.text).one("#recipe-results")
    return results, [a.text for a in results.select("a") if "clear-filters" not in a.classes]


def _client_for(collection: str) -> TestClient:
    """Build a client for one of the fixture collections.

    Args:
        collection: Fixture folder name.

    Returns:
        A test client.
    """
    return TestClient(create_app(Settings(recipes_dir=FIXTURE_RECIPES / collection)))


# --- Browse (US1) ----------------------------------------------------------------------------


def test_list_page(client: TestClient) -> None:
    """Every recipe is listed alphabetically with its link, type and ingredient summary."""
    response = client.get("/recipes")
    assert response.status_code == 200
    document = parse(response.text)
    assert document.one("h1").text == "Recipes"
    results = document.one("#recipe-results")
    assert results.attrs["aria-label"] == "Recipes"
    status = results.select("p")[0]
    assert (status.attrs.get("role"), status.text) == ("status", "4 recipes")
    rows = results.select("li")
    assert [row.one("a").text for row in rows] == _ALL
    assert [row.one("a").attrs["href"] for row in rows] == [
        "/recipes/aperol-spritz",
        "/recipes/french-75",
        "/recipes/full-english",
        "/recipes/moscow-mule",
    ]
    assert [row.one(".recipe-type").text for row in rows] == [
        "Drink",
        "Drink",
        "Breakfast",
        "Drink",
    ]
    assert rows[1].one(".recipe-summary").text == (
        "Elderflower cordial · Gin · Ice cubes · Lime · Champagne, Prosecco or Cava"
    )
    assert not results.select(".clear-filters")


def test_recipe_page(client: TestClient) -> None:
    """French 75 shows its type, ingredients with labels and amounts, and a numbered method."""
    response = client.get("/recipes/french-75")
    assert response.status_code == 200
    document = parse(response.text)
    assert document.one("h1").text == "French 75"
    assert "<title>French 75 · Tim" in response.text
    article = document.one("article.recipe")
    assert article.one(".recipe-type").text == "Drink"
    back = article.one(".back-link")
    assert (back.text, back.attrs["href"]) == ("All recipes", "/recipes")
    body = article.one(".recipe-body")
    assert [section.attrs["class"] for section in body.children] == [
        "recipe-ingredients",
        "recipe-method",
    ]
    items = body.one(".ingredients").select("li")
    assert len(items) == 5
    assert items[0].one(".ingredient-name").text == "Elderflower cordial"
    assert items[0].one(".ingredient-amount").text == "10 ml"
    assert items[0].one(".ingredient-optional").text == "optional"
    assert not items[1].select(".ingredient-optional")
    assert items[-1].one(".ingredient-name").text == "Champagne, Prosecco or Cava"
    assert not items[-1].select(".ingredient-amount")
    assert len(body.one(".method").one("ol").select("li")) == 4


@pytest.mark.parametrize(("slug", "tag"), [("aperol-spritz", "p"), ("full-english", "ul")])
def test_method_formats(client: TestClient, slug: str, tag: str) -> None:
    """A paragraph method and a bulleted method render as written."""
    method = parse(client.get(f"/recipes/{slug}").text).one(".method")
    assert method.children[0].tag == tag


@pytest.mark.parametrize("path", ["/recipes/French-75", "/recipes/nope"])
def test_unknown_recipe_is_not_found(client: TestClient, path: str) -> None:
    """Unknown slugs, including a different case, give the site's 404 page."""
    response = client.get(path)
    assert response.status_code == 404
    assert "<h1>Page not found</h1>" in response.text


def test_empty_collection() -> None:
    """With no recipes the list says so and offers no filters."""
    with _client_for("empty") as client:
        results, names = _results(client, "/recipes")
        assert results.one("p").text == "No recipes yet."
        assert names == []
        assert "recipe-filters" not in client.get("/recipes").text


def test_unsafe_content_is_escaped() -> None:
    """Recipe content cannot inject markup (FR-019)."""
    with _client_for("unsafe") as client:
        html = client.get("/recipes/unsafe").text
    main = html[html.index("<main") :]
    assert "<script" not in main
    assert "&lt;script&gt;" in main
    assert 'href="javascript:' not in main
    assert "<img" not in main
    assert "Unsafe &lt;b&gt;name&lt;/b&gt;" in html


@pytest.mark.parametrize("path", ["/recipes", "/recipes/french-75", "/recipes?type=drink"])
def test_no_cookies_or_inline_styles(client: TestClient, path: str) -> None:
    """Recipe pages set no cookies and use no style attributes (CSP)."""
    response = client.get(path)
    assert "set-cookie" not in response.headers
    assert all("style" not in node.attrs for node in parse(response.text).iter())


# --- Start-up (US2) --------------------------------------------------------------------------


def test_invalid_collection_stops_start_up() -> None:
    """An invalid collection raises at app creation, naming every bad file (FR-010)."""
    with pytest.raises(RecipeCollectionError) as raised:
        create_app(Settings(recipes_dir=FIXTURE_RECIPES / "invalid"))
    report = str(raised.value)
    assert "bad-amount.md: " in report
    assert "missing-method.md: " in report


# --- Filter (US3) ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "expected", "status"),
    [
        ("", _ALL, "4 recipes"),
        ("type=drink", ["Aperol Spritz", "French 75", "Moscow Mule"], "3 recipes"),
        ("type=drink&type=breakfast", _ALL, "4 recipes"),
        ("name=FRENCH", ["French 75"], "1 recipe"),
        ("ingredient=prosecco", ["Aperol Spritz", "French 75"], "2 recipes"),
        ("ingredient=elderflower%20cordial", ["French 75"], "1 recipe"),
        ("ingredient=gin", ["French 75"], "1 recipe"),
        ("ingredient=limes", [], "No matching recipes."),
        ("type=breakfast&ingredient=gin", [], "No matching recipes."),
        ("type=bogus", _ALL, "4 recipes"),
        ("name=" + "x" * 300, [], "No matching recipes."),
    ],
)
def test_filters(client: TestClient, query: str, expected: list[str], status: str) -> None:
    """Filters from the query string narrow the results and never error."""
    results, names = _results(client, f"/recipes?{query}")
    assert names == expected
    assert results.select("p")[0].text == status
    tip = results.select(".no-results-tip")
    assert bool(tip) == (not expected)


def test_form_is_prefilled_and_escaped(client: TestClient) -> None:
    """The form shows the filters from the URL, escaped."""
    response = client.get('/recipes?type=breakfast&name=<b>"x&ingredient=gin')
    form = parse(response.text).one("#recipe-filters")
    boxes = {box.attrs["value"]: "checked" in box.attrs for box in form.select("input")[:2]}
    assert boxes == {"drink": False, "breakfast": True}
    assert form.one("#recipe-name").attrs["value"] == '<b>"x'
    assert 'value="&lt;b&gt;&#34;x"' in response.text
    assert form.one("#recipe-ingredient").attrs["value"] == "gin"


def test_filter_form_markup(client: TestClient) -> None:
    """The form matches the page-layout contract."""
    document = parse(client.get("/recipes").text)
    panel = document.one("details.recipe-filters-panel")
    assert "open" not in panel.attrs
    assert panel.one("summary").text == "Filters"
    form = panel.one("form")
    assert {k: v for k, v in form.attrs.items() if k != "class"} == {
        "id": "recipe-filters",
        "method": "get",
        "action": "/recipes",
        "role": "search",
        "aria-label": "Filter recipes",
        "hx-get": "/recipes",
        "hx-trigger": "submit, input delay:250ms",
        "hx-target": "#recipe-results",
        "hx-select": "#recipe-results",
        "hx-select-oob": "#filter-count",
        "hx-swap": "outerHTML",
        "hx-push-url": "true",
        "hx-sync": "this:replace",
    }
    assert form.one("legend").text == "Type"
    assert [label.text for label in form.select("label.type-option")] == ["Drink", "Breakfast"]
    for field_id in ("recipe-name", "recipe-ingredient"):
        box = form.one(f"#{field_id}")
        assert (box.attrs["type"], box.attrs["maxlength"], box.attrs["autocomplete"]) == (
            "search",
            "100",
            "off",
        )
    assert form.one("#recipe-ingredient").attrs["list"] == "ingredient-options"
    options = [o.attrs["value"] for o in form.one("#ingredient-options").select("option")]
    assert options[:3] == ["Aperol", "Bacon", "Bread"]
    assert len(options) == 17
    assert form.one("button.filter-submit").text == "Filter"


@pytest.mark.parametrize(
    ("query", "count", "clear"),
    [
        ("", "", False),
        ("type=drink&ingredient=gin", "· 2 active", True),
        ("name=x", "· 1 active", True),
    ],
)
def test_filter_count_and_clear_link(
    client: TestClient, query: str, count: str, clear: bool
) -> None:
    """The toggle counts active filters and "Clear filters" shows only when filtering."""
    document = parse(client.get(f"/recipes?{query}").text)
    assert document.one("#filter-count").text == count
    assert bool(document.one("#recipe-results").select(".clear-filters")) == clear


def test_htmx_request_gets_the_full_page(client: TestClient) -> None:
    """Htmx requests get the same page, from which the form selects the results."""
    response = client.get("/recipes?type=drink", headers={"HX-Request": "true"})
    assert 'id="recipe-results"' in response.text
    assert 'id="filter-count"' in response.text


def test_filter_button_hidden_when_scripting() -> None:
    """The stylesheet hides the Filter button when JavaScript runs."""
    css = (Path(__file__).parents[2] / "src/website/static/css/site.css").read_text("utf-8")
    assert "@media (scripting: enabled) {\n  .filter-submit {\n    display: none;" in css
