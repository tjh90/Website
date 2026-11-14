# Research: Anascramble Page

All Technical Context unknowns are resolved below. Sources: main branch Java implementation
(`CharacterScrambler`, `AnascrambleViewModel`), the vendored htmx 4.0.1 file (inspected directly),
the npm registry and the site's existing CSP (`src/website/app.py`).

## R1. Solution-row keyboard behaviour under the CSP

- **Decision**: One `<input type="text">` drawn as a row of N letter cells (one-time-passcode
  pattern). The browser's own editing gives auto-advance, Backspace and Space (blank). The page never
  moves focus.
- **Rationale**:
  - Key-specific htmx triggers (`keydown[key=='Backspace']`) are evaluated with `Function(...)` in
    htmx 4.0.1. The site's CSP has no `'unsafe-eval'`, so they cannot run. Without them, Backspace in
    an empty box cannot be detected (it causes no `input` event).
  - Focus moved by server round trips races fast typing: the second key lands in the old box before
    the response arrives, which breaks FR-015.
  - A single field needs no focus logic, no JS and no per-box state, and gives one labelled control
    to assistive technology.
- **Alternatives considered**: per-box server-driven focus (blocked, as above); Tab-only boxes
  (slower, loses reference behaviour); ~20 lines of hand-written JS (constitution exception, user
  declined); `'unsafe-eval'` in the CSP (weakens XSS protection, still racy). The user chose the
  single field on 2026-11-14.

## R2. Scramble area rendering

- **Decision**: Render the scramble area as inline SVG. Each character is a `<text>` element with
  `x`/`y` attributes. The `viewBox` is computed by the server to enclose every character plus a
  margin, never smaller than 400 × 400 units and always square and centred on the origin. The SVG is
  `width: 100%; max-width: 400px; aspect-ratio: 1`.
- **Rationale**:
  - The CSP is `style-src 'self'`, which blocks `style=""` attributes. Main positioned letters with
    inline `left`/`top` styles, which would be blocked here. SVG geometry attributes are not styles.
  - Fitting the `viewBox` to the letters guarantees FR-006 (all inside the area) for any length: long
    inputs just scale down. No rejection-sampling failure mode exists.
  - SVG scales with its width, so FR-007 (shrink on narrow screens) needs no extra code. Font size
    scales with it.
  - Dimming is a class (`dimmed`) styled in `site.css`, so it themes with `light-dark()` tokens.
- **Alternatives considered**: absolutely positioned elements with inline styles (blocked by CSP);
  a CSP nonce or hash for styles (complexity, per-response nonces); generated CSS classes per
  position (unbounded); `<canvas>` (needs JS).

## R3. Scrambling algorithm

- **Decision**: Port main's algorithm to a pure Python module: for each character, pick a random
  angle at the current radius; if the point is within the minimum distance of an earlier one, retry,
  growing the radius by a fixed step every 10 tries. Positions are relative to the origin. Then the
  `viewBox` is fitted (R2). Constants: start radius 50, step 5, minimum distance 50 units (matches
  main's 32 px font in a 400 px area).
- **Rationale**: Same visual result as main (letters cluster round the centre, spreading for longer
  inputs). Termination is guaranteed because the radius keeps growing.
- **Randomness**: functions take a `random.Random` instance (constitution IV: injectable seeds). The
  route creates `random.Random(seed)`. The seed is a 63-bit value from `secrets.randbits`. `random`
  is not used for security, so Ruff `S311` is suppressed with a justifying comment where needed.
- **Shuffled reading order** (FR-019): after placing, the list of placed characters is shuffled with
  the same `Random` before rendering. Each item keeps its source index, so dimming is unaffected.
  One extra line.

## R4. Keeping state without storage

- **Decision**: The page is a single `<form method="post" action="/anascramble">`. State travels in
  the form: `letters`, `solution`, and hidden `seed` and `arranged` (the letters the current
  arrangement was made from). The server regenerates the arrangement from `(arranged, seed)` on
  every request. Nothing is stored server-side or in the browser.
- **Rationale**:
  - Dimming after a solution edit must apply to the arrangement currently shown. Regenerating it
    from the seed is deterministic and stateless.
  - `arranged` lets one rule cover both JS and no-JS flows: if `letters != arranged`, there is no
    current arrangement, and the solution is reset (FR-009, FR-013).
  - POST keeps the letters out of the URL and browser history (FR-018). The endpoint has no side
    effects, so CSRF is not a concern, and `form-action 'self'` already allows it.
- **Tampering** (FR-016): every field is re-validated. Bad `seed` values (non-integer, out of range)
  are treated as "no arrangement". Over-long or disallowed input is sanitised, never rejected with an
  error page. Tampering only affects the tamperer's own page.
- **Alternatives considered**: server sessions (needs storage and cookies, against FR-018); GET
  with query parameters (letters stored in browser history); returning only class changes and
  keeping positions client-side (needs JS).

## R5. htmx interaction design

- **Decision**:
  - The form has `hx-post="/anascramble" hx-swap="none" hx-sync="this:replace"`. Responses to htmx
    requests contain only out-of-band fragments (`hx-swap-oob`), each replacing an element by `id`.
  - Each text field adds `hx-trigger="input"` and an intent via JSON `hx-vals` (no `js:` values, so
    no eval): `{"intent":"letters"}` or `{"intent":"solution"}`. The "Scramble!" button is
    `name="intent" value="scramble"`, so a plain submission (with or without JS, including Enter)
    sends `intent=scramble`.
  - Fragments in every response: the scramble SVG, the hidden state inputs, the button (for its
    enabled state), and the solution cells. The solution input is included when the intent is not
    `solution` (it must be reset) or when its value was corrected. The letters input is included
    only when its value was corrected.
- **Rationale**:
  - Never swapping the field being typed in (unless the server changed its value) keeps the caret
    and any keys typed while the request was pending (FR-015).
  - When a correction is needed, htmx 4 restores focus and selection on the element with the same
    `id` after a swap (inspected: the swap task re-focuses `document.getElementById(id)` and calls
    `setSelectionRange(start, end)`). The Playwright tests verify the caret survives a refusal.
  - `hx-sync="this:replace"` aborts an in-flight request when a newer one starts, so a stale
    response cannot overwrite a newer one.
  - Residual race: if a correction response arrives after the visitor typed more, those later keys
    are overwritten. This only happens straight after a refused key, and the next `input` event
    corrects the state. Accepted as within FR-015's intent (accepted characters are not lost:
    the next request re-sends them).
