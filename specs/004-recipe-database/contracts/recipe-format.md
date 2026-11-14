# Contract: Recipe Authoring Format

This is the interface between the site owner and the site. It will also be published for authors
as `src/website/recipes/README.md` (FR-005).

## Folder

```text
src/website/recipes/
├── README.md          # Authoring guide (ignored by the loader)
├── vocabulary.yaml    # Recognised types and the master ingredient list
└── <slug>.md          # One recipe per file, e.g. french-75.md → /recipes/french-75
```

`<slug>` is lower-case letters and digits in words joined by single hyphens.

## `vocabulary.yaml`

```yaml
# Recipe types, in the order shown in the filter.
types:
  - Drink
  - Breakfast
  - Lunch
  - Dinner
  - Snack
  - Side
  - Dessert

# Master ingredient list. Every ingredient in every recipe must appear here.
# Use the spelling to show on the site. No "/" or parentheses.
ingredients:
  - Cava
  - Champagne
  - Elderflower cordial
  - Gin
  - Ice cubes
  - Lime
  - Prosecco
```

## Recipe file

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

Rules, in file order:

1. **Preamble**: a YAML block between `---` lines at the very top, containing only `type`. The
   type must be in `vocabulary.yaml`'s `types`. Case is ignored.
2. **Name**: exactly one `#` heading.
3. **Sections**: exactly `## Ingredients` then `## Method` (case ignored). No other `#`/`##`
   headings. `###` and below are allowed inside the method.
4. **Ingredients**: one bulleted list (`-`, `*` or `+`), one ingredient per item, with no nested
   lists. Each item is:

   ```text
   [OPTIONAL] Name/Alternative/Alternative (amount)
   └ optional ┘ └─ one or more, "/"-separated ─┘ └ optional, at end ┘
   ```

   - `[OPTIONAL]` is upper case and followed by a space.
   - Every name, including each alternative, must be in `ingredients` (case ignored). It is shown
     with the vocabulary's spelling.
   - The amount is free text in a single pair of parentheses at the end. It cannot be empty or
     contain parentheses.
5. **Method**: any markdown text (paragraphs, numbered or bulleted lists, emphasis, links).
   Raw HTML is shown as plain text, and images are not supported.

## Checking

Run the recipe collection test (see [quickstart](../quickstart.md#checking-recipes)). Every problem
in every file is reported as `<file>: <message>`. Unknown types and ingredients are named but no
alternatives are suggested: check `vocabulary.yaml` for the right spelling. The same check runs in
CI and when the site starts, and the site will not start with an invalid collection.
