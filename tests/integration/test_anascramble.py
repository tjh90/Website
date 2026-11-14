"""Integration tests for the Anascramble page (contracts/http.md, contracts/page-layout.md)."""

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Final

from fastapi.testclient import TestClient


@dataclass
class Element:
    """A parsed start tag with its attributes and direct text.

    Attributes:
        tag: Tag name.
        attrs: Attribute values; valueless attributes map to ``""``.
        text: Text directly inside the element.
        depth: Nesting depth (0 for top-level elements).
    """

    tag: str
    attrs: dict[str, str]
    text: str = ""
    depth: int = 0


class _Collector(HTMLParser):
    """Collect every element of a document, in source order."""

    _VOID: Final = frozenset({"input", "meta", "link", "br", "img", "hr"})

    def __init__(self) -> None:
        """Start with no elements."""
        super().__init__()
        self.elements: list[Element] = []
        self._open: list[Element] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record a start tag."""
        element = Element(tag, {k: v or "" for k, v in attrs}, depth=len(self._open))
        self.elements.append(element)
        if tag not in self._VOID:
            self._open.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record a self-closing tag."""
        self.elements.append(Element(tag, {k: v or "" for k, v in attrs}, depth=len(self._open)))

    def handle_endtag(self, tag: str) -> None:
        """Close the innermost open element with this tag."""
        for i in range(len(self._open) - 1, -1, -1):
            if self._open[i].tag == tag:
                del self._open[i:]
                break

    def handle_data(self, data: str) -> None:
        """Attach text to the innermost open element."""
        if self._open:
            self._open[-1].text += data


def parse(html: str) -> list[Element]:
    """Parse HTML into a flat list of elements.

    Args:
        html: The document or fragment.

    Returns:
        Every element, in source order.
    """
    collector = _Collector()
    collector.feed(html)
    return collector.elements


def by_id(elements: list[Element], element_id: str) -> Element:
    """Find the single element with an id.

    Args:
        elements: Parsed elements.
        element_id: The id to look for.

    Returns:
        The element.
    """
    matches = [e for e in elements if e.attrs.get("id") == element_id]
    assert len(matches) == 1, f"expected one #{element_id}, found {len(matches)}"
    return matches[0]


def test_get_renders_empty_puzzle(client: TestClient) -> None:
    """The page renders an empty, inert form (FR-001, FR-003, FR-004, FR-010)."""
    response = client.get("/anascramble")
    assert response.status_code == 200
    assert "set-cookie" not in response.headers
    elements = parse(response.text)

    h1 = next(e for e in elements if e.tag == "h1")
    assert h1.text.strip() == "Anascramble"

    form = by_id(elements, "anascramble")
    assert form.attrs["method"] == "post"
    assert form.attrs["action"] == "/anascramble"
    assert form.attrs["hx-post"] == "/anascramble"
    assert form.attrs["hx-swap"] == "none"
    assert form.attrs["hx-sync"] == "this:replace"

    letters = by_id(elements, "letters")
    assert letters.attrs["maxlength"] == "30"
    assert letters.attrs["minlength"] == "3"
    assert letters.attrs["pattern"] == "[A-Za-z]{3,30}"
    assert "required" in letters.attrs
    assert letters.attrs["autocomplete"] == "off"
    assert letters.attrs["value"] == ""

    assert by_id(elements, "scramble-button").attrs.get("aria-disabled") == "true"
    assert "hidden" in by_id(elements, "solution-row").attrs
    scramble = by_id(elements, "scramble")
    assert scramble.attrs["aria-hidden"] == "true"
    assert not [e for e in elements if e.tag == "text"]


def test_page_order(client: TestClient) -> None:
    """Scramble area, solution row, letters field, then the button (FR-003)."""
    ids = [e.attrs.get("id") for e in parse(client.get("/anascramble").text)]
    order = ["scramble", "solution-row", "letters", "scramble-button"]
    assert [ids.index(i) for i in order] == sorted(ids.index(i) for i in order)


