"""Domain logic for the Anascramble page.

Pure functions and value types only: no web framework or template imports, so everything here is
unit-testable without HTTP. Randomness always comes from an injected :class:`random.Random`.
"""

import math
import random
import secrets
import string
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal, Self

MIN_LETTERS: Final = 3
MAX_LETTERS: Final = 30
BLANK: Final = " "
START_RADIUS: Final = 50.0
RADIUS_STEP: Final = 5.0
TRIES_PER_STEP: Final = 10
MIN_SPACING: Final = 58.0
MIN_VIEW_SIZE: Final = 400.0
VIEW_MARGIN: Final = 40.0
MAX_FIELD_LENGTH: Final = 200
MAX_SEED: Final = 2**63

_LETTERS: Final = frozenset(string.ascii_uppercase)

type Intent = Literal["letters", "solution", "scramble"]
_INTENTS: Final[dict[str, Intent]] = {
    "letters": "letters",
    "solution": "solution",
    "scramble": "scramble",
}


def sanitise_letters(raw: str) -> str:
    """Reduce raw input to the letters that can be scrambled.

    Args:
        raw: The submitted letters field.

    Returns:
        At most ``MAX_LETTERS`` upper-case letters A-Z, in order.
    """
    upper = raw[:MAX_FIELD_LENGTH].upper()
    return "".join(c for c in upper if c in _LETTERS)[:MAX_LETTERS]


def claimed_map(letters: str, solution: str) -> list[bool]:
    """Work out which letters the solution uses.

    Each solution letter, in order, claims the first unclaimed matching letter. Blanks claim
    nothing. This is the reference implementation's rule.

    Args:
        letters: The upper-case letters to scramble.
        solution: The upper-case solution letters and blanks.

    Returns:
        A list parallel to ``letters``: true where that letter is used by the solution.
    """
    claimed = [False] * len(letters)
    for char in solution:
        for i, letter in enumerate(letters):
            if not claimed[i] and letter == char:
                claimed[i] = True
                break
    return claimed


def sanitise_solution(raw: str, letters: str) -> str:
    """Reduce raw input to an acceptable solution.

    Keeps letters and blanks only, refuses any letter that has no unclaimed match among
    ``letters`` (counting repeats), and caps the length at ``len(letters)``.

    Args:
        raw: The submitted solution field.
        letters: The sanitised letters to scramble.

    Returns:
        The upper-case solution, or ``""`` when there are too few letters for a solution.
    """
    if not MIN_LETTERS <= len(letters) <= MAX_LETTERS:
        return ""
    remaining = list(letters)
    kept: list[str] = []
    for char in raw[:MAX_FIELD_LENGTH].upper():
        if char == BLANK:
            kept.append(char)
        elif char in remaining:
            remaining.remove(char)
            kept.append(char)
    return "".join(kept)[: len(letters)]


@dataclass(frozen=True, slots=True)
class PlacedLetter:
    """A letter placed in the scramble area.

    Attributes:
        index: Position of the letter in the scrambled letters; links it to the solution.
        letter: The upper-case letter.
        x: Horizontal centre, relative to the centre of the area.
        y: Vertical centre, relative to the centre of the area.
    """

    index: int
    letter: str
    x: float
    y: float


def _too_close(point: tuple[float, float], others: list[tuple[float, float]]) -> bool:
    """Report whether a point is within ``MIN_SPACING`` of another, horizontally and vertically.

    A square (not circular) clearance matches the roughly square letters. At 32 units, Rock Salt
    letters are at most 49 units wide or tall, so a 58-unit square keeps their ink apart.
    """
    return any(
        abs(point[0] - x) < MIN_SPACING and abs(point[1] - y) < MIN_SPACING for x, y in others
    )


def scramble(letters: str, rng: random.Random) -> list[PlacedLetter]:
    """Place letters at random, non-overlapping positions clustered round the centre.

    Port of the reference implementation: each letter is put at a random angle on a circle; if
    it lands too close (within a ``MIN_SPACING`` square) to an earlier letter, a new angle is
    tried, and every ``TRIES_PER_STEP`` tries the circle grows by ``RADIUS_STEP``. The radius
    carries over between letters, so longer inputs spread further out. The result is then
    shuffled so that its order (which is the reading order for assistive technology) does not
    give the typed order away.

    Args:
        letters: The letters to place.
        rng: Source of randomness; seed it for reproducible arrangements.

    Returns:
        One placed letter per input letter, in shuffled order.
    """
    radius = START_RADIUS
    points: list[tuple[float, float]] = []
    placed: list[PlacedLetter] = []
    for index, letter in enumerate(letters):
        tries = 0
        while True:
            theta = math.tau * rng.random()
            point = (round(radius * math.sin(theta), 1), round(radius * math.cos(theta), 1))
            if not _too_close(point, points):
                break
            tries += 1
            if tries % TRIES_PER_STEP == 0:
                radius += RADIUS_STEP
        points.append(point)
        placed.append(PlacedLetter(index, letter, *point))
    rng.shuffle(placed)
    return placed


