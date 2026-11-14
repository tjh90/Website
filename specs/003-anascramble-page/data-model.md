# Data Model: Anascramble Page

Nothing is persisted. These are the in-request values, all in `website.anascramble` except the form
model, which lives in `website.routes`.

## Constants

| Name | Value | Source |
|---|---|---|
| `MIN_LETTERS` | 3 | FR-004 |
| `MAX_LETTERS` | 30 | FR-004 |
| `BLANK` | `" "` | FR-011 (unknown letter in the solution) |
| `START_RADIUS` | 50.0 | Main's `DEFAULT_INITIAL_OFFSET` |
| `RADIUS_STEP` | 5.0 | Main's `DEFAULT_OFFSET_INCR` |
| `TRIES_PER_STEP` | 10 | Main (`tries % 10`) |
| `MIN_SPACING` | 58.0 | Square clearance; main's circular 50 let Rock Salt ink overlap (research R3) |
| `MIN_VIEW_SIZE` | 400.0 | Main's 400 px container (R2) |
| `VIEW_MARGIN` | 40.0 | Keeps glyph ink (up to 49 units, off-centre) fully inside the box |

## AnascrambleForm (Pydantic, request body)

Raw form submission. Every field is optional and lenient, so a tampered request is sanitised rather
than rejected (FR-016).

| Field | Type | Default | Notes |
|---|---|---|---|
| `letters` | `str` | `""` | Raw letters field |
| `solution` | `str` | `""` | Raw solution field |
| `seed` | `str` | `""` | Hidden; parsed to `int` in `[0, 2**63)` or treated as absent |
| `arranged` | `str` | `""` | Hidden; letters the shown arrangement was made from |
| `intent` | `Literal["letters", "solution", "scramble"] \| None` | `None` | Unknown values → `None`, treated as a full-page render with no new scramble |

Fields longer than 200 characters are truncated before sanitising, to bound work.

## Puzzle (domain, frozen dataclass)

The validated state that templates render.

| Field | Type | Rule |
|---|---|---|
| `letters` | `str` | Upper case A–Z only, at most `MAX_LETTERS` (`sanitise_letters`) |
| `solution` | `str` | Upper case letters and `BLANK`, at most `len(letters)`, refused letters removed (`sanitise_solution`); `""` if `letters` has fewer than `MIN_LETTERS` |
| `seed` | `int \| None` | Present only when an arrangement exists for the current `letters` |
| `letters_corrected` | `bool` | Raw letters differed from `letters` (after upper-casing) |
| `solution_corrected` | `bool` | Raw solution differed from `solution` (after upper-casing) |

Derived:

- `can_scramble`: `MIN_LETTERS <= len(letters) <= MAX_LETTERS`
- `shows_solution`: same condition as `can_scramble` (FR-010)
- `claimed`: `claimed_map(letters, solution)`
- `arrangement`: `scramble(letters, Random(seed))` when `seed` is not `None`, else empty

### State transitions (`Puzzle.from_form`)

| Intent | Rule |
|---|---|
| any | `letters` sanitised. If `arranged != letters` or `seed` invalid → `seed = None` and `solution = ""` (FR-009, FR-013) |
| `letters` | as above; the field changed, so normally `arranged != letters` and everything resets |
| `solution` | `solution` sanitised against `letters`; `seed` kept if still valid |
| `scramble` | if `can_scramble`: new `seed` from `secrets.randbits(63)`, `arranged = letters`, solution kept (sanitised); otherwise no seed |
| `None` | as `solution` (no-JS fallback renders the current state) |

Order matters: the reset check runs before the solution is sanitised, so editing the letters always
clears the solution even if the old solution would still be valid.

## PlacedLetter (domain, frozen dataclass)

| Field | Type | Notes |
|---|---|---|
| `index` | `int` | Position in `letters`; links to `claimed[index]` for dimming |
| `letter` | `str` | One upper-case letter |
| `x`, `y` | `float` | Centre, relative to the origin (0, 0) |

`scramble(letters, rng) -> list[PlacedLetter]` places letters in typed order (main's algorithm),
then shuffles the list with the same `rng` (FR-019 reading order). For a given seed the result is
identical every time (FR-008).

Invariants (tested, SC-003): every index appears once; any two centres are at least `MIN_SPACING`
apart horizontally or vertically.

## ViewBox (domain)

`view_box(placed) -> tuple[float, float, float, float]` returns `(min_x, min_y, size, size)`:
square, centred on the origin, with half-size `max(MIN_VIEW_SIZE / 2, max(|x|, |y|) + VIEW_MARGIN)`.
Every letter is therefore inside the box (FR-006).

## claimed_map

`claimed_map(letters, solution) -> list[bool]`, parallel to `letters`. For each non-blank letter in
`solution`, in order, mark the first unclaimed matching index. Same rule as main's
`computeClaimedMap`. `sanitise_solution` uses the same walk: a letter with no unclaimed match is
refused (removed).
