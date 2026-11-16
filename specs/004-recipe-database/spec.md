# Feature Specification: Recipe Database

**Feature Branch**: `claude/recipe-database-suggester-303d49` (spec-kit feature id `004-recipe-database`)

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "I'd like to add a new page that acts as a recipe database/suggester. Each
recipe will have: a type (drink, breakfast, snack, side, etc.) in the preamble; a list of ingredients
(some may be prefixed with `[OPTIONAL]`, some may be suffixed by an amount, some may be required but
have alternatives denoted with a `/`, e.g. `Champagne/Prosecco/Cava`); a method section that might be
a paragraph or itemized list. I'd like to be able to author and store the recipes as markdown files
and have them rendered to HTML on the website. I'd like a list of all recipes that I can filter by
type (checkbox), contained ingredient (textbox), and name (textbox). We will also need some mechanism
for checking that ingredients are consistent between recipes so that the ingredient filter/search
works properly, and a way of enforcing this. Recipes preserved as a folder in the website repo that
is searched and parsed when the website starts up. 10s to 100s of recipes. No DB needed."

## Clarifications

### Session 2026-11-14

- Q: How are "recognised ingredient names" defined? → A: A hand-maintained master ingredient list
  that every recipe must use.
- Q: Does "suggester" mean anything beyond the filters? → A: No; the type, name and ingredient
  filters are the suggester.
- Q: Does the ingredient box take one ingredient or several? → A: A single ingredient.
- Q: How is an ingredient's amount separated from its name? → A: The amount is written in
  parentheses at the end of the line, e.g. `Gin (50 ml)`.
- Q: Should unknown ingredient or type names come with "did you mean" suggestions (in the check or
  the filter)? → A: No. The master ingredient list is the reference; no near-miss matching.
- Q: Which UI design decisions from the mockup are adopted? → A: An ingredient summary line under
  each recipe in the list; filters collapsible on narrow screens with an active-filter count; no
  helper text under the ingredient box; a two-column recipe page on wide screens; no "Filter"
  button while scripting is available (it remains for visitors without JavaScript).

## UI Design