def test_no_inline_styles(client: TestClient) -> None:
    """No element carries a style attribute, which the CSP would block."""
    assert not [e for e in parse(client.get("/anascramble").text) if "style" in e.attrs]


_HX = {"HX-Request": "true"}


def _oob_ids(html: str) -> list[str]:
    """Ids of the top-level out-of-band fragments in an htmx response."""
    top = [e for e in parse(html) if e.depth == 0]
    assert all(e.attrs.get("hx-swap-oob") == "true" for e in top), [e.tag for e in top]
    return [e.attrs["id"] for e in top]


def _svg_markup(html: str) -> str:
    """The scramble SVG's markup within a response."""
    return html[html.index("<svg") : html.index("</svg>")]


def _letters_in_svg(elements: list[Element]) -> list[str]:
    """The letters drawn in the scramble area, in document order."""
    return [e.text for e in elements if e.tag == "text"]


def test_scramble_without_htmx_renders_full_page(client: TestClient) -> None:
    """A plain submission returns the whole page with the arrangement (FR-005, FR-017)."""
    response = client.post("/anascramble", data={"intent": "scramble", "letters": "letter"})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    elements = parse(response.text)
    assert any(e.tag == "h1" for e in elements)
    assert sorted(_letters_in_svg(elements)) == sorted("LETTER")
    seed = next(e for e in elements if e.attrs.get("name") == "seed").attrs["value"]
    assert seed.isdigit()
    assert next(e for e in elements if e.attrs.get("name") == "arranged").attrs["value"] == "LETTER"
    assert by_id(elements, "scramble").attrs["aria-label"] == "Scrambled letters"


