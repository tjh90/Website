"""Browser tests for the Anascramble page."""

import itertools
import re
from collections.abc import Callable
from typing import Final

import pytest
from playwright.sync_api import Browser, Locator, Page, expect

_PATH: Final = "/anascramble"
_FEEDBACK_TIMEOUT: Final = 1_000  # SC-002: feedback well within a second on localhost.


def _letters(page: Page) -> Locator:
    """The "Letters to scramble" field."""
    return page.get_by_role("textbox", name="Letters to scramble")


def _scramble_button(page: Page) -> Locator:
    """The "Scramble!" button."""
    return page.get_by_role("button", name="Scramble!")


def _placed(page: Page) -> Locator:
    """The scrambled letters."""
    return page.locator("#scramble text")


# Ink box of each scrambled letter in SVG user units, from the font's real glyph metrics. The SVG
# bounding box would use the font's (much taller) line box, so it cannot show visual overlaps.
_INK_BOXES_JS: Final = """
async svg => {
  await document.fonts.ready;
  const style = getComputedStyle(svg.querySelector('text'));
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.font = `${style.fontSize} ${style.fontFamily}`;
  return [...svg.querySelectorAll('text')].map(t => {
    const m = ctx.measureText(t.textContent);
    const x = parseFloat(t.getAttribute('x')), y = parseFloat(t.getAttribute('y'));
    const start = x - m.width / 2;
    const baseline = y + (m.fontBoundingBoxAscent - m.fontBoundingBoxDescent) / 2;
    return [start - m.actualBoundingBoxLeft, baseline - m.actualBoundingBoxAscent,
            start + m.actualBoundingBoxRight, baseline + m.actualBoundingBoxDescent];
  });
}
"""


def _ink_boxes(page: Page) -> list[tuple[float, float, float, float]]:
    """Ink boxes (left, top, right, bottom) of the scrambled letters, in SVG user units."""
    return [tuple(box) for box in page.locator("#scramble").evaluate(_INK_BOXES_JS)]


def _view_box(page: Page) -> tuple[float, float, float, float]:
    """The scramble SVG's view box as (left, top, right, bottom)."""
    view_box = page.locator("#scramble").get_attribute("viewBox")
    assert view_box is not None
    x, y, w, h = (float(v) for v in view_box.split())
    return (x, y, x + w, y + h)


def _assert_inside_without_overlap(page: Page) -> None:
    """Every letter's ink is inside the view box and no two letters' ink overlaps (FR-006)."""
    assert page.evaluate("""document.fonts.check('32px "Rock Salt"')""")
    left, top, right, bottom = _view_box(page)
    boxes = _ink_boxes(page)
    for box in boxes:
        assert left <= box[0], box
        assert box[2] <= right, box
        assert top <= box[1], box
        assert box[3] <= bottom, box
    for a, b in itertools.combinations(boxes, 2):
        overlap = min(min(a[2], b[2]) - max(a[0], b[0]), min(a[3], b[3]) - max(a[1], b[1]))
        assert overlap <= 0, (a, b)


def _positions(page: Page) -> list[tuple[str, str]]:
    """The (x, y) attributes of every scrambled letter, sorted."""
    return sorted(
        page.locator("#scramble text").evaluate_all(
            "els => els.map(e => [e.getAttribute('x'), e.getAttribute('y')])"
        )
    )


