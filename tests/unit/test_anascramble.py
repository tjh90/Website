"""Unit tests for :mod:`website.anascramble`."""

import itertools
import random
import string

import pytest

from website.anascramble import (
    MAX_FIELD_LENGTH,
    MAX_LETTERS,
    MIN_SPACING,
    MIN_VIEW_SIZE,
    VIEW_MARGIN,
    PlacedLetter,
    Puzzle,
    claimed_map,
    sanitise_letters,
    sanitise_solution,
    scramble,
    view_box,
)


def _random_letters(rng: random.Random) -> str:
    """Pick a random 3-30 letter input."""
    return "".join(rng.choices(string.ascii_uppercase, k=rng.randint(3, MAX_LETTERS)))


# sanitise_letters


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("letter", "LETTER"),
        ("le7t!t er", "LETTER"),
        ("café", "CAF"),
        ("", ""),
        ("a" * 31, "A" * 30),
    ],
)
def test_sanitise_letters(raw: str, expected: str) -> None:
    """Letters are upper-cased, non A-Z characters dropped and the length capped (FR-004)."""
    assert sanitise_letters(raw) == expected


def test_sanitise_letters_bounds_raw_input_first() -> None:
    """Raw input is cut to MAX_FIELD_LENGTH before filtering, bounding the work done."""
    raw = "1" * MAX_FIELD_LENGTH + "abc"
    assert sanitise_letters(raw) == ""


# scramble


def test_scramble_places_every_letter_once() -> None:
    """Each letter is placed exactly once and keeps its source index."""
    letters = "LETTER"
    placed = scramble(letters, random.Random(1))
    assert sorted(p.index for p in placed) == list(range(len(letters)))
    assert all(p.letter == letters[p.index] for p in placed)


def test_scramble_never_overlaps() -> None:
    """Across 1,000 seeded runs, letters are MIN_SPACING apart on some axis (SC-003)."""
    inputs = random.Random(12345)
    for seed in range(1000):
        placed = scramble(_random_letters(inputs), random.Random(seed))
        for a, b in itertools.combinations(placed, 2):
            gap = max(abs(a.x - b.x), abs(a.y - b.y))
            assert gap >= MIN_SPACING - 0.1, seed


def test_scramble_is_reproducible_from_seed() -> None:
    """The same seed always gives the same arrangement (FR-008)."""
    assert scramble("ANAGRAM", random.Random(42)) == scramble("ANAGRAM", random.Random(42))


def test_scramble_differs_between_seeds() -> None:
    """Different seeds give different arrangements."""
    positions = {
        tuple(
            (p.x, p.y) for p in sorted(scramble("ANAGRAM", random.Random(s)), key=lambda p: p.index)
        )
        for s in range(10)
    }
    assert len(positions) == 10


def test_scramble_shuffles_reading_order() -> None:
    """The output order is not tied to the typed order (FR-019)."""
    orders = {tuple(p.index for p in scramble("ANAGRAM", random.Random(s))) for s in range(20)}
    assert len(orders) > 1


# view_box


def test_view_box_default() -> None:
    """With no letters the view box is the 400-unit square centred on the origin."""
    assert view_box([]) == (-200.0, -200.0, 400.0, 400.0)


def test_view_box_contains_every_letter() -> None:
    """Every letter is inside the view box with a margin, for any length (FR-006)."""
    inputs = random.Random(7)
    for seed in range(200):
        placed = scramble(_random_letters(inputs), random.Random(seed))
        min_x, min_y, width, height = view_box(placed)
        assert width == height >= MIN_VIEW_SIZE
        assert min_x == min_y == -width / 2
        eps = 1e-9  # Tolerate floating-point rounding at the edge.
        for p in placed:
            assert min_x + VIEW_MARGIN - eps <= p.x <= min_x + width - VIEW_MARGIN + eps
            assert min_y + VIEW_MARGIN - eps <= p.y <= min_y + height - VIEW_MARGIN + eps


def test_view_box_grows_for_far_letters() -> None:
    """A letter beyond the default square enlarges the view box."""
    min_x, _, size, _ = view_box([PlacedLetter(0, "A", 300.0, 0.0)])
    assert size == 2 * (300.0 + VIEW_MARGIN)
    assert min_x == -(300.0 + VIEW_MARGIN)


# Puzzle.from_form: letters and scramble intents


def _form(**overrides: str) -> dict[str, str]:
    """Build Puzzle.from_form keyword arguments with defaults."""
    values = {"letters": "", "solution": "", "seed": "", "arranged": ""}
    values.update(overrides)
    return values


def test_scramble_intent_creates_arrangement() -> None:
    """Scrambling 3+ letters creates a seeded arrangement of those letters."""
    puzzle = Puzzle.from_form(**_form(letters="letter"), intent="scramble")
    assert puzzle.letters == "LETTER"
    assert puzzle.seed is not None
    assert len(puzzle.arrangement) == 6


def test_scramble_intent_needs_three_letters() -> None:
    """Fewer than 3 letters cannot be scrambled."""
    puzzle = Puzzle.from_form(**_form(letters="le"), intent="scramble")
    assert puzzle.seed is None
    assert puzzle.arrangement == []


