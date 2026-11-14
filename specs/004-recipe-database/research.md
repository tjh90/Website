# Research: Recipe Database

Phase 0 decisions for feature 004. Each records what was chosen, why, and what was rejected.

## R1. Storage: files in the repository, loaded into memory at start-up

- **Decision**: Recipes are markdown files in `src/website/recipes/`. They are parsed and validated
  once when the app is created and kept in memory as an immutable `RecipeCollection` on
  `app.state`. No database.
- **Rationale**: A few hundred files of under 2 KB each come to well under 1 MB. Git provides
  history, review and backup. Keeping the folder inside the package means it ships in the wheel
  and the Docker image with no Dockerfile change, the same way `templates/` and `static/` do.
  Constitution V requires a spec-level justification for a database; none exists.
- **Alternatives considered**: SQLite (adds schema, migrations and a write path nobody needs);
  a top-level `recipes/` folder (needs Dockerfile and runtime path changes for no gain); reading
  files per request (slower, and errors would surface to visitors rather than at start-up).

## R2. Recipe folder location is configurable

- **Decision**: A new setting, `recipes_dir` (`WEBSITE_RECIPES_DIR`), defaults to the packaged
  folder.
- **Rationale**: Integration and browser tests need a small fixed collection whose contents do not
  change as real recipes are added. Pydantic settings is how the app already takes configuration.
- **Alternatives considered**: Passing a collection to `create_app` (couples tests to internals and
  bypasses the start-up loading path); monkeypatching a module constant (fragile).

## R3. Markdown parsing: markdown-it-py with the front-matter plugin, and PyYAML

- **Decision**: Parse each file into tokens with `markdown-it-py` (`commonmark` preset, `html`
  disabled, `image` rule disabled), plus `mdit-py-plugins`' `front_matter_plugin` to capture the
  preamble. Load the preamble with `yaml.safe_load` (PyYAML) and validate it with a Pydantic model
  that forbids extra keys. Walk the token stream to find the single `h1` (the name) and the
  `## Ingredients` and `## Method` sections.
- **Rationale**: One parser gives both the structure (headings, list items) and safe HTML for the
  method, so the structure check and the rendering cannot disagree. markdown-it-py is the
  CommonMark-compliant parser maintained by the Executable Books project. With `html` disabled,
  raw HTML in a file is shown as text, and its `validateLink` rejects `javascript:`, `vbscript:`,
  `file:` and `data:` links, which satisfies FR-019. Images are disabled because they are out of
  scope and the CSP would block external ones anyway. All three packages are MIT-licensed, which
  is compatible with AGPL-3.0.
- **Alternatives considered**: `python-frontmatter` + `markdown` (two passes over the file, and
  Python-Markdown passes raw HTML through by default); `mistune` (fine, but its AST plugin API is
  less stable); regex splitting of the file (bespoke and fragile, contrary to constitution I).

## R4. Recipe file grammar

- **Decision**: The format of the reference file is the contract
  ([contracts/recipe-format.md](contracts/recipe-format.md)):
  - YAML preamble with exactly one key, `type`, matched to the vocabulary ignoring case.
  - Exactly one `#` heading: the recipe name.
  - Exactly two `##` sections, `Ingredients` then `Method`, matched ignoring case. Any other
    section fails, so a misspelt heading is caught rather than silently dropped.
  - Ingredients: one flat bulleted list. Each item is a single line parsed with
    `^(?:\[OPTIONAL\]\s+)?(?P<names>[^()]+?)(?:\s*\((?P<amount>[^()]*)\))?$`. `names` is split
    on `/` and each part is trimmed. `[OPTIONAL]` must be upper case, so typos are caught.
  - Method: any block content, rendered as given.
- **Rationale**: Strict validation keeps the collection consistent (FR-008), and an author gets one
  clear message rather than a recipe that renders oddly.
- **Alternatives considered**: Allowing any extra sections (typos would go unnoticed); putting the
  name in the preamble (duplicates the heading the author already writes).

## R5. Recipe address: the file name

- **Decision**: A recipe's URL is `/recipes/{slug}`, where `slug` is the file name without `.md`.
  It must match `^[a-z0-9]+(?:-[a-z0-9]+)*$`, so `french-75.md` is served at `/recipes/french-75`.
- **Rationale**: Stable even if the display name is reworded. It needs no slug library, and file
  names are unique within a folder by definition. Requiring lower case avoids clashes between
  Windows (case-insensitive) and Linux (case-sensitive) checkouts.
- **Alternatives considered**: Slugifying the name with `python-slugify` (the URL would change when
  the name is edited, and it adds a dependency); numeric IDs (not readable).

## R6. Consistency: a vocabulary file and a collection check

- **Decision**: `src/website/recipes/vocabulary.yaml` holds two ordered lists, `types` and
  `ingredients`, validated by a Pydantic model. The loader collects every problem across all files
  into a `RecipeCollectionError` with one line per problem (`file: message`). Unknown types and
  ingredients are reported by name only, with no "near miss" suggestions: the master list is the
  reference (decided 2026-11-14).
  Enforcement happens at three points:
  1. **Merge gate**: a unit test loads the shipped folder and fails with the full report. It runs in
     the existing CI `test` job, so a pull request with an invalid recipe fails CI.
  2. **Start-up**: `create_app` loads the collection and raises on any problem, so an invalid
     collection never serves (FR-010). The Docker health check then fails, as for any start-up error.
  3. **Authoring**: the author runs the same test locally (see quickstart).
- **Rationale**: One loader is used for every check, so CI and production cannot disagree.
  YAML is consistent with the preamble format and allows
  comments.