def _eventually(page: Page, condition: Callable[[], bool]) -> None:
    """Wait up to the feedback timeout for a condition to hold."""
    for _ in range(_FEEDBACK_TIMEOUT // 50):
        if condition():
            return
        page.wait_for_timeout(50)
    assert condition()


def _type_letters(page: Page, text: str) -> None:
    """Type into the letters field and wait for the server's response to settle."""
    _letters(page).press_sequentially(text)
    page.wait_for_load_state("networkidle")


def _scramble(page: Page, text: str) -> None:
    """Enter letters and press "Scramble!"."""
    _type_letters(page, text)
    _scramble_button(page).click()
    expect(_placed(page)).to_have_count(len(text), timeout=_FEEDBACK_TIMEOUT)


def test_empty_page(page: Page) -> None:
    """The button starts disabled and the scramble area empty (US1 scenario 1)."""
    page.goto(_PATH)
    expect(_scramble_button(page)).to_be_disabled()
    expect(_placed(page)).to_have_count(0)
    expect(page.get_by_text("Solution:")).to_be_hidden()


def test_button_enables_at_three_letters(page: Page) -> None:
    """Two letters keep the button disabled; the third enables it (US1 scenario 2)."""
    page.goto(_PATH)
    _type_letters(page, "le")
    expect(_scramble_button(page)).to_be_disabled()
    _type_letters(page, "t")
    expect(_scramble_button(page)).to_be_enabled(timeout=_FEEDBACK_TIMEOUT)


def test_disallowed_characters_are_removed(page: Page) -> None:
    """Digits and punctuation disappear, and a 31st letter is not entered (US1 scenario 3)."""
    page.goto(_PATH)
    _type_letters(page, "le7!")
    expect(_letters(page)).to_have_value("LE", timeout=_FEEDBACK_TIMEOUT)
    _letters(page).fill("")
    _type_letters(page, "a" * 31)
    expect(_letters(page)).to_have_value("a" * 30)


def test_scramble_shows_letters_without_overlap(page: Page) -> None:
    """Every letter appears once, upper case, without overlaps, inside the area (scenario 4)."""
    page.goto(_PATH)
    _scramble(page, "anagrams")
    expect(_placed(page)).to_have_count(8)
    assert sorted(_placed(page).all_text_contents()) == sorted("ANAGRAMS")
    _assert_inside_without_overlap(page)


def test_scramble_again_changes_layout(page: Page) -> None:
    """Pressing again gives a new arrangement (US1 scenario 5)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    before = _positions(page)
    _scramble_button(page).click()
    _eventually(page, lambda: _positions(page) != before)


def test_editing_letters_clears_scramble(page: Page) -> None:
    """Editing the letters empties the scramble area (US1 scenario 6)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_letters(page, "s")
    expect(_placed(page)).to_have_count(0, timeout=_FEEDBACK_TIMEOUT)


def test_enter_scrambles(page: Page) -> None:
    """Pressing Enter in the letters field scrambles (US1 scenario 7)."""
    page.goto(_PATH)
    _type_letters(page, "letter")
    _letters(page).press("Enter")
    expect(_placed(page)).to_have_count(6, timeout=_FEEDBACK_TIMEOUT)


def test_nothing_is_stored(page: Page) -> None:
    """The letters stay out of the URL, and no cookies or storage are used (FR-018)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    assert page.url.endswith(_PATH)
    assert page.evaluate("document.cookie") == ""
    assert page.evaluate("localStorage.length + sessionStorage.length") == 0


def _solution(page: Page) -> Locator:
    """The solution field."""
    return page.get_by_role("textbox", name="Solution")


def _dimmed_letters(page: Page) -> list[str]:
    """The dimmed scrambled letters, sorted."""
    return sorted(page.locator("#scramble text.dimmed").all_text_contents())


def _type_solution(page: Page, text: str) -> None:
    """Type into the solution field and wait for the server's response to settle."""
    _solution(page).press_sequentially(text)
    page.wait_for_load_state("networkidle")


def test_no_solution_row_below_three_letters(page: Page) -> None:
    """The solution row is hidden until 3 letters are entered (US2 scenario 1)."""
    page.goto(_PATH)
    _type_letters(page, "le")
    expect(_solution(page)).to_be_hidden()


def test_solution_cells_before_scrambling(page: Page) -> None:
    """Six letters give six empty cells before scrambling (US2 scenario 2)."""
    page.goto(_PATH)
    _type_letters(page, "letter")
    expect(_solution(page)).to_be_visible(timeout=_FEEDBACK_TIMEOUT)
    expect(_solution(page)).to_have_value("")
    expect(_solution(page)).to_have_attribute("maxlength", "6")
    expect(page.locator("#solution-cells span")).to_have_count(6)


def test_repeated_letters_are_limited(page: Page) -> None:
    """Two T are accepted and dimmed; a third is refused (US2 scenario 3)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "tt")
    expect(_solution(page)).to_have_value("tt")
    _eventually(page, lambda: _dimmed_letters(page) == ["T", "T"])
    _type_solution(page, "t")
    expect(_solution(page)).to_have_value("TT", timeout=_FEEDBACK_TIMEOUT)
    assert _dimmed_letters(page) == ["T", "T"]


def test_unavailable_letter_is_refused(page: Page) -> None:
    """A letter that is not among the letters is removed (US2 scenario 4)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "z")
    expect(_solution(page)).to_have_value("", timeout=_FEEDBACK_TIMEOUT)