- **Alternatives considered**: swapping the whole form (loses caret and pending keys); a delay on
  `input` (slower feedback, SC-002); reading htmx's `HX-Source` header instead of `intent` (couples
  the server to element ids).

## R6. Input restrictions without JavaScript

- **Decision**: `maxlength` (30 for letters, N for solution) is enforced natively. Disallowed
  characters are removed by the server on each `input` request (corrected value swapped back, R5).
  The letters field also has `pattern="[A-Za-z]{3,30}"`, `minlength="3"`, `required` and
  `autocomplete="off"`, `autocapitalize="characters"`, `spellcheck="false"`, so native validation
  covers no-JS submission. The solution field gets the same `autocomplete`, `autocapitalize` and
  `spellcheck` attributes, with `pattern="[A-Za-z ]*"`.
- **Rationale**: HTML cannot block typing a character, which is what main's Vaadin
  `allowedCharPattern` did with JS. Server correction keeps the observable behaviour (the character
  disappears) within SC-002's 0.5 s.
- **"Scramble!" enabled state**: rendered disabled when fewer than 3 valid letters; updated by the
  button fragment on every letters `input`. Without JS, the button is enabled and native
  `minlength`/`pattern` validation blocks short submissions; the server also refuses to scramble
  fewer than 3 letters.

## R7. Solution field appearance

- **Decision**: A grid stacks the input on top of a row of N empty cell `<span>`s (rendered by the
  server, `aria-hidden="true"`). The input is transparent, in a monospace font, with
  `letter-spacing` and padding set so each character sits centred in a cell. Cell width is a CSS
  custom property defined in `site.css`, reduced at 11+ and 21+ letters using
  `:has(> :nth-child(n))` selectors, with a floor of about 1.25 rem. Below the floor the row scrolls
  sideways inside its own container (`overflow-x: auto`).
- **Rationale**: No inline styles (CSP). Cells count comes from the markup, so CSS can size them.
  The input stays a real text field for editing, autofill suppression and assistive technology.
- **Alternatives considered**: `background-image` stripes on the input (do not scroll with the text;
  width needs N in CSS); `field-sizing: content` (no Firefox support); CSS `attr()` with types
  (Chromium only).

## R8. Handwritten font

- **Decision**: Rock Salt (as on main), self-hosted from `@fontsource/rock-salt` 5.3.0
  (`files/rock-salt-latin-400-normal.woff2`), served from `static/fonts/` with an `@font-face` rule
  using `font-display: swap`. The package's `LICENSE` (Apache-2.0) is kept next to the font file.
- **Licence**: Apache-2.0, compatible with AGPL-3.0 (via GPLv3 compatibility). It does not require
  visible attribution, but a courtesy credit is added to `CREDITS` (Rock Salt, Sideshow, Apache
  License 2.0), consistent with the htmx credit.
- **Rationale**: Constitution V requires self-hosted assets; main used the Google Fonts CDN. Latin
  subset only: input is A–Z.
- **Alternatives considered**: Google Fonts CDN (constitution V, privacy); a system cursive font
  (inconsistent look across platforms).

## R9. Form parsing

- **Decision**: Add `python-multipart` (Apache-2.0, maintained by the Starlette/FastAPI
  maintainers) and parse the form with a Pydantic model via `Annotated[AnascrambleForm, Form()]`.
- **Rationale**: FastAPI requires `python-multipart` for any `Form()` parameter. Constitution III
  requires Pydantic models for request data. Every field is optional with lenient types, and
  sanitising happens in the domain layer, so tampered input never produces a 422 (FR-016).
- **Alternatives considered**: parsing `await request.form()` manually (untyped dicts, still needs
  python-multipart).

## R10. Testing approach

- **Unit** (`tests/unit/test_anascramble.py`): sanitising, claimed-letter map with repeats,
  determinism from a seed, no overlaps and all inside the `viewBox` over many seeded runs (SC-003),
  shuffle changes order but keeps the multiset.
- **Integration** (`TestClient`): GET renders the empty form; POST with each intent returns a full
  page without `HX-Request` and only OOB fragments with it; tampered input is handled; no cookies;
  navigation link and `aria-current`; font and licence served; credit present.
- **E2E** (Playwright): scramble flow, button enabling, digits refused, solution acceptance and
  refusal with dimming, caret kept after a refusal, fast typing, reset on letters change, no-JS form
  flow, narrow viewport (320 px, no page scroll), axe in both themes before and after scrambling with
  dimmed letters.
