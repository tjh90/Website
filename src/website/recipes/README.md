# Writing recipes

Each recipe on the site's Recipes page (`/recipes`) is a markdown file in this folder. The site
reads the folder when it starts. **It will not start if any file here is invalid**, so check your
changes before committing (see [Checking](#checking)).

## Folder layout

```text
src/website/recipes/
├── README.md          # This guide (not a recipe)
├── vocabulary.yaml    # Recipe types and the master ingredient list
└── <name>.md          # One recipe per file
```

The file name sets the recipe's address: `french-75.md` is shown at `/recipes/french-75`. Use
lower-case letters and digits, with single hyphens between words.

## `vocabulary.yaml`

This file lists every recipe type and every ingredient the recipes may use. It keeps ingredient
names consistent, so the ingredient filter finds every recipe that uses an ingredient.

```yaml
# Recipe types, in the order shown in the filter.
types:
  - Drink
  - Breakfast

# Master ingredient list. Every ingredient in every recipe must appear here.
# Use the spelling to show on the site. No "/" or parentheses.
ingredients:
  - Gin
  - Lime
```

- Both lists must have at least one entry, and no name may appear twice (case is ignored).
- Ingredient names cannot contain `/` or parentheses, because recipes use those for alternatives
  and amounts.
- To use a new ingredient, add it here first. Names you list but do not use yet are fine.
- Recipes may write names in any case (`gin`), but the site always shows this file's spelling
  (`Gin`).

## A recipe file

```markdown
---
type: DRINK
---

# French 75

## Ingredients

- [OPTIONAL] Elderflower cordial (10 ml)
- Gin (50 ml)
- Ice cubes
- Lime
- Champagne/Prosecco/Cava

## Method

1. Add the ice cubes to a small tumbler.
1. Pour the gin and elderflower cordial into the glass.
1. Chop the lime into segments. Pierce a segment with a fork and squeeze the lime juice into the glass. Once juiced, drop the lime segment into the glass.
1. Top up the glass with sparkling wine.
```

The parts, in order:

1. **Preamble**: `type: ...` between two `---` lines at the very top of the file, and nothing else.
   The type must be one of the `types` in `vocabulary.yaml` (case is ignored).
2. **Name**: exactly one `#` heading. Nothing else may come between the preamble and
   `## Ingredients`. Names must be unique across the collection (case is ignored).
3. **Sections**: `## Ingredients` then `## Method`, once each (case is ignored). No other `#` or
   `##` headings. `###` and smaller headings are fine inside the method.
4. **Ingredients**: one bulleted list (`-`, `*` or `+`), one ingredient per item, on one line,
   with no nested lists.
5. **Method**: any markdown: paragraphs, numbered or bulleted lists, emphasis and links. It cannot
   be empty. Raw HTML is shown as plain text and images are not supported.

### Ingredient lines

```text
[OPTIONAL] Name/Alternative/Alternative (amount)
└ optional ┘ └─ one or more, "/"-separated ─┘ └ optional, at end ┘
```

- `[OPTIONAL]` marks an ingredient the recipe works without. It must be upper case and followed
  by a space.
- `/` separates interchangeable ingredients: `Champagne/Prosecco/Cava` is shown as "Champagne,
  Prosecco or Cava", and the recipe is found by filtering for any of them. Each name must be in
  `vocabulary.yaml`, and none may be repeated or empty.
- The amount is free text in one pair of parentheses at the end, such as `(50 ml)` or
  `(2 slices)`. It cannot be empty or contain parentheses.

## Checking

Run the recipe check from the repository root:

```shell
uv run pytest tests/unit/test_shipped_recipes.py
```

It reports every problem in every file, one per line, as `<file>: <message>`. For example:

```text
french-75.md: unknown ingredient "Limes"
aperol-spritz.md: missing section "Method"
```

Unknown types and ingredients are named, but no alternatives are suggested: check
`vocabulary.yaml` for the right spelling, or add the new name there. The same check runs in CI,
and the site will not start until every problem is fixed. Changes appear on the site the next time
it starts.
