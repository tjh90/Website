---

description: "Task list for feature 003: Anascramble Page"
---

# Tasks: Anascramble Page

**Input**: Design documents from `specs/003-anascramble-page/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included. Constitution principle IV requires every feature to ship with tests. Within
each story, write the tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story, in spec order:
- US1, P1: scramble letters
- US2, P2: build the solution
- US3, P3: fast keyboard entry in the solution field

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: The user story this task belongs to (US1 to US3)
- Paths are relative to the repository root (single project, `src/` layout)

**Applies to every task**:
- Follow constitution III: type hints everywhere (`Final[...]` for module constants), Google-style
  docstrings on every public module, class and function, and Ruff and ty clean.
- Write no hand-written JavaScript (constitution II). htmx attributes use JSON values only: no
  `js:` prefixes and no trigger filters (`[...]`), because the CSP has no `'unsafe-eval'`.
  JavaScript in Playwright `evaluate()` calls inside tests is fine.
- No `style="..."` attributes anywhere (CSP `style-src 'self'`). All styling goes in
  `src/website/static/css/site.css`, using the existing `light-dark()` colour tokens.
- Locate elements by role and accessible name first (see
  [contracts/page-layout.md](contracts/page-layout.md)).
- Render pages and fragments with `website.templating.render()` so `Vary: HX-Request` is set.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: New dependency and the vendored font.

- [ ] T001 Run `uv add python-multipart` so `pyproject.toml` `[project].dependencies` and `uv.lock` include it (research R9). Confirm `uv lock --check` passes.
- [ ] T002 [P] Vendor the Rock Salt font (research R8): download `https://registry.npmjs.org/@fontsource/rock-salt/-/rock-salt-5.3.0.tgz` into a new empty scratch directory, extract it there, and copy `package/files/rock-salt-latin-400-normal.woff2` to `src/website/static/fonts/rock-salt-latin-400-normal.woff2` and `package/LICENSE` to `src/website/static/fonts/rock-salt-LICENSE.txt`. Do not modify either file. Delete the scratch directory afterwards.
- [ ] T003 [P] Add a `Credit` to `CREDITS` in `src/website/content.py`, after htmx: `work="Rock Salt font"`, `author="Sideshow"`, `work_url="https://fonts.google.com/specimen/Rock+Salt"`, `licence="Apache License 2.0"`, `licence_url="https://www.apache.org/licenses/LICENSE-2.0"`. Add a test in `tests/unit/test_content.py` asserting this credit is present with those values.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The page exists, is in the navigation and renders an empty form. Every story builds on
it.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add `ANASCRAMBLE: Final = Page(name="anascramble", path="/anascramble", title="Anascramble", nav_label="Anascramble")` to `src/website/content.py` and set `PAGES = (HOME, ANASCRAMBLE, ABOUT)` (About stays last, pinned at the bottom of the drawer). Update the expected list in `tests/unit/test_content.py` `PAGES` test, and add `(ANASCRAMBLE.title, "Anascramble · Tim's Page")` to the tab-title parametrisation.
- [ ] T005 [P] Add `@font-face { font-family: "Rock Salt"; font-style: normal; font-weight: 400; font-display: swap; src: url("../fonts/rock-salt-latin-400-normal.woff2") format("woff2"); }` near the top of `src/website/static/css/site.css`. Add a test in `tests/integration/test_static.py` that `/static/fonts/rock-salt-latin-400-normal.woff2` returns 200 with content type `font/woff2`, and that `/static/fonts/rock-salt-LICENSE.txt` returns 200 and contains `Apache License`.
- [ ] T006 Create `src/website/anascramble.py` (module docstring: pure domain logic for the Anascramble page, no web imports) with the constants from [data-model.md](data-model.md#constants), all `Final`: `MIN_LETTERS = 3`, `MAX_LETTERS = 30`, `BLANK = " "`, `START_RADIUS = 50.0`, `RADIUS_STEP = 5.0`, `TRIES_PER_STEP = 10`, `MIN_SPACING = 50.0`, `MIN_VIEW_SIZE = 400.0`, `VIEW_MARGIN = 30.0`, `MAX_FIELD_LENGTH = 200`.
- [ ] T007 Add to `src/website/routes.py` the Pydantic model `AnascrambleForm` with fields `letters: str = ""`, `solution: str = ""`, `seed: str = ""`, `arranged: str = ""`, `intent: str = ""` (plain `str` so unknown intents never cause a 422; map to `Literal["letters", "solution", "scramble"] | None` in the domain, see T012). Add `GET`/`HEAD` route `/anascramble`, name `anascramble`, `include_in_schema=False`, rendering `anascramble.html` with an empty puzzle (until T012 exists, pass placeholder values the template needs).
- [ ] T008 Create `src/website/templates/anascramble.html` extending `base.html` with `{% set page_title = "Anascramble" %}` and `{% set current_page = "anascramble" %}`, and `src/website/templates/anascramble/_parts.html` holding one Jinja macro per fragment (`scramble_svg`, `puzzle_state`, `scramble_button`, `solution_row`, `solution_input`, `letters_input`). Each macro takes an `oob: bool = False` argument that adds `hx-swap-oob="true"` to its root element. The page renders the form skeleton exactly as in [contracts/page-layout.md](contracts/page-layout.md#page-structure-inside-main-idcontent) (form attributes `method="post" action="/anascramble" hx-post="/anascramble" hx-swap="none" hx-sync="this:replace"`), using the macros. For now, `solution_row` renders with `hidden` and the scramble SVG is empty with `aria-hidden="true"`.
- [ ] T009 [P] Extend `tests/integration/test_navigation.py` if needed so the parametrised drawer and `aria-current` tests cover Anascramble (they iterate `PAGES`, so confirm they pass). Add `tests/integration/test_anascramble.py` with: `GET /anascramble` returns 200 HTML with `<h1>` "Anascramble"; the form has the attributes from T008; the letters input has `maxlength="30" minlength="3" pattern="[A-Za-z]{3,30}" required autocomplete="off"`; "Scramble!" is `disabled`; `#solution-row` has `hidden`; no `Set-Cookie` header; no element has a `style` attribute.
- [ ] T010 Update the Pages table in `README.md` with a row: `` `/anascramble` `` | Anascramble | Anagram solving aid: scrambles letters and tracks a partial solution.

**Checkpoint**: `/anascramble` is reachable from the drawer and shows an empty, inert form.

---

## Phase 3: User Story 1 - Scramble letters (Priority: P1) 🎯 MVP

**Goal**: Visitors type 3–30 letters and press "Scramble!" to see them jumbled, non-overlapping,
round the centre, with a new layout each press.

**Independent Test**: Enter letters of varying lengths, press "Scramble!" repeatedly, and check
every letter appears once, upper case, non-overlapping and inside the area, in a new arrangement
each time; the button is disabled below 3 letters and digits are removed.

### Tests for User Story 1 ⚠️

- [ ] T011 [P] [US1] Create `tests/unit/test_anascramble.py` covering:
  - `sanitise_letters`: upper-cases; removes everything except A–Z (digits, spaces, punctuation, non-ASCII letters such as `é`); truncates to `MAX_LETTERS` (30); truncates raw input to `MAX_FIELD_LENGTH` (200) before sanitising.
  - `scramble(letters, rng)`: returns one `PlacedLetter` per letter, each `index` in `range(len(letters))` exactly once, `letter == letters[index]`; for 1,000 seeded runs (`random.Random(seed)` for seeds 0–999) of random 3–30 letter inputs, every pair of centres is at least `MIN_SPACING` apart (SC-003); same seed gives an identical result (FR-008); different seeds give different positions; the output order is not always the index order (shuffled reading order, FR-019).
  - `view_box(placed)`: square, centred on the origin, side at least `MIN_VIEW_SIZE` (400); every letter centre is at least `VIEW_MARGIN` (30) inside every edge; `view_box([])` is `(-200.0, -200.0, 400.0, 400.0)`.
  - `Puzzle.from_form` for intents `letters` and `scramble` per the transition table in [data-model.md](data-model.md#state-transitions-puzzlefrom_form): `scramble` with ≥ 3 letters sets a seed and `arranged == letters`; `scramble` with < 3 letters sets no seed; `letters` with `arranged != letters` clears the seed; invalid `seed` values (`""`, `"abc"`, `"-1"`, `str(2**63)`) mean no arrangement; `letters_corrected` is true for `"le7"` and false for `"let"`.
- [ ] T012 [P] [US1] Add to `tests/integration/test_anascramble.py`:
  - POST `intent=scramble`, `letters=letter` without `HX-Request`: 200 full page; SVG has 6 `<text>` elements whose letters form the multiset `LETTER`; hidden `seed` is an integer and `arranged=LETTER`; response has `Cache-Control: no-store`.
  - Same with `HX-Request: true`: body contains only elements with `hx-swap-oob="true"` and ids `scramble`, `puzzle-state`, `scramble-button`, `solution-row`; no `<html>` or `<h1>`.
  - POST `intent=letters`, `letters=le7` with `HX-Request: true`: includes `#letters` fragment with `value="LE"`, `#scramble-button` with `disabled`, empty `#scramble`, empty hidden `seed`.
  - POST `intent=letters`, `letters=lette`: no `#letters` fragment; button enabled.
  - Tampering: fields 10,000 characters long, unknown `intent`, `seed=abc`, and a missing body all return 200 (never 422 or 500).
  - Two POSTs with the same `letters`, `arranged` and `seed` and `intent=solution` return identical SVG markup (arrangement rebuilt from the seed).
- [ ] T013 [P] [US1] Create `tests/e2e/test_anascramble.py` (Chromium, `live_server`/`base_url` fixtures) for US1 acceptance scenarios 1–7: empty page has disabled button and empty scramble area; typing 2 letters keeps it disabled and the third enables it; typing `7` or `!` is removed from the field within 1 s; typing a 31st letter is not entered; pressing "Scramble!" shows each letter once in upper case, with no two `text` elements' bounding boxes overlapping and all inside the SVG's bounding box; pressing again changes at least one position; editing the field empties the scramble area; pressing Enter in the letters field scrambles. Also assert the page URL stays `/anascramble` (no letters in the URL) and `document.cookie` is empty and `localStorage.length`/`sessionStorage.length` are 0.

### Implementation for User Story 1

- [ ] T014 [US1] In `src/website/anascramble.py`, implement:
  - `sanitise_letters(raw: str) -> str` (truncate to `MAX_FIELD_LENGTH`, upper-case, keep only `A`–`Z`, truncate to `MAX_LETTERS`).
  - Frozen, slotted dataclass `PlacedLetter(index: int, letter: str, x: float, y: float)`.
  - `scramble(letters: str, rng: random.Random) -> list[PlacedLetter]`, porting main's `CharacterScrambler`: for each letter in order, start at radius `START_RADIUS`, pick `theta = math.tau * rng.random()`, point `(r*sin θ, r*cos θ)`; while it is closer than `MIN_SPACING` to any earlier point, pick a new angle and every `TRIES_PER_STEP` tries add `RADIUS_STEP` to the radius. The radius carries over between letters (as on main). Round coordinates to 1 decimal place. Then `rng.shuffle` the list.
  - `view_box(placed: Sequence[PlacedLetter]) -> tuple[float, float, float, float]` per [data-model.md](data-model.md#viewbox-domain).
  - `new_seed() -> int` returning `secrets.randbits(63)`.
  - `parse_seed(raw: str) -> int | None` (integer in `[0, 2**63)`, else `None`).

  If Ruff `S311` flags `random.Random`, suppress it on that line with a comment saying the generator is not used for security.
- [ ] T015 [US1] In `src/website/anascramble.py`, add `type Intent = Literal["letters", "solution", "scramble"]`, `parse_intent(raw: str) -> Intent | None`, and a frozen dataclass `Puzzle` with fields `letters: str`, `solution: str`, `seed: int | None`, `letters_corrected: bool`, `solution_corrected: bool`, properties `can_scramble`, `shows_solution` and `arrangement` (`scramble(letters, random.Random(seed))` when `seed` is set, else `[]`), and `classmethod from_form(cls, *, letters: str, solution: str, seed: str, arranged: str, intent: Intent | None) -> Puzzle` implementing the `letters` and `scramble` rows of the transition table. For now set `solution=""` and `solution_corrected=False` (US2 fills these in). Add `Puzzle.empty()` for the GET route.
- [ ] T016 [US1] In `src/website/routes.py`, add `POST /anascramble` taking `form: Annotated[AnascrambleForm, Form()]`. Build the `Puzzle` with `Puzzle.from_form(..., intent=parse_intent(form.intent))`. Without `HX-Request` (use `is_htmx_request`), render `anascramble.html`. With it, render `anascramble/_fragments.html` (created in T017), which calls the `_parts.html` macros with `oob=True` per the fragment table in [contracts/http.md](contracts/http.md#with-hx-request-true). Set `Cache-Control: no-store` on all POST responses. Update the GET route to pass `Puzzle.empty()`.
- [ ] T017 [US1] Implement the US1 macros in `src/website/templates/anascramble/_parts.html` and create `src/website/templates/anascramble/_fragments.html`:
  - `scramble_svg(puzzle)`: `<svg id="scramble" class="scramble" viewBox="{min_x} {min_y} {size} {size}" role="group" aria-label="Scrambled letters">` with one `<text x y class="scramble-letter" text-anchor="middle" dominant-baseline="central">` per `PlacedLetter`, in list order. When there is no arrangement, render an empty `<svg>` with `aria-hidden="true"` and the default view box.
  - `puzzle_state(puzzle)`: `<div id="puzzle-state">` with hidden `seed` (empty when `None`) and `arranged` (equal to `letters` when seeded, else empty).
  - `scramble_button(puzzle)`: `disabled` unless `can_scramble`.
  - `letters_input(puzzle)`: the letters input from the layout contract, `hx-trigger="input"`, `hx-vals='{"intent":"letters"}'`, `value` set to `puzzle.letters`.
  - `_fragments.html`: always emits `scramble_svg`, `puzzle_state`, `scramble_button`; emits `solution_row` when `intent != "solution"`; emits `letters_input` when `letters_corrected`.
- [ ] T018 [US1] Style the page in `src/website/static/css/site.css`: `.anascramble` is a centred single column with gap (order: scramble, solution row, letters label and field, button); `.scramble` is `display: block; width: 100%; max-width: 400px; aspect-ratio: 1; height: auto`; `.scramble-letter` uses `font-family: "Rock Salt", cursive`, `font-size: 32px` (SVG user units), and `fill` from the accent colour token used for links (readable in both themes, WCAG AA); `.scramble-letter.dimmed { opacity: 0.25; }`; the letters input and "Scramble!" button use the existing control styles and a minimum 44 px touch target (`var(--menu-button-size)`); the primary button uses the accent token background with AA contrast text in both themes and a visible disabled state.

**Checkpoint**: US1 tests pass; scrambling works with and without JavaScript.

---

## Phase 4: User Story 2 - Build the solution (Priority: P2)

**Goal**: Visitors type a candidate answer into the solution field. Each accepted letter dims one
matching scrambled letter; unavailable letters are refused.

**Independent Test**: Enter "LETTER", scramble, type available, repeated and unavailable letters in
the solution field, delete some, and check acceptance and dimming.

### Tests for User Story 2 ⚠️

- [ ] T019 [P] [US2] Add to `tests/unit/test_anascramble.py`:
  - `claimed_map("LETTER", "TT")` marks indices 2 and 3; `claimed_map("LETTER", " E")` marks index 1 only; blanks claim nothing; result length equals `len(letters)`.
  - `sanitise_solution(raw, letters)`: upper-cases; keeps letters and `BLANK` only; removes a letter with no unclaimed match (`"TTT"` → `"TT"` for `LETTER`; `"Z"` → `""`); truncates to `len(letters)`; returns `""` when `len(letters) < MIN_LETTERS`.
  - `Puzzle.from_form`: `intent="solution"` keeps a valid seed and sanitises the solution; `solution_corrected` is true for `"TTT"` and false for `"tt"` (case-only change is not a correction); `intent="scramble"` keeps the sanitised solution; `intent="letters"` with changed letters resets the solution to `""` even if it would still be valid; `intent=None` behaves like `solution`.
- [ ] T020 [P] [US2] Add to `tests/integration/test_anascramble.py`, using `HX-Request: true`:
  - `intent=solution`, `letters=LETTER`, `arranged=LETTER`, valid seed, `solution=TTT`: `#solution` fragment with `value="TT"`; exactly two `text.dimmed` elements, both `T`, each with `aria-disabled="true"`; positions identical to the same request with `solution=""`; no `#solution-row` fragment.
  - `solution=T E`: two dimmed letters (`T`, `E`); no `#solution` fragment.
  - `intent=letters` changing letters: `#solution-row` fragment present, not `hidden`, with `#solution` empty, `maxlength` equal to the new length and one `span` per letter in `#solution-cells`.
  - fewer than 3 letters: `#solution-row` has `hidden`.
  - Without `HX-Request`, `intent=scramble` with a solution keeps the solution value and dims the matching letters in the full page.
- [ ] T021 [P] [US2] Add to `tests/e2e/test_anascramble.py` US2 acceptance scenarios 1–8: no solution row below 3 letters; 6 cells appear for `letter` before scrambling; typing `t`, `t`, `t` leaves `TT` and dims exactly two `T`; typing `z` is removed; deleting a letter undims it; re-scrambling keeps the solution and dims matching letters in the new layout; editing the letters resets the solution to empty cells of the new length; typing in the solution before scrambling accepts and refuses letters the same way.

### Implementation for User Story 2

- [ ] T022 [US2] In `src/website/anascramble.py`, implement `claimed_map(letters: str, solution: str) -> list[bool]` and `sanitise_solution(raw: str, letters: str) -> str` per [data-model.md](data-model.md#claimed_map) (truncate raw to `MAX_FIELD_LENGTH` first). Complete `Puzzle.from_form` for all transition rows: reset check first (`arranged != letters` or invalid seed → no seed, `solution=""`), then sanitise the solution against `letters`, then apply the intent. Set `solution_corrected` by comparing the sanitised value with the upper-cased raw value. Add property `claimed` returning `claimed_map(self.letters, self.solution)`.
- [ ] T023 [US2] In `src/website/templates/anascramble/_parts.html`: `scramble_svg` adds class `dimmed` and `aria-disabled="true"` to a `<text>` when `puzzle.claimed[placed.index]`; implement `solution_row(puzzle)` (`<div id="solution-row" class="solution-row">`, `hidden` unless `shows_solution`, containing `<label for="solution">Solution:</label>` and `<div class="solution-field">` with `<div id="solution-cells" class="solution-cells" aria-hidden="true">` holding one empty `<span>` per letter, then `solution_input`) and `solution_input(puzzle)` (`id="solution" name="solution" type="text" maxlength="{len(letters)}" pattern="[A-Za-z ]*" autocomplete="off" autocapitalize="characters" spellcheck="false" hx-trigger="input" hx-vals='{"intent":"solution"}'`, `value` = `puzzle.solution`). In `_fragments.html`, also emit `solution_input` when `intent == "solution"` and `solution_corrected`.
- [ ] T024 [US2] Style the solution field in `src/website/static/css/site.css` (research R7): `.solution-field` is a grid with `#solution-cells` and `#solution` in the same grid area; define `--cell-width` (about 2.5rem) and reduce it with `.solution-field:has(.solution-cells > :nth-child(11))` and `:nth-child(21)` steps so 30 cells fit 320 px where possible, floor about 1.25rem; `.solution-cells` is a flex row of `--cell-width` boxes with a visible border (AA non-text contrast in both themes); `#solution` has transparent background, no border, a monospace font sized to the cells, `letter-spacing` and `padding-inline-start` so each character is centred in its cell, width equal to `n × --cell-width` via the cells' grid track; `.solution-field` has `overflow-x: auto`; visible focus ring on the field using the existing focus token.

**Checkpoint**: US1 and US2 tests pass; solution acceptance, refusal and dimming work with and
without JavaScript.

---

## Phase 5: User Story 3 - Fast keyboard entry (Priority: P3)

**Goal**: Typing straight through the solution field puts each character in the next cell, Space
leaves a blank, Backspace steps back, and server feedback never moves the caret or loses accepted
keystrokes.

**Independent Test**: With the keyboard only, type a word with blanks and corrections and check
which cell each character is in and where the caret is.

### Tests for User Story 3 ⚠️

- [ ] T025 [P] [US3] Add to `tests/e2e/test_anascramble.py`, marked `@pytest.mark.firefox` so they also run in Firefox, for US3 acceptance scenarios 1–6:
  - typing `l`, space, `t` gives value `L T`, caret (`selectionStart`) at 3, and each character's horizontal centre within its cell's bounds (compare with `#solution-cells span` boxes, measuring characters with a `Range` in `evaluate`);
  - Backspace removes the previous character and the caret moves back one;
  - a refused letter typed mid-word (`L` then caret moved to the start, type `z`) is removed and `selectionStart` stays where it was before the refused key;
  - `page.keyboard.type("letter", delay=0)` into a 6-cell solution for `LETTER` ends with value `LETTER` and six dimmed letters after the network is idle (no lost or misplaced keystrokes);
  - when all cells are filled, a further key is not entered;
  - `document.activeElement` remains `#solution` after every server response.
- [ ] T026 [P] [US3] Add an integration test to `tests/integration/test_anascramble.py`: an `intent=solution` response with no correction contains no element with `id="solution"` and no `autofocus` attribute anywhere (FR-015: the server never moves focus).

### Implementation for User Story 3

- [ ] T027 [US3] Make T025 and T026 pass, adjusting only markup and CSS. Likely fixes: align `letter-spacing`/padding in `src/website/static/css/site.css` so characters sit centred in cells in both Chromium and Firefox (use a font stack whose `ch` is reliable, e.g. `ui-monospace, "Cascadia Mono", "DejaVu Sans Mono", monospace`, and size cells in `ch`); confirm the `#solution` fragment keeps the same `id` so htmx 4 restores focus and selection (research R5). If htmx does not restore the caret after an out-of-band swap, switch the corrected-solution response to a main-target swap of `#solution` (`hx-target`/`hx-swap="outerHTML"` on the solution input) rather than writing any script, and record the change in [research.md](research.md#r5-htmx-interaction-design).

**Checkpoint**: All user stories work; keyboard entry is reliable in Chromium and Firefox.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T028 [P] Add Anascramble to `tests/e2e/test_accessibility.py`: axe reports no serious or critical violations in light and dark themes for the empty page, after scrambling `LETTER`, and with `TT` typed into the solution (two dimmed letters, FR-020). Do not disable the colour-contrast rule.
- [ ] T029 [P] Add a no-JavaScript test to `tests/e2e/test_anascramble.py` using a context with `java_script_enabled=False`: type `letter`, press Enter → full page with 6 scrambled letters and a solution row; type `ttz` in the solution and press Enter → solution `TT`, two dimmed letters (re-scrambled is fine); the URL path stays `/anascramble`.
- [ ] T030 [P] Add a narrow-viewport test to `tests/e2e/test_anascramble.py` at 320 × 640: with 30 letters scrambled and the solution row shown, `document.documentElement.scrollWidth <= 320` (SC-005), the SVG is no wider than the viewport, and all `text` elements are inside the SVG's bounding box.
- [ ] T031 [P] Add a theme test to `tests/e2e/test_anascramble.py`: after scrambling with a partial solution, toggling "Dark mode" keeps the letters, solution, seed and dimming unchanged (switching theme does not lose the puzzle).
- [ ] T032 Run every command in [quickstart.md](quickstart.md#automated-checks) and walk through its manual table; fix any failures. Confirm the About page cookie statement is still accurate and no task introduced `style=""` attributes, inline scripts or `js:` htmx values (`git grep -n 'style="\|js:\|<script' src/website/templates`, expecting only the existing htmx `<script src>` in `base.html`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies. T002 and T003 can run alongside T001.
- **Foundational (Phase 2)**: depends on Setup (T005 needs the font from T002; T007 needs T001).
  Blocks all stories.
- **US1 (Phase 3)**: depends on Foundational.
- **US2 (Phase 4)**: depends on US1 (`Puzzle`, the POST route and fragments).
- **US3 (Phase 5)**: depends on US2 (the solution field).
- **Polish (Phase 6)**: depends on all stories.

### Within Each User Story

- Tests first; confirm they fail.
- Domain (`anascramble.py`) → route (`routes.py`) → templates → CSS.
- Run the story's tests and Ruff/ty before moving on.

### Parallel Opportunities

- Setup: T002 and T003.
- Foundational: T005 and T009 alongside T006–T008.
- Each story: its test tasks (unit, integration, e2e) are in different files and run in parallel.
- Polish: T028–T031 are independent test additions.

## Parallel Example: User Story 1

```text
# Write all US1 tests together:
T011 tests/unit/test_anascramble.py
T012 tests/integration/test_anascramble.py
T013 tests/e2e/test_anascramble.py

# Then implement in order:
T014 → T015 → T016 → T017 → T018
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phases 1 and 2.
2. Phase 3 (US1). Stop and validate: the page scrambles letters with and without JS.
3. Shippable on its own: the solution row stays hidden until US2.

### Incremental Delivery

1. US1: scramble (MVP).
2. US2: solution field with dimming.
3. US3: keyboard reliability checks and fixes.
4. Polish: accessibility, no-JS, narrow screens, theme.

## Notes

- Commit after each phase with Conventional Commits (`feat:`, `test:`, `docs:`).
- Keep `src/website/anascramble.py` free of FastAPI, Starlette and Jinja imports (constitution V).
