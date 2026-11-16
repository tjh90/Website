# Implementation Plan: Recipe Database

**Branch**: `claude/recipe-database-suggester-303d49` (spec-kit feature id `004-recipe-database`) |
**Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-recipe-database/spec.md`

## Summary

Add a Recipes page. It lists recipes authored as markdown files in the repository, with filters for
type (checkboxes), name and a single ingredient. Each recipe has its own page showing optional
ingredients, alternatives, amounts and the method. A master ingredient list keeps names consistent,
and the same check enforces it in CI and at start-up.

Technical approach (details in [research.md](research.md)):

- **Files, not a database**: `src/website/recipes/` holds one `<slug>.md` per recipe, plus
  `vocabulary.yaml` (types and master ingredient list) and an authoring `README.md`. The folder is
  loaded once in `create_app` into an immutable in-memory collection. It ships inside the package,
  so the Docker build is unchanged.
- **Parsing**: markdown-it-py (CommonMark, raw HTML off, images off) with the `mdit-py-plugins`
  front-matter plugin, and a PyYAML preamble validated by Pydantic. One token stream gives both the
  structure check and the safe method HTML.
- **Strict validation, all problems at once**: a single loader reports every problem, with file
  names. It runs in a unit test over the shipped folder (merge gate
  in the existing CI `test` job) and at start-up, where any problem stops the site starting.
- **Filtering**: a pure `filter_recipes` function over GET query parameters, so filters are
  shareable and work without JavaScript. htmx re-requests the page as the visitor types and swaps
  only `#recipe-results` (and the filter count), which keeps focus. A native `<datalist>` suggests
  ingredients. The "Filter" button only appears without JavaScript.
- **UI design**: follows the agreed mockup (linked in the spec):
  - Each list row has an ingredient summary.
  - Filters are a sidebar on wide screens and a collapsible `<details>` panel on narrow ones,
    chosen by CSS on screen width only.
  - The recipe page is two-column (ingredients card beside the method, circled step numbers).
  - New colour tokens are added for muted text, borders and pills.
- **Addresses**: `/recipes/{file stem}`. The reference French 75 ships as
  `src/website/recipes/french-75.md`, with the typo fixes ("into", "Pierce").

## Technical Context

**Language/Version**: Python 3.15 (CPython), Jinja2 templates, CSS

**Primary Dependencies**: FastAPI, Jinja2, Uvicorn, pydantic-settings, htmx 4.0.1 (existing).
New:
- `markdown-it-py` (MIT): CommonMark parser
- `mdit-py-plugins` (MIT): front-matter plugin
- `pyyaml` (MIT): preamble and vocabulary

All are added with `uv add` at their latest releases.

**Storage**: Markdown and YAML files in the repository, read at start-up. No runtime storage.

**Testing**: pytest, FastAPI `TestClient`, pytest-playwright (Chromium), axe-playwright-python.
Tests use a fixed fixture collection via `WEBSITE_RECIPES_DIR`.

**Target Platform**: Linux container behind Caddy. Current evergreen browsers (`<datalist>` and
`type="search"` are Baseline).

**Project Type**: Server-rendered web application (single project)

**Performance Goals**: Page and filter results in under 1 s, and start-up load in under 5 s, both
with 500 recipes (SC-002, SC-003). Expected: parsing well under 1 ms per file, filtering well under
1 ms.

**Constraints**:
- No hand-written JavaScript. htmx attributes use plain values (no `js:`), because the CSP has no
  `'unsafe-eval'`.
- CSP unchanged, so no inline styles. Recipe content cannot inject markup (FR-019).
- Works without JavaScript. Filters live in the URL.
- WCAG 2.2 AA in both themes. Usable at 320 px with no horizontal page scroll.

