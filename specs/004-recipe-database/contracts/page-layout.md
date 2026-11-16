# Page Layout Contract: Recipes

DOM structure the templates must produce and the tests rely on. The visual reference is the
agreed "Recipes UI mockup" design canvas (<https://claude.ai/artifact/1e7Yuhg4R4t8cfjDSiHQDV>). As
elsewhere on the site, there are no `style` attributes (the CSP forbids inline styles) and no
hand-written scripts.

## Navigation

`content.PAGES` becomes `(HOME, ANASCRAMBLE, RECIPES, ABOUT)`. "Recipes" links to `/recipes`. It
has `aria-current="page"` on both the list page and every recipe page (`current_page = "recipes"`).

## List page (`templates/recipes.html`), `<h1>` "Recipes"

```html
<div class="recipes-layout">                <!-- flex-wrap row: filters beside results when wide -->
  <details class="recipe-filters-panel">    <!-- never rendered with "open" -->
    <summary>Filters <span id="filter-count">· 2 active</span></summary>  <!-- span empty when none -->
    <form id="recipe-filters" class="recipe-filters" method="get" action="/recipes" role="search"
          aria-label="Filter recipes"
          hx-get="/recipes" hx-trigger="submit, input delay:250ms" hx-target="#recipe-results"
          hx-select="#recipe-results" hx-select-oob="#filter-count" hx-swap="outerHTML"
          hx-push-url="true" hx-sync="this:replace">
      <fieldset>
        <legend>Type</legend>
        <!-- one per type in use, vocabulary order -->
        <label><input type="checkbox" name="type" value="drink" [checked]> Drink</label>
      </fieldset>
      <label for="recipe-name">Name</label>
      <input id="recipe-name" name="name" type="search" maxlength="100" autocomplete="off" value="…">
      <label for="recipe-ingredient">Ingredient</label>
      <input id="recipe-ingredient" name="ingredient" type="search" maxlength="100"
             list="ingredient-options" autocomplete="off" value="…">
      <datalist id="ingredient-options"><option value="Cava">…</option></datalist>
      <button type="submit" class="filter-submit">Filter</button>  <!-- hidden when scripting is enabled -->
    </form>
  </details>

  <section id="recipe-results" aria-label="Recipes">
    <div class="results-header">
      <p role="status">3 recipes</p>          <!-- "1 recipe" / "No matching recipes." / "No recipes yet." -->
      <a href="/recipes" class="clear-filters">Clear filters</a>   <!-- only when a filter is active -->
    </div>
    <!-- only when filtered and empty: -->
    <p class="no-results-tip">Try fewer filters, or pick an ingredient from the suggestions as you type.</p>
    <ul class="recipe-list">
      <li>
        <div class="recipe-list-row">
          <a href="/recipes/french-75">French 75</a>
          <span class="recipe-type">Drink</span>
        </div>
        <p class="recipe-summary">Elderflower cordial · Gin · Ice cubes · Lime · Champagne, Prosecco or Cava</p>
      </li>
    </ul>
  </section>
</div>
```

- **Live filtering**: every control change re-requests the page. htmx swaps in `#recipe-results`
  and `#filter-count` only, so focus and the caret stay in the filter controls (research R8, R8a).
- **"Filter" button**: hidden by `@media (scripting: enabled)`. Without JavaScript it is visible
  and submits the form normally.
- **Narrow screens** (below 768 px): the panel sits above the results and starts collapsed. Its
  `summary` is the toggle ("Filters · N active", with a chevron).
- **Wide screens** (768 px and up): the `summary` is hidden and the panel content is forced visible
  (`::details-content`), so the filters are a sidebar beside the results.
- **Form state**: controls are re-filled from `RecipeSearch.query`, so a shared URL shows its
  filters.
- **Empty collection**: `#recipe-results` holds only the status "No recipes yet.".
- **Helper text**: there is none under the ingredient box.

## Recipe page (`templates/recipe.html`), `<h1>` is the recipe name

```html
<article class="recipe">
  <div class="recipe-top">
    <a href="/recipes" class="back-link">All recipes</a>   <!-- preceded by an aria-hidden chevron -->
    <p class="recipe-type">Drink</p>
  </div>
  <div class="recipe-body">                 <!-- flex-wrap row: side by side when wide -->
    <section class="recipe-ingredients" aria-labelledby="ingredients-heading">
      <h2 id="ingredients-heading">Ingredients</h2>
      <ul class="ingredients">
        <li>
          <span class="ingredient-name">Elderflower cordial</span>
          <span class="ingredient-optional">optional</span>
          <span class="ingredient-amount">10 ml</span>
        </li>
        <li><span class="ingredient-name">Champagne, Prosecco or Cava</span></li>
      </ul>
    </section>
    <section class="recipe-method" aria-labelledby="method-heading">
      <h2 id="method-heading">Method</h2>
      <div class="method"><!-- method_html: <ol><li>…</li></ol>, <ul> or <p>… --></div>
    </section>
  </div>
</article>
```

- **Wide screens**: the ingredients card (about 280–360 px) sits left of the method.
- **Narrow screens**: they stack, ingredients first.
- **Method numbering**: `.method ol > li` gets a circled step number from a CSS counter
  (`::before`, `aria-hidden` by nature), replacing the default marker. Screen readers still announce
  a numbered list because the `<ol>` semantics are unchanged.

## Styling and accessibility

- **Colours**: `site.css` styles everything with theme tokens. These new `light-dark()` tokens are
  added beside the existing ones:
  - `--color-muted` (`#5c5c5c` / `#a6a6a6`)
  - `--color-border` (`#d0d4dc` / `#2c3038`)
  - `--color-pill-bg` (`#dbe6ff` / `#1f2a44`)
  - `--color-pill-text` (`#1a3f99` / `#c0e0ff`)

  All text pairs meet WCAG 2.2 AA in both themes.
- **Narrow widths**: no horizontal page scroll at 320 px.
- **Touch targets**: controls are at least 44 px tall, and checkbox rows at least 36 px with the
  whole label clickable.
- **Secondary text**: the amount, "optional" label and ingredient summary are muted but remain
  plain text, read in order by screen readers.
- **axe**: no violations on the list (unfiltered, filtered, no results, collapsed and expanded
  panel) or the recipe page, in both themes.
