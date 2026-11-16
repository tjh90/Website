---

description: "Task list for feature 004: Recipe Database"
---

# Tasks: Recipe Database

**Input**: Design documents from `specs/004-recipe-database/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included, because constitution principle IV requires every feature to ship with tests.
Within each story, write the tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story, in spec order:
- US1, P1: browse and read recipes
- US2, P1: author a recipe as a text file
- US3, P2: filter recipes
- US4, P2: keep ingredient names consistent

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: The user story this task belongs to (US1 to US4)
- Paths are relative to the repository root (single project, `src/` layout)

**Applies to every task**:
- Follow constitution III: type hints everywhere (`Final[...]` for module constants), Google-style
  docstrings on every public module, class and function, and Ruff and ty clean.
- Keep `src/website/cookbook.py` pure: no FastAPI, Starlette or Jinja imports.
- Write no hand-written JavaScript (constitution II). htmx attributes use plain values only: no
  `js:` prefixes and no trigger filters (`[...]`), because the CSP has no `'unsafe-eval'`.
- Add no `style="..."` attributes anywhere (CSP `style-src 'self'`). All styling goes in
  `src/website/static/css/site.css`, using the existing `light-dark()` colour tokens.
- Render pages with `website.templating.render()`.
- In tests, locate elements by role and accessible name first, using the markup in
  [contracts/page-layout.md](contracts/page-layout.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, configuration and the test collection that every story uses.

- [X] T001 Run `uv add markdown-it-py mdit-py-plugins pyyaml` so `pyproject.toml` `[project].dependencies` and `uv.lock` include all three (research R3). If ty reports missing stubs for `yaml`, run `uv add --dev types-pyyaml`. Confirm `uv lock --check` passes.
- [X] T002 [P] Add `recipes_dir: DirectoryPath` to `Settings` in `src/website/config.py`, defaulting to `Path(__file__).parent / "recipes"`, and document it in the class docstring's Attributes (env var `WEBSITE_RECIPES_DIR`, research R2). In `tests/unit/test_config.py`, test that the default points at `src/website/recipes` and that `WEBSITE_RECIPES_DIR` overrides it (use `monkeypatch.setenv` and `tmp_path`).
- [X] T003 [P] Create the fixed test collection `tests/fixtures/recipes/valid/`:
  - `vocabulary.yaml`: types `Drink, Breakfast, Snack, Dessert` (Dessert deliberately unused); ingredients `Aperol, Bacon, Bread, Cava, Champagne, Egg, Elderflower cordial, Gin, Ginger beer, Ice cubes, Lime, Mint, Mushroom, Orange, Prosecco, Soda water, Vodka` (Mint deliberately unused).
  - `french-75.md`: copy of the spec's Reference Recipe File, with "into" and "Pierce".
  - `aperol-spritz.md`: `type: drink`; ingredients `Ice cubes`, `Aperol (75 ml)`, `Prosecco (100 ml)`, `Soda water (25 ml)`, `[OPTIONAL] Orange (1 slice)`; method a single paragraph.
  - `moscow-mule.md`: `type: Drink`; ingredients `Vodka (50 ml)`, `Ginger beer (150 ml)`, `Lime`, `Ice cubes`; method a numbered list. Used to prove "gin" does not match "Ginger beer".
  - `full-english.md`: `type: BREAKFAST`; ingredients `Egg (2)`, `Bacon (3 rashers)`, `Bread`, `[OPTIONAL] Mushroom`; method a bulleted list.
  - `README.md` with one line saying it is test data, which checks that `README.md` is ignored.
- [X] T004 [P] Create `tests/fixtures/recipes/empty/vocabulary.yaml` (types `Drink`, ingredients `Gin`, no recipes). Create `tests/fixtures/recipes/unsafe/`: a copy of the valid `vocabulary.yaml`, plus `unsafe.md` (`type: Snack`, name `Unsafe <b>name</b>`, ingredient `Bread`). Its method contains `<script>alert(1)</script>`, `[click](javascript:alert(1))` and `![img](https://example.com/x.png)`.
- [X] T005 Update `tests/conftest.py`:
  - Add `FIXTURE_RECIPES: Final = Path(__file__).parent / "fixtures" / "recipes"`.
  - Give the `settings` fixture `recipes_dir=FIXTURE_RECIPES / "valid"`.
  - Make `live_server` build `Settings(revision=LIVE_REVISION, recipes_dir=FIXTURE_RECIPES / "valid")`.

  This makes every existing and new app test independent of the real recipes. Depends on T002 and T003.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The domain types and a happy-path loader that parses valid files into a collection
held by the app. Every story builds on it.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Create `src/website/cookbook.py`. Its module docstring says: domain logic for the recipe collection, pure, no web imports. Define, per [data-model.md](data-model.md):
  - `Vocabulary`: Pydantic model with `model_config = ConfigDict(extra="forbid", frozen=True)` and fields `types: list[str]` and `ingredients: list[str]`. Each entry is trimmed. The model builds the private casefold lookups `casefold(name) → canonical name` for both lists. Self-validation is added in T040.
  - Frozen, slotted dataclasses:
    - `RecipeType(name: str, key: str)`, where `key = name.casefold()`.
    - `IngredientEntry(alternatives: tuple[str, ...], amount: str | None, optional: bool)`, with a `display_name` property returning "A", "A or B", or "A, B or C".
    - `Recipe(slug, name, type: RecipeType, ingredients: tuple[IngredientEntry, ...], method_html: str, source: Path)`, with an `ingredient_keys: frozenset[str]` property holding the casefolded names of every alternative of every entry, and an `ingredient_summary: str` property joining each entry's `display_name` with " · ".
    - `RecipeProblem(source: Path, message: str)`.
    - `RecipeCollection(recipes: tuple[Recipe, ...], vocabulary: Vocabulary)`, with properties `by_slug: Mapping[str, Recipe]`, `types_in_use: tuple[RecipeType, ...]` ("vocabulary order, only types with at least one recipe") and `ingredient_names: tuple[str, ...]` (vocabulary order).
  - `RecipeCollectionError(Exception)`, holding `problems: tuple[RecipeProblem, ...]`. Its `__str__` is a header line plus one `<file name>: <message>` line per problem, sorted by file name.
- [X] T007 [P] Write unit tests in `tests/unit/test_cookbook.py` for the foundation:
  - `IngredientEntry.display_name` for 1, 2 and 3 alternatives ("Champagne, Prosecco or Cava").
  - `Recipe.ingredient_keys`, which includes alternatives and optional entries.
  - `Recipe.ingredient_summary` for French 75 is `"Elderflower cordial · Gin · Ice cubes · Lime · Champagne, Prosecco or Cava"`.
  - `RecipeCollection.types_in_use` omits unused types and keeps vocabulary order.
  - `str(RecipeCollectionError(...))` lists every problem sorted by file.
  - `load_collection(FIXTURE_RECIPES / "valid")` returns 4 recipes sorted by `name.casefold()` (Aperol Spritz, French 75, Full English, Moscow Mule), ignores `README.md`, and parses French 75 exactly:
    - type `Drink`
    - 5 entries
    - first entry `optional=True`, alternatives `("Elderflower cordial",)`, amount `"10 ml"`
    - last entry alternatives `("Champagne", "Prosecco", "Cava")`, amount `None`
    - `method_html` containing `<ol>` and 4 `<li>`

  Import `FIXTURE_RECIPES` from `tests.conftest`, or define a small helper module.
- [X] T008 Implement the happy path of `load_collection(directory: Path) -> RecipeCollection` in `src/website/cookbook.py` (research R3, R4):
  - Read `vocabulary.yaml` with `yaml.safe_load` into `Vocabulary.model_validate`.
  - For every `*.md` except `README.md`, sorted, parse with a module-level `MarkdownIt("commonmark", {"html": False}).use(front_matter_plugin).disable("image")`.
  - Take `type` from the `front_matter` token via `yaml.safe_load` and a `RecipePreamble` Pydantic model (`type: str`, `extra="forbid"`).
  - The name is the inline content of the single `h1`.
  - Ingredients: the `bullet_list` items under the `h2` "Ingredients", each matched with the regex in research R4 (`^(?:\[OPTIONAL\]\s+)?(?P<names>[^()]+?)(?:\s*\((?P<amount>[^()]*)\))?$`), with names split on `/`, trimmed, and mapped to canonical vocabulary spelling.
  - Method: render the tokens after the `h2` "Method" with `md.renderer.render(tokens, md.options, {})`.
  - Collect problems into a list rather than raising per file, and raise `RecipeCollectionError` at the end if the list is non-empty. In this task, record a single generic problem for anything unparseable. Detailed messages come in US2 and US4.
  - Sort recipes by `name.casefold()`.
- [X] T009 Load the collection in `create_app` in `src/website/app.py`: `app.state.recipes = load_collection(app.state.settings.recipes_dir)`, before routes are used. Let `RecipeCollectionError` propagate. Add a typed helper `get_collection(request: Request) -> RecipeCollection` in `src/website/routes.py`, which reads `request.app.state.recipes`.
- [X] T010 [P] Create the real collection:
  - `src/website/recipes/vocabulary.yaml`, exactly as in [contracts/recipe-format.md](contracts/recipe-format.md#vocabularyyaml), with its comments.
  - `src/website/recipes/french-75.md`, the reference recipe with "into" and "Pierce".

  No `__init__.py`. Confirm `uv build` includes the folder in the wheel (`uv build --wheel` then list the wheel contents), then delete `dist/`.

**Checkpoint**: `create_app()` loads both the fixture and real collections. The full existing test
suite passes.

---

## Phase 3: User Story 1 - Browse and read recipes (Priority: P1) 🎯 MVP

**Goal**: A Recipes page lists every recipe by name and type, and each recipe has its own readable
page.

**Independent Test**: With the fixture collection, open `/recipes`, check all 4 recipes are listed
alphabetically with types, and open French 75 to check the optional label, amounts, alternatives and
numbered method.

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] In `tests/unit/test_content.py`, update the `PAGES` test to expect `(HOME, ANASCRAMBLE, RECIPES, ABOUT)`, and add `(RECIPES.title, "Recipes · Tim's Page")` to the tab-title parametrisation.
- [X] T012 [P] [US1] Create `tests/integration/test_recipes.py` with list and recipe-page tests, using the `client` fixture (fixture collection):
  - `GET /recipes` returns 200 with `<h1>` "Recipes". `#recipe-results` lists the 4 recipes in order Aperol Spritz, French 75, Full English, Moscow Mule, each linking to `/recipes/<slug>` with its type ("Drink", "Breakfast") and its `.recipe-summary` (French 75's is "Elderflower cordial · Gin · Ice cubes · Lime · Champagne, Prosecco or Cava"). The status reads "4 recipes".
  - `GET /recipes/french-75` returns 200, with `<h1>` "French 75", `.recipe-type` "Drink", and `section.recipe-ingredients` before `section.recipe-method` inside `.recipe-body`.
    - `.ingredients` has 5 `<li>`. The first has `.ingredient-name` "Elderflower cordial", `.ingredient-amount` "10 ml" and `.ingredient-optional` "optional". The last has `.ingredient-name` "Champagne, Prosecco or Cava".
    - `.method ol` has 4 `<li>`, and there is an "All recipes" link to `/recipes`.
  - `GET /recipes/aperol-spritz` has `.method p` (paragraph), and `GET /recipes/full-english` has `.method ul` (bulleted list).
  - `GET /recipes/French-75` and `/recipes/nope` return 404 with the site's not-found page.
  - With the `empty` fixture collection, `/recipes` shows "No recipes yet." To switch collections, override the `settings` fixture with `recipes_dir`.
  - With the `unsafe` fixture collection, `/recipes/unsafe` contains no `<script` and no `href="javascript:`. The script text is escaped (`&lt;script&gt;`), there is no `<img`, and the name is shown with the literal text `<b>name</b>`, escaped.
  - No response sets a cookie, and no element has a `style` attribute.
- [X] T013 [P] [US1] In `tests/integration/test_navigation.py`, make sure the parametrised drawer tests cover Recipes (they iterate `PAGES`). Add a test that `/recipes/french-75` marks the "Recipes" drawer link with `aria-current="page"`.
- [X] T014 [P] [US1] Create `tests/e2e/test_recipes.py` with browse tests:
  - Open the drawer, click "Recipes", and see the list.
  - Click "French 75" and check the URL is `/recipes/french-75`, the heading is "French 75" and the method has 4 numbered items.
  - Click "All recipes" to return to the list.
  - At a 320 px wide viewport, both pages have `document.documentElement.scrollWidth <= 320`, and on the recipe page the method is below the ingredients.
  - At a 1280 px wide viewport, the recipe page's method is to the right of the ingredients (compare bounding boxes).
- [X] T015 [P] [US1] In `tests/e2e/test_accessibility.py`, add axe checks with no violations for `/recipes` and `/recipes/french-75` in both light and dark themes, following the existing pattern, at 1280 px and at 390 px wide.

### Implementation for User Story 1

- [X] T016 [US1] Add `RECIPES: Final = Page(name="recipes", path="/recipes", title="Recipes", nav_label="Recipes")` to `src/website/content.py`, and set `PAGES = (HOME, ANASCRAMBLE, RECIPES, ABOUT)`. About stays last.
- [X] T017 [US1] In `src/website/routes.py`, add `GET`/`HEAD` `/recipes` (name `recipes`, `include_in_schema=False`) rendering `recipes.html` with `{"collection": collection}`. Add `GET`/`HEAD` `/recipes/{slug}` (name `recipe`) that looks up `collection.by_slug` and raises `HTTPException(404)` when the slug is missing, otherwise rendering `recipe.html` with `{"recipe": recipe}`. US3 replaces the list context with a `RecipeSearch`.
- [X] T018 [P] [US1] Create `src/website/templates/recipes.html` extending `base.html`, with `page_title = "Recipes"` and `current_page = "recipes"`. Render `<section id="recipe-results" aria-label="Recipes">` as in [contracts/page-layout.md](contracts/page-layout.md#list-page-templatesrecipeshtml-h1-recipes):
  - a `<p role="status">` with "N recipes", "1 recipe" or "No recipes yet."
  - a `ul.recipe-list` with a `<li>` per recipe: a link to `/recipes/{{ slug }}` with the name, `span.recipe-type`, and `p.recipe-summary` holding `recipe.ingredient_summary`.

  Leave a clearly marked place above the results for the filter form (US3).
- [X] T019 [P] [US1] Create `src/website/templates/recipe.html` extending `base.html`, with `page_title = recipe.name` and `current_page = "recipes"`. Render the `article.recipe` markup from [contracts/page-layout.md](contracts/page-layout.md#recipe-page-templatesrecipehtml-h1-is-the-recipe-name):
  - A top row with the "All recipes" link and `p.recipe-type`, then `div.recipe-body` holding `section.recipe-ingredients` (the ingredients card) and `section.recipe-method`.
  - `.ingredient-amount` only when there is an amount, and `.ingredient-optional` only when the entry is optional.
  - Method as `{{ recipe.method_html | safe }}`. This is the only `safe` filter, and it gets a Jinja comment noting the HTML comes from markdown-it with raw HTML disabled.
- [X] T020 [US1] Add styles to `src/website/static/css/site.css`, matching the mockup (see [contracts/page-layout.md](contracts/page-layout.md#styling-and-accessibility)). Use only existing tokens plus the new ones listed there, with AA contrast in both themes:
  - `.recipe-list`: rows separated by a rule.
  - `.recipe-type`: a pill.
  - `.recipe-summary`: muted, one line.
  - `.recipe-body`: a `flex-wrap` row, with the ingredients card at `flex: 1 1 280px; max-width: 360px` and the method at `flex: 999 1 420px; min-width: 0`, so it stacks on narrow screens.
  - `.ingredients`: rows with the amount right-aligned in the muted colour, and `.ingredient-optional` as an outlined pill.
  - `.method ol`: circled step numbers drawn with a CSS counter and `::before`.

  No horizontal overflow at 320 px.
- [X] T021 [US1] Add a row to the Pages table in `README.md`: `` `/recipes` `` | Recipes | Recipe collection with type, name and ingredient filters.

**Checkpoint**: The recipes are browsable and readable. US1 tests pass.

---

## Phase 4: User Story 2 - Author a recipe as a simple text file (Priority: P1)

**Goal**: The documented format is enforced with clear, complete error reports, and an invalid
collection stops the site starting.

**Independent Test**: Following only `src/website/recipes/README.md`, write a recipe and restart:
it appears. Break it in each documented way: the check names the file and the problem.

### Tests for User Story 2 ⚠️

- [X] T022 [P] [US2] In `tests/unit/test_cookbook.py`, add parametrised structural-validation tests. Each writes a valid `vocabulary.yaml` and one recipe file to `tmp_path`, calls `load_collection`, and asserts that `RecipeCollectionError` contains exactly one problem for that file whose message contains the expected text. Cases (messages from [data-model.md](data-model.md#recipeproblem--recipecollectionerror)):
  - no preamble → "preamble"
  - preamble not a mapping → "preamble"
  - extra preamble key `serves: 2` → `preamble must contain only "type"`
  - invalid YAML → "not valid YAML"
  - file name `French_75.md` → "file name must be lower-case words joined by hyphens"
  - no `#` heading, or two of them → "expected exactly one "#" recipe name heading"
  - missing `## Method` → `missing section "Method"`
  - `## Ingrediants` → `unknown section "Ingrediants"`
  - Method before Ingredients → "section"
  - duplicate `## Ingredients` → "section"
  - ingredients as a paragraph or numbered list → "ingredients must be a single bulleted list"
  - nested bullet list → same message
  - `Gin (50 ml` → "unbalanced parentheses"
  - `Gin ()` → "empty amount"
  - `Gin (50 ml) (double)` → malformed line
  - `Gin//Vodka` → empty alternative
  - `Gin/Gin` → duplicate alternative
  - `[optional] Gin` → unknown ingredient, because `[OPTIONAL]` must be upper case
  - empty method → "method section is empty"
  - non-UTF-8 bytes → "UTF-8"
- [X] T023 [P] [US2] In `tests/unit/test_cookbook.py`, test that two files whose names differ only in case (`French 75` and `french 75`) give a problem naming both files ("is also used by"). Also test that a folder with three different broken files reports all three problems in one error (FR-008).
- [X] T024 [P] [US2] Create `tests/fixtures/recipes/invalid/` with a valid `vocabulary.yaml`, `missing-method.md` (no `## Method`) and `bad-amount.md` (`Gin ()`). In `tests/integration/test_recipes.py`, test that `create_app(Settings(recipes_dir=FIXTURE_RECIPES / "invalid"))` raises `RecipeCollectionError` whose `str()` names both files (FR-010).
- [X] T025 [P] [US2] Add a unit test in `tests/unit/test_cookbook.py` that parses every recipe code block in `src/website/recipes/README.md` (the fenced `markdown` blocks) by writing each to `tmp_path` with the real `vocabulary.yaml`, and asserts they load. This keeps the documented example valid (FR-005).

### Implementation for User Story 2

- [X] T026 [US2] In `src/website/cookbook.py`, replace the generic problem from T008 with the specific checks and messages listed in T022, in [data-model.md](data-model.md#recipeproblem--recipecollectionerror) and in [contracts/recipe-format.md](contracts/recipe-format.md#recipe-file):
  - Slug: `^[a-z0-9]+(?:-[a-z0-9]+)*$`.
  - Section headings: `h2` matched with `casefold()`, exactly `Ingredients` then `Method`, no other `h1`/`h2`.
  - Ingredients: exactly one `bullet_list` with no nested lists.
  - Amount: trimmed, and "Empty parentheses are an error".
  - Alternatives: "At least 1", with "No duplicates within the entry".
  - Method: "must not be empty".
  - Name: "Unique ignoring case across the collection".

  Read files as UTF-8 and report decode errors as problems. A file with problems is excluded from the collection, but checking continues.
- [X] T027 [P] [US2] Create `src/website/recipes/README.md`, the authoring guide, from [contracts/recipe-format.md](contracts/recipe-format.md): folder layout, file naming, `vocabulary.yaml`, the full French 75 example, the ingredient line diagram and rules, method rules, and how to check (`uv run pytest tests/unit/test_shipped_recipes.py`). Note that the site will not start with an invalid collection.
- [X] T028 [US2] Add a "Recipes" section to `README.md` after "Running locally". It says recipes live in `src/website/recipes/`, links to its README, gives the check command, and says changes appear on the next start.

**Checkpoint**: Every documented authoring mistake is reported with file and message. An invalid
collection stops start-up.

---

## Phase 5: User Story 3 - Filter recipes (Priority: P2)

**Goal**: Filter by types, name and one ingredient. Filters combine, live in the URL, update live
without losing focus, and work without JavaScript.

**Independent Test**: With the fixture collection, apply each filter alone and in combination via
URL and via the form, and compare with the expectations in [contracts/http.md](contracts/http.md#examples-given-the-reference-collection).

### Tests for User Story 3 ⚠️

- [X] T029 [P] [US3] In `tests/unit/test_cookbook.py`, add filtering tests for `filter_recipes` over the valid fixture collection:
  - no filters → all 4, `is_filtered=False`
  - `type=["drink"]` → 3 drinks
  - `type=["drink", "breakfast"]` → 4
  - `type=["bogus"]` → all 4 (dropped)
  - `name="FRENCH"` → French 75
  - `name="  spritz "` → Aperol Spritz
  - `ingredient="prosecco"` → Aperol Spritz and French 75 (alternative)
  - `ingredient="elderflower cordial"` → French 75 (optional counts)
  - `ingredient="mushroom"` → Full English (optional)
  - `ingredient="gin"` → French 75 only, not Moscow Mule ("Ginger beer")
  - `ingredient="mint"` → no recipes (listed but unused)
  - `ingredient="limes"` → no recipes (not in the vocabulary)
  - `type=["breakfast"], ingredient="gin"` → none
  - `name` longer than 100 characters is truncated

  Also add a timing test: build 500 recipe files in `tmp_path` and assert `load_collection` takes less than 5 s and `filter_recipes` less than 0.1 s (SC-002, SC-003).
- [X] T030 [P] [US3] In `tests/integration/test_recipes.py`, add filter tests through `GET /recipes` covering every row of the examples table in [contracts/http.md](contracts/http.md#examples-given-the-reference-collection), adjusted to the fixture collection. Also check:
  - The form is pre-filled from the query: the checked boxes match, and the `name` and `ingredient` values are echoed and escaped.
  - The filter shows only types in use (Drink, Breakfast; no Snack or Dessert).
  - `#ingredient-options` lists every vocabulary ingredient in order.
  - "Clear filters" appears only when a filter is active.
  - The form sits inside `details.recipe-filters-panel` with no `open` attribute. `#filter-count` reads "· 2 active" for `?type=drink&ingredient=gin` and is empty with no filters.
  - The "Filter" button has class `filter-submit`, and `site.css` contains `@media (scripting: enabled)` hiding `.filter-submit`.
  - The form has exactly the attributes in [contracts/page-layout.md](contracts/page-layout.md#list-page-templatesrecipeshtml-h1-recipes).
  - The response with `HX-Request: true` still contains `#recipe-results`.
- [X] T031 [P] [US3] In `tests/e2e/test_recipes.py`, add filtering tests:
  - Typing `spr` in Name updates the list to Aperol Spritz without a navigation, focus stays in the Name box, and the URL contains `name=spr`.
  - Ticking "Breakfast" shows only Full English.
  - Typing `limes` in Ingredient shows "No matching recipes."
  - Reloading a filtered URL shows the same filters and results.
  - "Clear filters" resets the list and controls.
  - Typing fast (`page.keyboard.type("french", delay=20)`) ends with only French 75 listed.
  - With JavaScript enabled, the "Filter" button is not visible.
  - With JavaScript disabled (a new context with `java_script_enabled=False`), the "Filter" button is visible, and filling Ingredient with `gin` and pressing it shows only French 75.
  - At a 390 px wide viewport, the filters start collapsed. Opening the "Filters" toggle reveals them, and after ticking "Drink" the toggle reads "Filters · 1 active" without a reload.
  - At 1280 px, the filter controls are visible without opening anything, and no toggle is shown.
- [X] T032 [P] [US3] In `tests/e2e/test_accessibility.py`, add axe checks for `/recipes?type=drink`, `/recipes?ingredient=limes` (unknown ingredient) and `/recipes?name=zzz` (no results), in both themes, plus `/recipes` at 390 px with the filters panel expanded.

### Implementation for User Story 3

- [X] T033 [US3] In `src/website/cookbook.py`, add:
  - `RecipeQuery`, a Pydantic model with `type: list[str] = []` (casefolded; "Values that are not a type key are dropped silently", done in `filter_recipes`, which knows the vocabulary), `name: str = ""` and `ingredient: str = ""` ("Trimmed, capped at 100 characters"). Lenient validators: never raise.
  - `RecipeSearch`, a frozen dataclass with `query`, `recipes`, `is_filtered: bool` and `active_filter_count: int` ("Number of ticked valid types, plus 1 for a non-empty name, plus 1 for a non-empty ingredient").
  - `filter_recipes(collection, query) -> RecipeSearch`, implementing research R7:
    - "an ingredient text that is not in the vocabulary gives `recipes == ()`".
- [X] T034 [US3] Change `GET /recipes` in `src/website/routes.py` to take `query: Annotated[RecipeQuery, Query()]`, so repeated `type` parameters become a list. Confirm FastAPI query-model support handles `list[str]`, and fall back to `request.query_params.getlist("type")` otherwise. Render `recipes.html` with `{"collection": collection, "search": filter_recipes(collection, query)}`, and never return 422.
- [X] T035 [US3] Add the filter form to `src/website/templates/recipes.html` above `#recipe-results`, exactly as in [contracts/page-layout.md](contracts/page-layout.md#list-page-templatesrecipeshtml-h1-recipes):
  - Wrap the form in `<details class="recipe-filters-panel">` (never `open`) with `<summary>Filters <span id="filter-count">· N active</span></summary>`. The span is empty when no filter is active.
  - Form attributes: `method="get" action="/recipes" role="search" hx-get="/recipes" hx-trigger="submit, input delay:250ms" hx-target="#recipe-results" hx-select="#recipe-results" hx-select-oob="#filter-count" hx-swap="outerHTML" hx-push-url="true" hx-sync="this:replace"` (research R8a).
  - A type fieldset over `collection.types_in_use`, with `value="{{ t.key }}"`.
  - `#recipe-name`, plus `#recipe-ingredient` with `list="ingredient-options"`, both `type="search" maxlength="100" autocomplete="off"`, and `<datalist id="ingredient-options">`.
  - A "Filter" submit button with class `filter-submit`.
  - No helper text under the ingredient box.

  Iterate `search.recipes` in the results. Show the status ("N recipes", "1 recipe", "No matching recipes." when filtered and empty, "No recipes yet." when the collection is empty). Show "Clear filters" when `search.is_filtered`. When filtered and empty, add the tip `p.no-results-tip` "Try fewer filters, or pick an ingredient from the suggestions as you type." Check in a browser that htmx 4 swaps only `#recipe-results` and pushes the URL. If an htmx 4 attribute name or trigger syntax differs, use the htmx 4 equivalent and update [contracts/page-layout.md](contracts/page-layout.md).
- [X] T036 [US3] Style the filters in `src/website/static/css/site.css`, matching the mockup:
  - `.recipe-filters-panel` is a bordered card. On wide screens (`min-width: 768px`) it is a sidebar beside the results (`flex: 1 1 240px; max-width: 300px`), its `summary` is hidden, and its content is forced visible with `.recipe-filters-panel::details-content { content-visibility: visible; display: contents; }`. On narrow screens it sits above the results with a 48 px-tall `summary` toggle and a chevron.
  - `@media (scripting: enabled) { .filter-submit { display: none; } }`.
  - Checkbox rows at least 36 px tall, inputs 44 px, visible focus.
  - Style `.clear-filters` and `.no-results-tip` (muted).

  No horizontal overflow at 320 px, and AA contrast in both themes. Confirm in Chromium and Firefox that the panel is open on wide screens and collapsible on narrow ones.

**Checkpoint**: All filters work live and without JavaScript. US1 and US2 tests still pass.

---

## Phase 6: User Story 4 - Keep ingredient names consistent (Priority: P2)

**Goal**: The master ingredient list is the single source of ingredient names. Violations fail CI
and start-up, naming the file and the unlisted name.

**Independent Test**: Change `Lime` to `Limes` in a recipe and run
`uv run pytest tests/unit/test_shipped_recipes.py`: it fails naming the file and "Limes".
Revert it: it passes.

### Tests for User Story 4 ⚠️

- [X] T037 [P] [US4] In `tests/unit/test_cookbook.py`, add vocabulary tests (each writes to `tmp_path`). Each case must produce a problem against `vocabulary.yaml`, and recipes are not checked if the vocabulary is invalid:
  - missing file → "vocabulary"
  - empty `types` or `ingredients` → problem
  - duplicate ingredient ignoring case (`Lime`, `lime `) → `vocabulary: duplicate ingredient "lime"`
  - duplicate type → problem
  - ingredient containing `/` or parentheses → problem
  - extra top-level key → problem
- [X] T038 [P] [US4] In `tests/unit/test_cookbook.py`, add recipe-against-vocabulary tests:
  - `Limes` → `unknown ingredient "Limes"`, and the message contains no "did you mean"
  - `Champagne/Prosseco` → unknown ingredient for the misspelt alternative only
  - `type: DRNK` → `unknown type "DRNK"`
  - an ingredient written `gin` in a recipe is stored and shown as `Gin`
  - unused vocabulary names are allowed
- [X] T039 [P] [US4] Create `tests/unit/test_shipped_recipes.py`. Its module docstring explains it is the merge gate for recipe consistency (research R6). It loads `Settings().recipes_dir`, the real folder. On `RecipeCollectionError` it calls `pytest.fail(str(error), pytrace=False)`, so the author sees only the report. It also asserts the collection is non-empty.

### Implementation for User Story 4

- [X] T040 [US4] Add self-validation to `Vocabulary` in `src/website/cookbook.py`, per [data-model.md](data-model.md#vocabulary-pydantic-from-vocabularyyaml):
  - `types`: "Non-empty. Each entry is trimmed and non-empty, with no duplicates ignoring case."
  - `ingredients`: "Non-empty. Each entry is trimmed, non-empty and contains no `/` or parentheses, with no duplicates ignoring case."
  - Extra keys are forbidden.

  In `load_collection`, convert `ValidationError` or a missing or unreadable file into `RecipeProblem`s against `vocabulary.yaml`, then stop before checking recipes.
- [X] T041 [US4] In `src/website/cookbook.py`, report unknown types and unknown ingredients (each alternative individually) as `unknown type "X"` or `unknown ingredient "X"`, using the name as written. Do not suggest near misses (no `difflib`): the master list is the reference.
- [X] T042 [US4] Add a "Recipes" note to the README section from T028: the `test` CI job runs the shipped-collection check, and `test` should be a required status check on `main` so an invalid recipe cannot be merged (SC-004).

**Checkpoint**: Every story works. An inconsistent ingredient fails CI and start-up, naming
the file and the unlisted name.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T043 [P] Check that the About page statements remain accurate (no cookies, no new visitor-facing assets) and that no `Credit` changes are needed (constitution VI). Record the result in the PR description.
- [X] T044 [P] Re-read `src/website/recipes/README.md` against the final behaviour and messages, and fix any drift. T025 keeps its example loading.
- [X] T045 Run every quality gate from [quickstart.md](quickstart.md#automated-checks) (`uv lock --check`, `uv run ruff format --check`, `uv run ruff check`, `uv run ty check`, `uv run pytest`, `uv run pytest -m firefox --browser firefox`) and build the Docker image (`docker build -f build/Dockerfile --target website-run .`). Fix any failure.
- [X] T046 Walk through the [quickstart](quickstart.md#manual-walkthrough) manual and enforcement tables against `uv run website`, and fix any mismatch.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 first (dependencies). T002, T003 and T004 can run in parallel. T005
  depends on T002 and T003.
- **Foundational (Phase 2)**: depends on Setup. T006 comes before T007 and T008, and T008 before
  T009. T010 can run any time after T001.
- **US1 (Phase 3)**: depends on Foundational.
- **US2 (Phase 4)**: depends on Foundational. T024 also uses `create_app` from T009. It is
  independent of US1's UI.
- **US3 (Phase 5)**: depends on US1 (it extends `recipes.html` and the `/recipes` route).
- **US4 (Phase 6)**: depends on Foundational. It touches `cookbook.py` like US2, so do it after US2
  to avoid conflicting edits.
- **Polish (Phase 7)**: after all stories.

### Within Each User Story

- Write the tests first and see them fail.
- Then domain (`cookbook.py`), routes, templates, CSS and docs, in that order.

### Parallel Opportunities

- Setup: T002, T003 and T004 together.
- US1: all test tasks T011 to T015 together, then T018 and T019 (templates) together.
- US2: T022 to T025 together. T027 (README) can run in parallel with T026.
- US3: T029 to T032 together.
- US4: T037 to T039 together.
- After Foundational, US1 and US2 can be built by different people (they touch different files,
  apart from tests in `test_cookbook.py` and `test_recipes.py`, so coordinate those).

---

## Parallel Example: User Story 1

```text
# Tests for US1, together:
T011 tests/unit/test_content.py           (PAGES order)
T012 tests/integration/test_recipes.py    (list, recipe page, 404, unsafe, empty)
T013 tests/integration/test_navigation.py (aria-current on recipe pages)
T014 tests/e2e/test_recipes.py            (browse, 320 px)
T015 tests/e2e/test_accessibility.py      (axe, both themes)

# Then the templates, together:
T018 src/website/templates/recipes.html
T019 src/website/templates/recipe.html
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup, then Phase 2 Foundational.
2. Phase 3 (US1): the recipes are browsable and readable. Stop and validate with the quickstart
   steps 1–3 and 11.

### Incremental Delivery

1. Setup and Foundational give a loadable collection.
2. US1 gives the browsable site (MVP).
3. US2 makes authoring safe, with clear errors and refusal to start when invalid.
4. US3 adds filtering (live, shareable, no-JS).
5. US4 makes the ingredient filter trustworthy, with consistency enforced in CI.
6. Polish runs the gates and the walkthrough.

Each step leaves the full test suite green and could be merged on its own.

---

## Notes

- `cookbook.py` grows across stories: types and the happy path (Phase 2), structural checks (US2),
  filtering (US3), vocabulary checks (US4). Keep each concern in its own private function so the
  file stays readable.
- Only `test_shipped_recipes.py` reads the real `src/website/recipes/`. Every other test uses
  `tests/fixtures/recipes/`.
- Commit after each task or logical group, using Conventional Commits (`feat:`, `test:`, `docs:`).