The agreed mockup is the "Recipes UI mockup" design canvas
(<https://claude.ai/artifact/1e7Yuhg4R4t8cfjDSiHQDV>). It follows the site's existing look: the
blue header with a centred title, the system font, and the existing light and dark colours.

## Reference Recipe File

The site owner supplied this example of the authoring format; it is the reference for FR-002 to
FR-004:

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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse and read recipes (Priority: P1)

A visitor opens the Recipes page and sees every recipe listed by name with its type. Choosing a
recipe shows it in full: its name, type, ingredients (with amounts, optional ingredients and
alternatives clearly marked) and method, formatted for easy reading.

**Why this priority**: Without published, readable recipes nothing else has value. This slice alone
replaces a scattered collection of notes with a single readable reference.

**Independent Test**: Add a few recipe files to the recipe collection, start the site, open the
Recipes page, and check that every recipe is listed and each one displays correctly.

**Acceptance Scenarios**:

1. **Given** the recipe collection holds N valid recipes, **When** the visitor opens the Recipes
   page, **Then** all N recipes are listed, sorted alphabetically by name, each showing its name and
   type.
2. **Given** a recipe in the list, **When** the visitor selects it, **Then** its full recipe is shown
   on its own page with a stable, shareable address.
3. **Given** a recipe with an ingredient marked `[OPTIONAL]`, **When** it is displayed, **Then** that
   ingredient is visibly marked as optional (and not with the raw `[OPTIONAL]` text).
4. **Given** a recipe with an ingredient `Champagne/Prosecco/Cava`, **When** it is displayed,
   **Then** the alternatives are shown as a choice of one (e.g. "Champagne, Prosecco or Cava").
5. **Given** a recipe with an ingredient amount, **When** it is displayed, **Then** the amount is
   shown alongside the ingredient name.
6. **Given** a method written as a paragraph, or as a numbered or bulleted list, **When** the recipe
   is displayed, **Then** the method keeps that structure.
7. **Given** the recipe list, **When** it is shown, **Then** each recipe shows a one-line summary of
   its ingredients under its name, e.g. "Elderflower cordial · Gin · Ice cubes · Lime · Champagne,
   Prosecco or Cava".
8. **Given** a wide screen, **When** a recipe is displayed, **Then** the ingredients and method are
   shown side by side; **Given** a narrow screen, **Then** they are stacked, ingredients first.

---

### User Story 2 - Author a recipe as a simple text file (Priority: P1)

The site owner writes a new recipe as a plain markdown file in the recipe folder of the website
repository, using a documented, lightweight format, and it appears on the site the next time the
site starts.

**Why this priority**: Authoring ease is the reason for choosing text files; the format and its
rules underpin every other story.

**Independent Test**: Following only the documented format, write a new recipe file, restart the
site, and confirm the recipe appears and renders as intended.

**Acceptance Scenarios**:

1. **Given** a correctly formatted new recipe file in the recipe folder, **When** the site starts,
   **Then** the recipe appears in the list and on its own page.
2. **Given** a recipe file that is missing a required part (name, type, ingredients or method),
   **When** the recipe collection is checked, **Then** the check fails and names the file and the
   missing part.
3. **Given** a recipe file is edited, **When** the site next starts, **Then** the change is shown.
4. **Given** a recipe file is deleted, **When** the site next starts, **Then** the recipe no longer
   appears.

---

### User Story 3 - Filter recipes (Priority: P2)

A visitor narrows the recipe list by ticking one or more recipe types, typing part of a recipe name,
and/or typing an ingredient. The list updates to show only matching recipes, and the filters can be
combined and cleared.

**Why this priority**: Filtering turns a list into a useful finder once there are more than a
handful of recipes, but the list is still usable without it.

**Independent Test**: With a known set of recipes, apply each filter alone and in combination and
compare the results with the expected matches.

**Acceptance Scenarios**:

1. **Given** the type checkboxes, **When** the visitor ticks "drink" and "snack", **Then** only
   recipes of those types are listed; **When** no type is ticked, **Then** recipes of all types are
   listed.
2. **Given** the name box, **When** the visitor types "spritz", **Then** only recipes whose names
   contain "spritz" (ignoring case) are listed.
3. **Given** the ingredient box, **When** the visitor enters "prosecco", **Then** only recipes
   containing Prosecco (including as an alternative, such as the French 75, or as an optional
   ingredient) are listed.
4. **Given** the ingredient box, **When** the visitor starts typing, **Then** names from the master
   ingredient list are suggested.
5. **Given** the ingredient box, **When** the visitor enters text that is not a recognised
   ingredient, **Then** no recipes are listed and the "no matching recipes" message is shown.
6. **Given** several filters are set, **When** the list is shown, **Then** only recipes matching all
   of them are listed.
7. **Given** no recipe matches the filters, **When** the list is shown, **Then** a clear "no matching
   recipes" message is displayed.
8. **Given** filters are set, **When** the visitor copies the page address and opens it elsewhere,
   **Then** the same filters and results are shown.
9. **Given** a narrow screen (phone), **When** the visitor opens the Recipes page, **Then** the filters
   are collapsed behind a "Filters" toggle that shows how many filters are active, and the results
   are visible without scrolling past the filters; **Given** a wide screen, **Then** the filters are
   always shown beside the results.
10. **Given** scripting is available, **When** the visitor changes any filter, **Then** the results
    update as they type and no "Filter" button is shown; **Given** scripting is not available,
    **Then** a "Filter" button is shown and submits the filters.

---

### User Story 4 - Keep ingredient names consistent (Priority: P2)

The site owner keeps a master ingredient list in the repository. When recipes are added or edited,
an automated check confirms that every ingredient name in every recipe is on that list, so that "Lime", "Limes" and "lime juice (fresh)"
do not silently split the ingredient filter. Inconsistent recipes are caught before they reach the
live site.

**Why this priority**: The ingredient filter is only trustworthy if names are consistent; the
check protects User Story 3 as the collection grows to hundreds of recipes.

**Independent Test**: Add a recipe that uses an unrecognised or near-duplicate ingredient name, run
the project's quality checks, and confirm they fail with a message naming the file and the
offending ingredient; fix it and confirm they pass.

**Acceptance Scenarios**:

1. **Given** every recipe uses only names on the master ingredient list, **When** the quality checks
   run, **Then** they pass.
2. **Given** a recipe uses an ingredient name that is not on the list (including any one alternative
   in a `/` group), **When** the quality checks run, **Then** they fail, naming the recipe file and
   the ingredient.
3. **Given** a failing ingredient check, **When** a change is proposed for merging, **Then** the
   change cannot be merged until the check passes.
4. **Given** a new ingredient is needed, **When** the site owner adds it to the master list and uses
   it in a recipe, **Then** the checks pass.
5. **Given** the master list contains two names differing only in case or surrounding spaces, or the
   same name twice, **When** the checks run, **Then** they fail naming the duplicates.
6. **Given** a name on the master list that no recipe uses, **When** the checks run, **Then** they
   still pass (unused names are allowed, so the list can be prepared ahead of recipes).

---

### Edge Cases

- **Optional ingredient that is also an alternative group**: e.g. `[OPTIONAL] Mint/Basil` is shown as
  an optional choice of one and is treated as both optional and alternatives for filtering.
- **Amount on an alternative group**: an amount applies to whichever alternative is chosen, e.g.
  `Champagne/Prosecco/Cava (100 ml)` shows "100 ml" once, not per alternative.
- **Parentheses that are not the amount**: only a parenthesised part at the very end of the line is
  the amount; an ingredient line with unbalanced parentheses or more than one trailing
  parenthesised part fails the collection check.
- **Empty amount**: `Gin ()` fails the collection check rather than showing empty brackets.
- **Ingredient name containing a slash that is not an alternative** (e.g. "Half/half cream"): the
  master list must not contain names with a slash, so `/` always means alternatives.
- **Type written in different case**: `DRINK`, `Drink` and `drink` are the same type, displayed
  consistently (e.g. "Drink").
- **Repeated `1.` numbering**: a method written with every item numbered `1.` (as in the reference
  file) is displayed as a correctly numbered list 1, 2, 3, ….
- **Duplicate recipe names or addresses**: two recipes with the same name (or that would get the same
  address) fail the collection check, naming both files.
- **Unknown recipe type**: a type not in the recognised set of types fails the collection check.
- **Malformed recipe file**: a file that cannot be read as a recipe fails the collection check with
  the file name and the problem; the live site never shows a half-parsed recipe.
- **Non-recipe files in the folder**: files other than recipe markdown files (e.g. a README) are
  ignored.
- **Empty collection**: the Recipes page shows a friendly "no recipes yet" message.
- **Case and spacing in filters**: name and ingredient matching ignores case and surrounding spaces.
- **Unsafe content**: markup in recipe files cannot inject scripts or styles into the site.
- **No JavaScript**: a "Filter" button appears and filtering works by submitting the filter form;
  the filters panel is still collapsible on narrow screens; only instant (as-you-type)
  updates may be lost.
- **Theme switching and narrow screens**: the list, filters and recipe pages are readable in light and
  dark themes and at phone widths without sideways page scrolling.
- **Unknown recipe address**: opening the address of a recipe that does not exist shows the site's
  standard "not found" page.

## Requirements *(mandatory)*

### Functional Requirements

**Recipe format and collection**

- **FR-001**: Recipes MUST be authored as one markdown file per recipe, stored in a dedicated folder
  in the website repository.
- **FR-002**: Each recipe file MUST follow the reference file's layout: a preamble at the top giving
  the type; the recipe name as the file's single main heading; an "Ingredients" section holding a
  bulleted list; and a "Method" section.
- **FR-003**: Each ingredient line MUST support, in combination: an optional `[OPTIONAL]` prefix; one
  or more alternatives separated by `/`; and an optional amount written in parentheses at the end of
  the line, e.g. `[OPTIONAL] Elderflower cordial (10 ml)`.
- **FR-004**: The method section MUST support a paragraph, a numbered list or a bulleted list.
- **FR-005**: The recipe format MUST be documented for authors in the repository, with a complete
  example covering every ingredient form.
- **FR-006**: The site MUST read and validate the whole recipe collection when it starts; changes to
  recipe files take effect on the next start.
- **FR-007**: Recipe types MUST come from a recognised set of types (initially at least: drink,
  breakfast, lunch, dinner, snack, side, dessert), which the site owner can extend.

**Validation and consistency**

- **FR-008**: A collection check MUST verify every recipe file and report all problems at once, each
  with the file name and a clear description: missing parts, unknown type, duplicate names,
  malformed ingredient lines and unrecognised ingredient names.
- **FR-009**: The collection check MUST run as part of the project's automated quality checks, so
  that a change with an invalid recipe cannot be merged.
- **FR-010**: If the collection is invalid at start-up, the site MUST NOT serve a partially loaded
  collection: it MUST fail to start with the collection check's report.
- **FR-011**: The repository MUST hold a hand-maintained master ingredient list. Every ingredient
  name in every recipe (each alternative individually) MUST appear on it; unlisted names MUST be
  reported with the file and the name. No "near miss" suggestions are offered: the master list is
  the reference. The list itself MUST contain no duplicates (ignoring
  case and surrounding spaces) and no names containing `/`.
- **FR-012**: Ingredient matching and checking MUST ignore letter case and surrounding spaces.

**Browsing and filtering**

- **FR-013**: The site MUST provide a Recipes page, reachable from the site's navigation, listing all
  recipes alphabetically with their name, type and a one-line summary of their ingredients
  (alternatives shown as "A, B or C"), and a page per recipe with a stable address.
- **FR-014**: Visitors MUST be able to filter the list by type (multiple checkboxes, combined as "any
  of the ticked types"), by name (case-insensitive "contains" text match) and by a single
  ingredient. The ingredient filter matches a whole name on the master ingredient list (ignoring
  case and surrounding spaces), so "gin" does not match "Ginger beer". A recipe matches if the
  ingredient is any of its alternatives; optional ingredients count as contained. Text that is not a
  listed ingredient MUST produce an empty result, with no "near miss" suggestions.
- **FR-015**: All active filters MUST combine (a recipe must satisfy every filter), MUST be reflected
  in the page address, and MUST be clearable in one action.
- **FR-016**: The ingredient box MUST offer names from the master ingredient list as suggestions
  while typing.
- **FR-017**: The filtered list MUST update as the visitor types, without a full page reload, when
  scripting is available, with no "Filter" button shown. When scripting is not available, a
  "Filter" button MUST be shown and the filters MUST work by form submission.
- **FR-020**: On narrow screens the filters MUST be collapsible behind a toggle labelled with the
  number of active filters (collapsed by default), using no hand-written JavaScript. On wide screens
  they MUST always be visible beside the results. The choice MUST depend only on the screen width,
  never on the browser's identity.
- **FR-018**: Recipe pages MUST display ingredients with optional ingredients, alternatives and
  amounts clearly distinguished, and the method with its paragraph or list structure kept. On wide
  screens the ingredients and method MUST sit side by side; on narrow screens they stack.
- **FR-019**: Content from recipe files MUST be displayed safely: it cannot run scripts or alter the
  site's layout or styling beyond normal text formatting.

### Key Entities

- **Recipe**: a single dish or drink. Has a name, a unique address derived from it, a type, an
  ordered list of ingredient entries and a method. Sourced from one recipe file.
- **Recipe Type**: a category such as drink, breakfast or side, from the recognised set of types.
- **Ingredient Entry**: one line of a recipe's ingredient list. Has one or more alternative
  ingredients (exactly one of which is used), an optional amount, and whether it is optional.
- **Ingredient**: a name on the master ingredient list, shared across recipes; the unit of the
  ingredient filter and of the consistency check.
- **Master Ingredient List**: the hand-maintained list of every recognised ingredient name, kept in
  the repository alongside the recipes.
- **Recipe Collection**: all recipes loaded from the recipe folder, plus the recognised types and
  master ingredient list they are checked against.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The site owner can add a new recipe by writing a single text file, without changing any
  other part of the site, in under 10 minutes using only the documented format.
- **SC-002**: With 500 recipes, the Recipes page and filter results appear in under 1 second.
- **SC-003**: With 500 recipes, the site still starts and validates the collection in under
  5 seconds.
- **SC-004**: 100% of recipes that use an ingredient name not on the master list, unknown type, duplicate name
  or are missing a required part are caught by the automated checks before merge.
- **SC-005**: For any ingredient, filtering by it returns every recipe containing it (including as
  an alternative or an optional ingredient) and no others.
- **SC-006**: A visitor can find a known recipe by name or by ingredient in under 15 seconds.
- **SC-007**: Every recipe page and the filtered list have no automatically detectable accessibility
  violations, in both themes.

## Assumptions

- No database is needed: tens to hundreds of small text files read once at start-up comfortably fit
  in memory, and keeping recipes in the repository gives free history, review and backup.
- Recipes are public: anyone visiting the site can browse them. Recipes are authored only by the site
  owner through the repository; there is no in-site editing, upload, user accounts or comments.
- Recipe changes reach the live site by the normal deploy (merge and redeploy/restart); live
  reloading of recipe files is not required.
- Amounts are free text (e.g. "50 ml", "2 tbsp", "a pinch"), shown as written; no unit conversion or
  serving scaling.
- An amount on an alternative group applies to the group as a whole.
- Ingredient names are plain names from the master list (e.g. "Lime"); quantities and preparation
  notes go in the parenthesised amount (e.g. "Lime (juice of 1)") or the method, so the filter stays
  consistent.
- "Suggester" means the type, name and ingredient filters; a "what can I make with what I have"
  mode is out of scope.
- A recipe has exactly one type.
- Images, nutrition data, servings, timings, ratings and printing layouts are out of scope for this
  feature.
- The Recipes page follows the existing site conventions: linked from the navigation drawer, works
  in both themes and at phone widths, and is covered by the same automated test suite.
