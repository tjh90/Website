# Page Layout Contract: Anascramble

Extends the site layout contract from features 001/002 (header, drawer, `<main id="content">`).
Tests rely on the ids, roles and attributes below. No element may carry a `style` attribute (CSP
`style-src 'self'`).

## Navigation

- `PAGES` order: Home, Anascramble, About. The drawer link reads "Anascramble", `href="/anascramble"`,
  with `aria-current="page"` on this page.
- Page title (header `<h1>`): "Anascramble". Tab title: "Anascramble · Tim's Page".

## Page structure (inside `<main id="content">`)

```html
<form id="anascramble" class="anascramble" method="post" action="/anascramble"
      hx-post="/anascramble" hx-swap="none" hx-sync="this:replace">

  <svg id="scramble" class="scramble" viewBox="-200 -200 400 400"
       role="group" aria-label="Scrambled letters">
    <!-- one per letter, in shuffled order -->
    <text x="12.3" y="-40.1" class="scramble-letter">E</text>
    <text x="..." y="..." class="scramble-letter dimmed" aria-disabled="true">T</text>
  </svg>

  <div id="solution-row" class="solution-row" [hidden]>
    <label for="solution">Solution:</label>
    <div class="solution-field">
      <div id="solution-cells" class="solution-cells" aria-hidden="true">
        <span></span> ... one per letter
      </div>
      <input id="solution" name="solution" type="text" maxlength="N" pattern="[A-Za-z ]*"
             autocomplete="off" autocapitalize="characters" spellcheck="false"
             hx-trigger="input" hx-vals='{"intent":"solution"}' value="...">
    </div>
  </div>

  <label for="letters">Letters to scramble</label>
  <input id="letters" name="letters" type="text" maxlength="30" minlength="3"
         pattern="[A-Za-z]{3,30}" required autocomplete="off" autocapitalize="characters"
         spellcheck="false" hx-trigger="input" hx-vals='{"intent":"letters"}' value="...">

  <div id="puzzle-state">
    <input type="hidden" name="seed" value="...">
    <input type="hidden" name="arranged" value="...">
  </div>

  <button id="scramble-button" type="submit" name="intent" value="scramble"
          class="primary" [disabled]>Scramble!</button>
</form>
```

## Rules

- **Order** (FR-003): scramble area, solution row, letters field, button, all centred in one column.
- **Scramble SVG** (FR-005–FR-007, FR-019):
  - `viewBox` from `view_box()`; `width: 100%`, `max-width: 400px`, `aspect-ratio: 1` in CSS.
  - `<text>` uses `text-anchor="middle"` and `dominant-baseline="central"` so `(x, y)` is the glyph
    centre. Font: Rock Salt, about 32 user units, colour from a `light-dark()` accent token.
  - Text elements appear in the shuffled order from `scramble()`.
  - Dimmed letters: class `dimmed` (opacity ≈ 0.25) and `aria-disabled="true"`, so they are
    marked inactive for the contrast exemption (FR-012, FR-020).
  - Empty arrangement: the `<svg>` is still rendered (keeps layout stable) with no children and
    `aria-hidden="true"`.
- **Solution row** (FR-010, FR-011, FR-015):
  - `hidden` attribute when fewer than 3 letters; no solution input value in that case.
  - Cells and input are stacked in the same grid area; input background transparent, monospace,
    `letter-spacing` and padding aligned to the cell width token.
  - Cell width token reduced at 11+ and 21+ cells via `.solution-cells:has(> :nth-child(11))` etc.;
    `.solution-field` has `overflow-x: auto` as the last resort (no page scroll at 320 px).
  - No script or attribute moves focus; htmx never targets `#solution` unless its value was
    corrected.
- **Button**: `disabled` when fewer than 3 valid letters. Without JS it is rendered enabled once the
  page has 3+ letters, and native validation guards the empty case. Primary styling uses the
  existing accent tokens in both themes; touch target at least 44 × 44 CSS px, as for other
  controls.
- **Labels**: visible text labels for both fields; the SVG has an accessible name.
- **Focus after in-place navigation**: unchanged (the `<h1>` autofocus rule from feature 002).

## Assets

- `/static/fonts/rock-salt-latin-400-normal.woff2` (`font/woff2`)
- `/static/fonts/rock-salt-LICENSE.txt` (`text/plain`)
- `@font-face { font-family: "Rock Salt"; font-display: swap; src: url(../fonts/...) format("woff2"); }`