**Scale/Scope**:
- New code: 1 domain module, 2 routes, 2 templates, CSS additions, 1 setting.
- New content: the recipes folder (README, vocabulary, 1 recipe) and fixture collections.
- About 6 test modules.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Modern Python toolchain | Three new well-supported public packages, added with `uv add` and locked. No bespoke markdown or YAML parsing. | ✅ Pass |
| II. Server-rendered UI, no hand-written JS | Pages are rendered on the server. Live filtering uses the vendored htmx with `hx-select`. Suggestions use native `<datalist>`. Without JS, the GET form submits normally. | ✅ Pass |
| III. Type safety & style | Domain types are typed frozen dataclasses. External input (preamble, vocabulary, query, settings) is validated by Pydantic models. Every public item has a docstring. | ✅ Pass |
| IV. Testing | Unit tests cover parsing, validation messages, filtering and the 500-recipe timing. A shipped-collection test acts as the merge gate. `TestClient` tests cover routes, 404 and start-up failure. Playwright covers live filtering, focus, no-JS, the recipe page, 320 px, and axe in both themes. | ✅ Pass |
| V. Simplicity | No database, cache or index: an in-memory tuple and linear filter at this scale. A spec-level justification for no infrastructure is in the spec's Assumptions. Domain logic is in `cookbook.py`, separate from routes and templates. | ✅ Pass |
| VI. Licence & attribution | The new dependencies are MIT, which is compatible with AGPL-3.0. No new visitor-facing third-party assets. Recipes are the owner's own content. No cookies, so the About page statements stay accurate. | ✅ Pass |
| Tech constraints | CSP, Docker, Caddy and CI workflow unchanged. The recipe folder ships via the existing `COPY src`. | ✅ Pass |

**Post-design re-check (after Phase 1)**: still passes. The contracts add two GET routes with no
side effects, no scripts, no inline styles, no storage and no new assets. The README in the recipe
folder satisfies FR-005. The constitution's README rule is met by adding a "Recipes" section to the
root `README.md` that points to it.

## Project Structure

### Documentation (this feature)

```text
specs/004-recipe-database/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── recipe-format.md # Authoring format: folder, vocabulary.yaml, recipe grammar
│   ├── http.md          # GET /recipes (query), GET /recipes/{slug}, start-up behaviour
│   └── page-layout.md   # DOM contract: filter form, results, recipe page, accessibility
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/website/
├── cookbook.py                 # NEW: pure domain: Vocabulary, Recipe, IngredientEntry,
│                               #   load_collection, RecipeCollectionError, RecipeQuery,
│                               #   filter_recipes
├── config.py                   # + recipes_dir setting (WEBSITE_RECIPES_DIR)
├── app.py                      # + load collection in create_app → app.state.recipes
├── content.py                  # + RECIPES page in PAGES (before ABOUT)
├── routes.py                   # + GET /recipes, GET /recipes/{slug}
├── recipes/                    # NEW: recipe content (package data, no __init__.py)
│   ├── README.md               #   authoring guide (from contracts/recipe-format.md)
│   ├── vocabulary.yaml         #   types and master ingredient list
│   └── french-75.md            #   the reference recipe, typos fixed
├── static/css/site.css         # + filter form, results list, recipe page styles
└── templates/
    ├── recipes.html            # NEW: list page with filter form and #recipe-results
    └── recipe.html             # NEW: single recipe page

tests/
├── fixtures/recipes/
│   ├── valid/                  # NEW: small fixed collection used by integration and e2e tests
│   └── invalid/                # NEW: one file per problem, for the validation report
├── unit/
│   ├── test_cookbook.py        # NEW: parsing, display names, every validation message,
│   │                           #   filtering rules, 500-recipe timing
│   ├── test_shipped_recipes.py # NEW: shipped collection is valid (merge gate)
│   ├── test_config.py          # + recipes_dir default and override
│   └── test_content.py         # + page order
├── integration/
│   ├── test_recipes.py         # NEW: list and filters, recipe page, 404, unsafe content
│   │                           #   escaped, start-up failure on invalid collection
│   └── test_navigation.py      # + drawer link and aria-current on list and recipe pages
└── e2e/
    ├── test_recipes.py         # NEW: live filtering keeps focus, URL updates, datalist, clear,
    │                           #   no-JS, recipe page, 320 px
    └── test_accessibility.py   # + list (filtered, empty) and recipe page in both themes

README.md                       # + "Recipes" section linking to src/website/recipes/README.md
```

**Structure Decision**: Keep the single-project layout. The domain module is named `cookbook.py`
rather than `recipes.py`, so it does not share a name with the `recipes/` content folder beside it.
Integration and e2e tests run against `tests/fixtures/recipes/valid`, so they are unaffected as real
recipes are added. Only `test_shipped_recipes.py` looks at the real folder.

## Complexity Tracking

No constitution violations to justify.