def test_scramble_intent_gives_new_seed_each_time() -> None:
    """Each press gives a new arrangement (FR-008)."""
    seeds = {Puzzle.from_form(**_form(letters="letter"), intent="scramble").seed for _ in range(5)}
    assert len(seeds) == 5


def test_letters_change_clears_arrangement() -> None:
    """Letters that differ from the arranged ones mean there is no arrangement (FR-009)."""
    puzzle = Puzzle.from_form(
        **_form(letters="letters", arranged="LETTER", seed="5"), intent="letters"
    )
    assert puzzle.seed is None


def test_unchanged_letters_keep_arrangement() -> None:
    """The arrangement is rebuilt from the seed while the letters are unchanged."""
    first = Puzzle.from_form(**_form(letters="letter", arranged="LETTER", seed="5"), intent=None)
    second = Puzzle.from_form(**_form(letters="letter", arranged="LETTER", seed="5"), intent=None)
    assert first.seed == 5
    assert first.arrangement == second.arrangement


@pytest.mark.parametrize("seed", ["", "abc", "-1", str(2**63), "1.5"])
def test_invalid_seed_means_no_arrangement(seed: str) -> None:
    """Tampered or missing seeds are treated as no arrangement (FR-016)."""
    puzzle = Puzzle.from_form(**_form(letters="letter", arranged="LETTER", seed=seed), intent=None)
    assert puzzle.seed is None


@pytest.mark.parametrize(("raw", "corrected"), [("le7", True), ("let", False), ("LeT", False)])
def test_letters_corrected(raw: str, *, corrected: bool) -> None:
    """Only real changes (not case) count as corrections."""
    assert Puzzle.from_form(**_form(letters=raw), intent="letters").letters_corrected is corrected


# claimed_map and sanitise_solution


@pytest.mark.parametrize(
    ("solution", "expected"),
    [
        ("TT", [False, False, True, True, False, False]),
        (" E", [False, True, False, False, False, False]),
        ("   ", [False] * 6),
        ("", [False] * 6),
        ("RETTEL", [True] * 6),
    ],
)
def test_claimed_map(solution: str, expected: list[bool]) -> None:
    """Each solution letter claims the first unclaimed match; blanks claim nothing."""
    assert claimed_map("LETTER", solution) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("tt", "TT"),
        ("TTT", "TT"),
        ("Z", ""),
        ("l e", "L E"),
        ("t7t", "TT"),
        ("letterxx", "LETTER"),
        ("  t", "  T"),
    ],
)
def test_sanitise_solution(raw: str, expected: str) -> None:
    """Refused letters and other characters are removed; length capped at the letters (FR-011)."""
    assert sanitise_solution(raw, "LETTER") == expected


def test_sanitise_solution_needs_three_letters() -> None:
    """There is no solution while fewer than 3 letters are entered."""
    assert sanitise_solution("le", "LE") == ""


# Puzzle.from_form: solution handling


_SEEDED = {"letters": "letter", "arranged": "LETTER", "seed": "5"}


def test_solution_intent_keeps_seed_and_sanitises() -> None:
    """Typing a solution keeps the arrangement and refuses unavailable letters."""
    puzzle = Puzzle.from_form(**_form(**_SEEDED, solution="ttt"), intent="solution")
    assert puzzle.seed == 5
    assert puzzle.solution == "TT"
    assert puzzle.solution_corrected
    assert puzzle.claimed == [False, False, True, True, False, False]


def test_case_change_is_not_a_correction() -> None:
    """Upper-casing alone does not count as a correction (the caret is left alone)."""
    puzzle = Puzzle.from_form(**_form(**_SEEDED, solution="tt"), intent="solution")
    assert puzzle.solution == "TT"
    assert not puzzle.solution_corrected


def test_scramble_keeps_solution() -> None:
    """Re-scrambling keeps the solution (US2 scenario 6)."""
    puzzle = Puzzle.from_form(**_form(**_SEEDED, solution="tt"), intent="scramble")
    assert puzzle.solution == "TT"
    assert puzzle.seed is not None


def test_letters_change_resets_solution() -> None:
    """Editing the letters clears the solution even if it would still fit (FR-013)."""
    puzzle = Puzzle.from_form(
        **_form(letters="letters", arranged="LETTER", seed="5", solution="TT"), intent="letters"
    )
    assert puzzle.solution == ""


def test_unknown_intent_behaves_like_solution() -> None:
    """Without a recognised intent, the current state is validated and rendered."""
    puzzle = Puzzle.from_form(**_form(**_SEEDED, solution="ttt"), intent=None)
    assert puzzle.seed == 5
    assert puzzle.solution == "TT"


def test_solution_before_scrambling() -> None:
    """Letters are accepted and refused the same way before any scramble (US2 scenario 8)."""
    puzzle = Puzzle.from_form(**_form(letters="letter", solution="tz"), intent="solution")
    assert puzzle.seed is None
    assert puzzle.solution == "T"