- **Alternatives considered**: A separate CLI command (a second entry point to maintain while the
  test already gives the report; it can be added later); a pre-commit hook (the constitution
  removed them); a plain-text list (no place for types, and no validation model); "did you mean"
  suggestions via `difflib` (rejected by the site owner: the master list already serves that
  purpose).

## R7. Filtering: pure domain function, GET query parameters

- **Decision**: `GET /recipes?type=drink&type=side&name=spr&ingredient=gin`. A Pydantic
  `RecipeQuery` model parses the query leniently (unknown types are ignored, text is trimmed and
  length-capped). `filter_recipes(collection, query)` returns a `RecipeSearch`: the matching
  recipes. Ingredient text that is not in the vocabulary simply matches nothing.
  - Types: any of the ticked types; none ticked means all.
  - Name: case-insensitive substring of the recipe name (`str.casefold`).
  - Ingredient: casefolded exact match against a vocabulary name. A recipe matches if any
    alternative of any entry is that ingredient; optional entries count.
  - All filters are combined with AND.
- **Rationale**: GET makes filters shareable (FR-015, US3 scenario 8) and work without JavaScript.
  A pure function is unit-testable (constitution V). With 500 recipes a linear scan takes well
  under a millisecond, so no index is needed.
- **Alternatives considered**: POST (filters would not be in the URL); a pre-built inverted index
  (premature at this scale).

## R8. Live filtering with htmx: swap only the results

- **Decision**: The filter form is a normal `method="get" action="/recipes"` form with
  `hx-get="/recipes" hx-trigger="submit, input delay:250ms" hx-target="#recipe-results"
  hx-select="#recipe-results" hx-swap="outerHTML" hx-push-url="true" hx-sync="this:replace"`.
  The server always returns the full page, and htmx picks out the results.
- **Rationale**: Swapping only the results keeps focus and the caret in the box being typed in.
  Returning the full page means no fragment-or-page switch on `HX-Target` and no extra `Vary`
  header. Boosted navigation, history restore (htmx 4 sends a plain GET with
  `HX-History-Restore-Request`) and no-JS submission all get a correct page from the same route.
  Checkboxes fire `input` events, so one trigger covers every control. `hx-sync` drops stale
  responses. Rendering the full page costs a few milliseconds.
- **Alternatives considered**: A fragment endpoint chosen by `HX-Target` (more code, and the
  response must also vary on that header); relying on the body-wide boost (it would replace the
  whole body and lose focus on every keystroke).

## R8a. Filter button only without JavaScript; collapsible filters on narrow screens

- **Decision**: The "Filter" submit button is hidden with `@media (scripting: enabled)` in
  `site.css`, so it shows only when JavaScript is off. The form sits inside
  `<details class="recipe-filters-panel">` whose `<summary>` reads "Filters", followed by
  "· N active" when filters are set. The server never adds `open`: on narrow screens the panel
  starts collapsed. On wide screens (`min-width: 768px`) CSS hides the summary and forces the
  content visible with `details::details-content { content-visibility: visible; display: contents }`.
  The count lives in `#filter-count` inside the summary. The htmx request also selects it with
  `hx-select-oob="#filter-count"`, so it updates live alongside the results.
- **Rationale**: The `scripting` media feature and `::details-content` are Baseline in current
  evergreen browsers, so neither needs a script (constitution II). Choosing by viewport width in
  CSS keeps one cacheable response for every device. Sniffing `User-Agent` is unreliable (tablets,
  resized windows), would need `Vary: User-Agent`, and puts layout logic on the server. Without
  JavaScript, implicit submission is blocked with several text fields and no button, so the
  button must stay for that case.
- **Alternatives considered**: Always showing the button (redundant with live filtering, as the
  site owner noted); User-Agent detection (above); a script-driven toggle (constitution II).
- **To confirm during implementation**: htmx 4 supports `hx-select-oob`. If it does not, use its
  htmx 4 equivalent, or move the count into `#recipe-results` with a visually hidden copy, and
  update [contracts/page-layout.md](contracts/page-layout.md).

## R9. Ingredient suggestions: native `<datalist>`

- **Decision**: `<input list="ingredient-options">` with a `<datalist>` of every vocabulary
  ingredient, in vocabulary order.
- **Rationale**: Native and needs no JavaScript (constitution II). Supported by all evergreen
  browsers, and accessible to screen readers.
- **Alternatives considered**: An htmx-driven suggestion list (more requests and markup, and the
  keyboard and ARIA behaviour would have to be rebuilt by hand).

## R10. Display

- **Decision**:
  - The list shows the name (linked) and type, sorted with `casefold()` by name.
  - The filter shows only types with at least one recipe, in vocabulary order.
  - Ingredient names are shown with the vocabulary's spelling (e.g. `gin` is shown as `Gin`).
  - Alternatives are joined as "A, B or C".
  - Optional entries get a visible "optional" label, and the amount is shown after the name.
  - The method HTML comes from markdown-it-py. Repeated `1.` items render as `<ol>`, which the
    browser numbers 1, 2, 3.
  - The recipe page title is the recipe name. The drawer marks "Recipes" as current on both the
    list and recipe pages.
- **Rationale**: Consistent spelling makes the filter predictable. Hiding types with no recipes
  avoids filters that always return nothing.
- **Alternatives considered**: Showing the author's original spelling (inconsistent across
  recipes).

## R11. Performance targets (SC-002, SC-003)

- **Decision**: A unit test generates 500 synthetic recipe files in `tmp_path` and checks that
  loading takes under 5 s. A filter over 500 recipes is checked to finish well under 1 s.
- **Rationale**: markdown-it-py parses small documents in well under a millisecond each, so both
  targets have a large margin. The test guards against accidental quadratic behaviour.