def test_deleting_a_letter_undims_it(page: Page) -> None:
    """Deleting an accepted letter makes it available again (US2 scenario 5)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "l")
    _eventually(page, lambda: _dimmed_letters(page) == ["L"])
    _solution(page).press("Backspace")
    _eventually(page, lambda: _dimmed_letters(page) == [])


def test_rescramble_keeps_solution(page: Page) -> None:
    """Scrambling again keeps the solution and dims it in the new layout (US2 scenario 6)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "le")
    before = _positions(page)
    _scramble_button(page).click()
    _eventually(page, lambda: _positions(page) != before)
    expect(_solution(page)).to_have_value(re.compile("^le$", re.IGNORECASE))
    assert _dimmed_letters(page) == ["E", "L"]


def test_editing_letters_resets_solution(page: Page) -> None:
    """Editing the letters resets the solution to empty cells (US2 scenario 7)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "le")
    _type_letters(page, "s")
    expect(_solution(page)).to_have_value("", timeout=_FEEDBACK_TIMEOUT)
    expect(page.locator("#solution-cells span")).to_have_count(7)


def test_solution_before_scrambling(page: Page) -> None:
    """Letters are accepted and refused before any scramble (US2 scenario 8)."""
    page.goto(_PATH)
    _type_letters(page, "letter")
    _type_solution(page, "tz")
    expect(_solution(page)).to_have_value(
        re.compile("^t$", re.IGNORECASE), timeout=_FEEDBACK_TIMEOUT
    )


# Centre of each character in the solution field (from the input's real font metrics) and of each
# cell, in CSS pixels.
_CHAR_AND_CELL_CENTRES_JS: Final = """
input => {
  const style = getComputedStyle(input);
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.font = `${style.fontSize} ${style.fontFamily}`;
  const advance = ctx.measureText('M').width + parseFloat(style.letterSpacing);
  const charWidth = ctx.measureText('M').width;
  const left =
    input.getBoundingClientRect().left + parseFloat(style.paddingLeft) - input.scrollLeft;
  const chars = [...input.value].map((_, i) => left + i * advance + charWidth / 2);
  const cells = [...document.querySelectorAll('#solution-cells span')].map(s => {
    const r = s.getBoundingClientRect();
    return r.left + r.width / 2;
  });
  return {chars, cells};
}
"""


def _caret(page: Page) -> int:
    """The caret position in the solution field."""
    return _solution(page).evaluate("e => e.selectionStart")


def _solution_has_focus(page: Page) -> bool:
    """Whether the solution field has keyboard focus."""
    return page.evaluate("document.activeElement?.id === 'solution'")


@pytest.mark.firefox
def test_each_character_sits_in_its_cell(page: Page) -> None:
    """Letters and blanks land in successive cells (US3 scenarios 1 and 3)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "l t")
    expect(_solution(page)).to_have_value(re.compile("^l t$", re.IGNORECASE))
    assert _caret(page) == 3
    centres = _solution(page).evaluate(_CHAR_AND_CELL_CENTRES_JS)
    for char_centre, cell_centre in zip(centres["chars"], centres["cells"], strict=False):
        assert abs(char_centre - cell_centre) < 3, centres


