# Quickstart: Recipe Database

Validation guide for feature 004. Markup, routes and the file format are in
[contracts/](contracts/); types and rules are in [data-model.md](data-model.md).

## Prerequisites

- uv installed. Dependencies synced (`uv sync`), including the new `markdown-it-py`,
  `mdit-py-plugins` and `pyyaml`.
- Playwright browsers installed (`uv run playwright install --with-deps chromium firefox`).

## Checking recipes

After adding or editing a recipe or `vocabulary.yaml`, run only the shipped-collection check:

```bash
uv run pytest tests/unit/test_shipped_recipes.py
```

Expected: it passes, or it fails with a report of every problem as `<file>: <message>`.

## Automated checks

All quality gates from the constitution:

```bash
uv lock --check
```

```bash
uv run ruff format --check
```

```bash
uv run ruff check
```

```bash
uv run ty check
```

```bash
uv run pytest
```

## Manual walkthrough

Start the site (`uv run website`) and open `/recipes`.

| # | Do | Expect |
|---|---|---|
| 1 | Open the drawer | "Recipes" sits between Anascramble and About |
| 2 | Look at the list | French 75 listed with type "Drink" and its ingredient summary; status "1 recipe"; filters in a sidebar; no "Filter" button |
| 3 | Select French 75 | `/recipes/french-75`; "optional" on Elderflower cordial; "10 ml" and "50 ml" amounts; "Champagne, Prosecco or Cava"; method numbered 1–4 in circles, to the right of the ingredients |
| 4 | Back on the list, type `prosecco` in Ingredient | Suggestions appear while typing; French 75 stays listed without a page reload; URL gains `?…ingredient=prosecco` |
| 5 | Change it to `limes` | "No matching recipes." |
| 6 | Untick/tick "Drink", type in Name | List updates live; focus stays in the field |
| 7 | Copy the URL into a new tab | Same filters and results |
| 8 | Press "Clear filters" | All recipes, empty controls |
| 9 | Disable JavaScript, filter and press "Filter" (now visible) | Same results by normal form submission |
| 10 | Switch theme; narrow the window to 320 px | Readable in both themes; no sideways page scroll; filters collapsed behind "Filters"; recipe page stacks ingredients above method |
| 11 | At phone width, open "Filters" and tick "Drink" | Toggle reads "Filters · 1 active"; list updates without a reload |
| 12 | Visit `/recipes/nope` | Site's "Page not found" page |

## Enforcement walkthrough

| # | Do | Expect |
|---|---|---|
| 1 | Change `- Lime` to `- Limes` in `french-75.md` and run the check | Fails: `french-75.md: unknown ingredient "Limes"` |
| 2 | Start the site with that change | It refuses to start and prints the same report |
| 3 | Rename `## Method` to `## Methd` | Check reports `unknown section "Methd"` (only the typo, not a missing "Method") |
| 4 | Add `Gin (50 ml` | Check reports unbalanced parentheses |
| 5 | Revert all changes | Check passes and the site starts |

In CI the same check runs in the `test` job, so a pull request containing an invalid recipe fails.