def test_scramble_with_htmx_returns_fragments(client: TestClient) -> None:
    """An htmx submission returns only out-of-band fragments (contracts/http.md)."""
    response = client.post(
        "/anascramble", data={"intent": "scramble", "letters": "letter"}, headers=_HX
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "<h1" not in response.text
    assert "<html" not in response.text
    assert _oob_ids(response.text) == [
        "scramble",
        "puzzle-state",
        "scramble-button",
        "solution-row",
    ]
    assert len(_letters_in_svg(parse(response.text))) == 6


def test_letters_intent_corrects_and_disables(client: TestClient) -> None:
    """Disallowed characters are removed and short input disables the button (FR-004, R6)."""
    response = client.post(
        "/anascramble", data={"intent": "letters", "letters": "le7"}, headers=_HX
    )
    ids = _oob_ids(response.text)
    assert "letters" in ids
    elements = parse(response.text)
    assert by_id(elements, "letters").attrs["value"] == "LE"
    assert by_id(elements, "scramble-button").attrs.get("aria-disabled") == "true"
    assert not _letters_in_svg(elements)
    assert next(e for e in elements if e.attrs.get("name") == "seed").attrs["value"] == ""


def test_letters_intent_without_correction(client: TestClient) -> None:
    """Valid letters are not sent back, so the caret is left alone (FR-015)."""
    response = client.post(
        "/anascramble", data={"intent": "letters", "letters": "lette"}, headers=_HX
    )
    assert "letters" not in _oob_ids(response.text)
    assert "aria-disabled" not in by_id(parse(response.text), "scramble-button").attrs


def test_arrangement_is_rebuilt_from_seed(client: TestClient) -> None:
    """The same letters and seed always render the same scramble (R4)."""
    data = {"intent": "solution", "letters": "letter", "arranged": "LETTER", "seed": "99"}
    first = client.post("/anascramble", data=data, headers=_HX).text
    second = client.post("/anascramble", data=data, headers=_HX).text
    assert _svg_markup(first) == _svg_markup(second)
    assert len(_letters_in_svg(parse(first))) == 6


def test_tampered_input_is_handled(client: TestClient) -> None:
    """Malformed or oversized input never produces an error (FR-016)."""
    cases: list[dict[str, str]] = [
        {"letters": "a" * 10_000, "solution": "b" * 10_000, "intent": "scramble"},
        {"letters": "letter", "intent": "nonsense"},
        {"letters": "letter", "arranged": "LETTER", "seed": "abc", "intent": "solution"},
        {},
    ]
    for data in cases:
        for headers in ({}, _HX):
            response = client.post("/anascramble", data=data, headers=headers)
            assert response.status_code == 200, data


_SEEDED = {"letters": "letter", "arranged": "LETTER", "seed": "99"}


def _dimmed(elements: list[Element]) -> list[Element]:
    """The dimmed scrambled letters."""
    return [e for e in elements if e.tag == "text" and "dimmed" in e.attrs.get("class", "")]


def _positions(elements: list[Element]) -> list[tuple[str, str, str]]:
    """Each scrambled letter with its position, sorted."""
    return sorted((e.text, e.attrs["x"], e.attrs["y"]) for e in elements if e.tag == "text")


def test_solution_refusal_and_dimming(client: TestClient) -> None:
    """A third T is refused; two T are dimmed in the same layout (FR-011, FR-012)."""
    data = {**_SEEDED, "intent": "solution", "solution": "TTT"}
    response = client.post("/anascramble", data=data, headers=_HX)
    assert _oob_ids(response.text) == ["scramble", "puzzle-state", "scramble-button", "solution"]
    elements = parse(response.text)
    assert by_id(elements, "solution").attrs["value"] == "TT"
    dimmed = _dimmed(elements)
    assert [e.text for e in dimmed] == ["T", "T"]
    assert all(e.attrs.get("aria-disabled") == "true" for e in dimmed)
    plain = client.post("/anascramble", data={**data, "solution": ""}, headers=_HX)
    assert _positions(elements) == _positions(parse(plain.text))


def test_accepted_solution_is_not_sent_back(client: TestClient) -> None:
    """An accepted solution is not replaced, so the caret is untouched (FR-015)."""
    data = {**_SEEDED, "intent": "solution", "solution": "T E"}
    response = client.post("/anascramble", data=data, headers=_HX)
    assert "solution" not in _oob_ids(response.text)
    assert sorted(e.text for e in _dimmed(parse(response.text))) == ["E", "T"]


def test_letters_change_resets_solution_row(client: TestClient) -> None:
    """Changing the letters sends a fresh row sized to the new letters (FR-010, FR-013)."""
    data = {**_SEEDED, "letters": "letters", "intent": "letters", "solution": "TT"}
    response = client.post("/anascramble", data=data, headers=_HX)
    assert "solution-row" in _oob_ids(response.text)
    elements = parse(response.text)
    row = by_id(elements, "solution-row")
    assert "hidden" not in row.attrs
    solution = by_id(elements, "solution")
    assert solution.attrs["value"] == ""
    assert solution.attrs["maxlength"] == "7"
    cells = by_id(elements, "solution-cells")
    assert len([e for e in elements if e.tag == "span" and e.depth == cells.depth + 1]) == 7


def test_short_letters_hide_solution_row(client: TestClient) -> None:
    """With fewer than 3 letters the solution row is hidden (FR-010)."""
    response = client.post("/anascramble", data={"intent": "letters", "letters": "le"}, headers=_HX)
    assert "hidden" in by_id(parse(response.text), "solution-row").attrs


def test_no_js_scramble_keeps_solution(client: TestClient) -> None:
    """A plain re-scramble keeps the solution and dims its letters (US2 scenario 6)."""
    data = {**_SEEDED, "intent": "scramble", "solution": "tt"}
    elements = parse(client.post("/anascramble", data=data).text)
    assert by_id(elements, "solution").attrs["value"] == "TT"
    assert [e.text for e in _dimmed(elements)] == ["T", "T"]


def test_server_never_moves_focus(client: TestClient) -> None:
    """Accepted solution input is not sent back and nothing is autofocused (FR-015)."""
    data = {**_SEEDED, "intent": "solution", "solution": "LET"}
    response = client.post("/anascramble", data=data, headers=_HX)
    elements = parse(response.text)
    assert not [e for e in elements if e.attrs.get("id") == "solution"]
    assert not [e for e in elements if "autofocus" in e.attrs]