@pytest.mark.firefox
def test_backspace_steps_back(page: Page) -> None:
    """Backspace removes the previous character and moves back a cell (US3 scenario 2)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "le")
    _solution(page).press("Backspace")
    page.wait_for_load_state("networkidle")
    expect(_solution(page)).to_have_value(re.compile("^l$", re.IGNORECASE))
    assert _caret(page) == 1


@pytest.mark.firefox
def test_refused_letter_keeps_caret_and_focus(page: Page) -> None:
    """A refused letter is removed, and the caret stays in its cell with focus (scenario 4)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "l")
    _type_solution(page, "z")
    expect(_solution(page)).to_have_value(
        re.compile("^l$", re.IGNORECASE), timeout=_FEEDBACK_TIMEOUT
    )
    assert _solution_has_focus(page)
    assert _caret(page) == 1


@pytest.mark.firefox
def test_fast_typing_loses_nothing(page: Page) -> None:
    """Typing without pauses keeps every accepted letter in place (US3 scenario 5)."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _solution(page).focus()
    page.keyboard.type("letter", delay=0)
    page.wait_for_load_state("networkidle")
    expect(_solution(page)).to_have_value(re.compile("^letter$", re.IGNORECASE))
    _eventually(page, lambda: len(_dimmed_letters(page)) == 6)
    assert _solution_has_focus(page)


@pytest.mark.firefox
def test_full_solution_takes_no_more(page: Page) -> None:
    """Once every cell is filled, further characters are not entered (US3 scenario 6)."""
    page.goto(_PATH)
    _scramble(page, "the")
    _type_solution(page, "t e")
    _type_solution(page, "h")
    expect(_solution(page)).to_have_value(re.compile("^t e$", re.IGNORECASE))


def test_works_without_javascript(browser: Browser, base_url: str) -> None:
    """With JavaScript off, the form works by plain submission (FR-017)."""
    context = browser.new_context(base_url=base_url, java_script_enabled=False)
    page = context.new_page()
    page.goto(_PATH)
    _letters(page).fill("letter")
    _letters(page).press("Enter")
    page.wait_for_load_state()
    expect(_placed(page)).to_have_count(6)
    expect(_solution(page)).to_be_visible()
    _solution(page).fill("ttz")
    _solution(page).press("Enter")
    page.wait_for_load_state()
    expect(_solution(page)).to_have_value("TT")
    assert _dimmed_letters(page) == ["T", "T"]
    assert page.url.endswith(_PATH)
    context.close()


def test_fits_narrow_screen(browser: Browser, base_url: str) -> None:
    """At 320 px, 30 letters fit without page scroll and stay inside the area (SC-005, FR-007)."""
    context = browser.new_context(base_url=base_url, viewport={"width": 320, "height": 640})
    page = context.new_page()
    page.goto(_PATH)
    _scramble(page, "abcdefghijklmnopqrstuvwxyzabcd")
    expect(_solution(page)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth") <= 320
    area = page.locator("#scramble").bounding_box()
    assert area is not None
    assert area["width"] <= 320
    _assert_inside_without_overlap(page)
    context.close()


def test_theme_switch_keeps_puzzle(page: Page) -> None:
    """Switching theme keeps the letters, solution, layout and dimming."""
    page.goto(_PATH)
    _scramble(page, "letter")
    _type_solution(page, "tt")
    _eventually(page, lambda: len(_dimmed_letters(page)) == 2)
    before = (_positions(page), _dimmed_letters(page), _solution(page).input_value())
    page.get_by_role("button", name="Menu").click()
    page.get_by_role("switch", name="Dark mode").click()
    page.keyboard.press("Escape")
    assert (_positions(page), _dimmed_letters(page), _solution(page).input_value()) == before
    expect(_letters(page)).to_have_value("letter")


def test_disabled_button_does_not_scramble(page: Page) -> None:
    """Pressing the button with fewer than 3 letters scrambles nothing."""
    page.goto(_PATH)
    _type_letters(page, "le")
    _scramble_button(page).click(force=True)
    page.wait_for_load_state("networkidle")
    expect(_placed(page)).to_have_count(0)
    expect(_letters(page)).to_have_value("le")
