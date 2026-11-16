# Data Model: Recipe Database

All domain types live in `src/website/cookbook.py` (pure: no FastAPI or Jinja imports). They are
frozen dataclasses unless marked as Pydantic models, which are used where external input is
validated (constitution III). Nothing is persisted at runtime: everything is built from files
at start-up.

## Vocabulary *(Pydantic, from `vocabulary.yaml`)*

| Field | Type | Rules |
|---|---|---|
| `types` | `list[str]` | Non-empty. Each entry is trimmed and non-empty, with no duplicates ignoring case. Order is the filter order. |
| `ingredients` | `list[str]` | Non-empty. Each entry is trimmed, non-empty and contains no `/` or parentheses, with no duplicates ignoring case. Order is the datalist order. |

Extra keys are forbidden. Derived lookups are built once: `casefold(name) → canonical name` for
both lists.

## RecipeType

| Field | Type | Notes |
|---|---|---|
| `name` | `str` | Canonical display name from the vocabulary, e.g. `Drink` |
| `key` | `str` | `name.casefold()`, used in query strings (`?type=drink`) |

## IngredientEntry

One line of the ingredients list.

| Field | Type | Rules |
|---|---|---|
| `alternatives` | `tuple[str, ...]` | At least 1. Canonical vocabulary names, in the order written. No duplicates within the entry. |
| `amount` | `str \| None` | Trimmed text from the trailing parentheses. Empty parentheses are an error. |
| `optional` | `bool` | `True` when the line starts with `[OPTIONAL] ` |

Derived: `display_name` returns "A", "A or B", or "A, B or C".

## Recipe

| Field | Type | Rules |
|---|---|---|
| `slug` | `str` | File stem, matching `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Unique (guaranteed by the folder). |
| `name` | `str` | Text of the single `#` heading, trimmed and non-empty. Unique ignoring case across the collection. |
| `type` | `RecipeType` | From the preamble `type`, matched to the vocabulary ignoring case |
| `ingredients` | `tuple[IngredientEntry, ...]` | At least 1 |
| `method_html` | `str` | Safe HTML rendered from the method section, which must not be empty |
| `source` | `Path` | File path, used only in error messages |

Derived: `ingredient_keys: frozenset[str]` holds the casefolded names of every alternative of every
entry, for filtering. `ingredient_summary: str` joins each entry's `display_name` with " · ", in
recipe order, for the list page.

## RecipePreamble *(Pydantic)*

| Field | Type | Rules |
|---|---|---|
| `type` | `str` | Required. Extra keys are forbidden. |

## RecipeCollection

| Field | Type | Notes |
|---|---|---|
| `recipes` | `tuple[Recipe, ...]` | Sorted by `name.casefold()` |
| `vocabulary` | `Vocabulary` | |

Derived:
- `by_slug: Mapping[str, Recipe]`
- `types_in_use: tuple[RecipeType, ...]`: vocabulary order, only types with at least one recipe
- `ingredient_names: tuple[str, ...]`: vocabulary order, for the datalist

Built by `load_collection(directory: Path) -> RecipeCollection`. This reads `vocabulary.yaml` and
every `*.md` file except `README.md`. It raises `RecipeCollectionError` if there is any problem.

## RecipeProblem / RecipeCollectionError

| Field | Type | Notes |
|---|---|---|
| `source` | `Path` | Offending file (`vocabulary.yaml` or a recipe) |
| `message` | `str` | Human-readable, e.g. `unknown ingredient "Limes"` |

`RecipeCollectionError(problems: tuple[RecipeProblem, ...])` holds every problem. Its `str()` is a
report with one line per problem, sorted by file. All files are checked before raising, so one run
reports everything (FR-008).

Problems detected (each with file and message):

| Check | Example message |
|---|---|
| Vocabulary invalid or missing | `vocabulary: duplicate ingredient "lime"` |
| File not UTF-8 / YAML invalid | `preamble is not valid YAML: …` |
| Preamble missing, not a mapping, or extra keys | `preamble must contain only "type"` |
| Unknown type | `unknown type "DRNK"` |
| Slug invalid | `file name must be lower-case words joined by hyphens` |
| Zero or several `#` headings | `expected exactly one "#" recipe name heading, found 2` |
| Missing, duplicate, misordered or unknown `##` section | `unknown section "Ingrediants"` |
| Ingredients section not one flat bullet list | `ingredients must be a single bulleted list` |
| Malformed ingredient line | `ingredient line "Gin (50 ml" has unbalanced parentheses` |
| Empty amount / empty alternative | `ingredient line "Gin ()" has an empty amount` |
| Unknown ingredient | `unknown ingredient "Limes"` |
| Empty method | `method section is empty` |
| Duplicate name | `recipe name "French 75" is also used by french-seventy-five.md` |

## RecipeQuery *(Pydantic, from query parameters)*

| Field | Type | Parsing |
|---|---|---|
| `type` | `list[str]` | Casefolded. Values that are not a type key are dropped silently. |
| `name` | `str` | Trimmed, capped at 100 characters, default `""` |
| `ingredient` | `str` | Trimmed, capped at 100 characters, default `""` |

Never rejects input with a 422: tampered values become "no filter" (as in feature 003).

## RecipeSearch *(result of `filter_recipes(collection, query)`)*

| Field | Type | Notes |
|---|---|---|
| `query` | `RecipeQuery` | Echoed back so the form can be re-filled |
| `recipes` | `tuple[Recipe, ...]` | Matches in collection order |
| `is_filtered` | `bool` | Whether any filter is active (controls the "Clear filters" link) |
| `active_filter_count` | `int` | Number of ticked valid types, plus 1 for a non-empty name, plus 1 for a non-empty ingredient. Shown in the "Filters · N active" toggle. |

Rules: an ingredient text that is not in the vocabulary gives `recipes == ()`. All other filters are
combined with AND, as in research R7.