def view_box(placed: Sequence[PlacedLetter]) -> tuple[float, float, float, float]:
    """Compute a square SVG view box, centred on the origin, that contains every letter.

    Args:
        placed: The placed letters.

    Returns:
        ``(min_x, min_y, width, height)``, at least ``MIN_VIEW_SIZE`` wide, with every letter
        centre at least ``VIEW_MARGIN`` inside each edge.
    """
    reach = max((max(abs(p.x), abs(p.y)) for p in placed), default=0.0)
    half = max(MIN_VIEW_SIZE / 2, reach + VIEW_MARGIN)
    return (-half, -half, 2 * half, 2 * half)


def new_seed() -> int:
    """Create a seed for a new arrangement.

    Returns:
        A random integer in ``[0, MAX_SEED)``.
    """
    return secrets.randbits(63)


def parse_seed(raw: str) -> int | None:
    """Parse a submitted seed.

    Args:
        raw: The hidden seed field.

    Returns:
        The seed, or ``None`` if it is missing, malformed or out of range.
    """
    text = raw.strip()
    if not text.isascii() or not text.isdigit() or len(text) > len(str(MAX_SEED)):
        return None
    seed = int(text)
    return seed if seed < MAX_SEED else None


def parse_intent(raw: str) -> Intent | None:
    """Parse a submitted intent.

    Args:
        raw: The intent field.

    Returns:
        The intent, or ``None`` if it is not recognised.
    """
    return _INTENTS.get(raw)


@dataclass(frozen=True, slots=True)
class Puzzle:
    """The validated state of an Anascramble puzzle, as rendered by the templates.

    Attributes:
        letters: Upper-case letters to scramble.
        solution: Upper-case solution letters and blanks.
        seed: Seed of the arrangement currently shown, or ``None`` if there is none.
        letters_corrected: Whether the submitted letters had to be changed.
        solution_corrected: Whether the submitted solution had to be changed.
    """

    letters: str
    solution: str
    seed: int | None
    letters_corrected: bool
    solution_corrected: bool

    @classmethod
    def empty(cls) -> Self:
        """Create the puzzle shown on a freshly opened page.

        Returns:
            A puzzle with no letters, solution or arrangement.
        """
        return cls(
            letters="", solution="", seed=None, letters_corrected=False, solution_corrected=False
        )

    @classmethod
    def from_form(
        cls, *, letters: str, solution: str, seed: str, arranged: str, intent: Intent | None
    ) -> Self:
        """Validate a form submission and apply its intent.

        Args:
            letters: The letters field.
            solution: The solution field.
            seed: The hidden seed of the arrangement shown.
            arranged: The hidden letters that arrangement was made from.
            intent: What triggered the request, or ``None`` if unknown.

        Returns:
            The resulting puzzle.
        """
        clean_letters = sanitise_letters(letters)
        current_seed = parse_seed(seed)
        raw_solution = solution[:MAX_FIELD_LENGTH].upper()
        # The arrangement shown belongs to the letters it was made from; other letters have none
        # (FR-009).
        if arranged != clean_letters:
            current_seed = None
        # Editing the letters starts the solution again (FR-013). Without JavaScript the edit is
        # only visible as letters that differ from those of the arrangement shown.
        if intent == "letters" or (arranged and arranged != clean_letters):
            raw_solution = ""
        clean_solution = sanitise_solution(raw_solution, clean_letters)
        if intent == "scramble":
            can_scramble = MIN_LETTERS <= len(clean_letters) <= MAX_LETTERS
            current_seed = new_seed() if can_scramble else None
        return cls(
            letters=clean_letters,
            solution=clean_solution,
            seed=current_seed,
            letters_corrected=clean_letters != letters[:MAX_FIELD_LENGTH].upper(),
            solution_corrected=clean_solution != raw_solution,
        )

    @property
    def can_scramble(self) -> bool:
        """Whether there are enough letters to scramble."""
        return MIN_LETTERS <= len(self.letters) <= MAX_LETTERS

    @property
    def shows_solution(self) -> bool:
        """Whether the solution row is shown."""
        return self.can_scramble

    @property
    def arrangement(self) -> list[PlacedLetter]:
        """The placed letters of the arrangement shown, rebuilt from the seed."""
        if self.seed is None:
            return []
        # Not used for security: the seed only reproduces a layout of the visitor's own letters.
        return scramble(self.letters, random.Random(self.seed))  # noqa: S311

    @property
    def view_box(self) -> tuple[float, float, float, float]:
        """The scramble area's SVG view box."""
        return view_box(self.arrangement)

    @property
    def claimed(self) -> list[bool]:
        """Which letters are used by the solution, parallel to ``letters``."""
        return claimed_map(self.letters, self.solution)
