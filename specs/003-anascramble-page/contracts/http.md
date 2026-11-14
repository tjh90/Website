# HTTP Contract: Anascramble

Existing site-wide behaviour (security headers, `Vary: HX-Request` from `render()`, no cookies,
404 page) applies unchanged.

## `GET /anascramble` (also `HEAD`)

- Route name `anascramble`. 200, `text/html`, full page (extends `base.html`).
- Empty puzzle: letters field empty, "Scramble!" disabled, no solution row, empty scramble area.
- Query parameters are ignored.
- With `HX-Request: true` (boosted navigation), the same page with the `<h1>` autofocus markup the
  site already uses.

## `POST /anascramble`

Body: `application/x-www-form-urlencoded` (or `multipart/form-data`) with the fields in
[data-model.md](../data-model.md#anascrambleform-pydantic-request-body). Never returns 4xx for
malformed or tampered field values: they are sanitised.

### Without `HX-Request` (no-JS submission)

- 200, full page, rendered from the resulting `Puzzle`.
- Letters, solution (corrected) and hidden state are filled in, so the visitor can carry on.

### With `HX-Request: true`

- 200, `text/html`, body is **only** out-of-band fragments; the form uses `hx-swap="none"`.
- Each fragment is a single element with an `id` and `hx-swap-oob="true"` (outer swap by id).

| Fragment `id` | Included when | Content |
|---|---|---|
| `scramble` | always | The scramble SVG (empty `<svg>` when no arrangement) |
| `puzzle-state` | always | Hidden `seed` and `arranged` inputs |
| `scramble-button` | always | The button with the correct `disabled` state |
| `solution-row` | `intent != "solution"` | Whole row: label, cells and input (reset or kept per data model), `hidden` when fewer than 3 letters |
| `solution` | `intent == "solution"` and `solution_corrected` | The solution input alone, with the corrected value |
| `letters` | `letters_corrected` | The letters input with the corrected value |

Rule: the field the visitor is typing in is only replaced when the server changed its value. For
`intent=letters` the visitor is in the letters field, so replacing the whole solution row is safe.
For `intent=scramble` the solution input is replaced with its own value; htmx restores focus and
selection by `id` if it was focused (Enter pressed in the solution field).

### Request/response examples (htmx)

| Request | Response fragments |
|---|---|
| `intent=letters`, `letters=lette` | `scramble` (empty), `puzzle-state` (empty), `scramble-button` (enabled), `solution-row` (5 cells, empty input with `maxlength=5`) |
| `intent=letters`, `letters=le7` | as above for `LE` (button disabled, row `hidden`), plus `letters` with value `LE` |
| `intent=scramble`, `letters=letter` | new `scramble` (6 letters), `puzzle-state` (new seed, `arranged=LETTER`), `scramble-button`, `solution-row` (solution kept) |
| `intent=solution`, `solution=TTT`, valid seed | `scramble` (two T dimmed, same positions), `puzzle-state`, `scramble-button`, `solution` with `TT` |
| `intent=solution`, `solution=T E`, valid seed | `scramble` (T and E dimmed), `puzzle-state`, `scramble-button`; no `solution` fragment |

## Caching

`Cache-Control: no-store` on POST responses (they reflect submitted input and must not be reused).
GET keeps the site default.
