# Implementation Plan: Anascramble Page

**Branch**: `rewrite` (spec-kit feature id `003-anascramble-page`) | **Date**: 2026-11-14 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-anascramble-page/spec.md`

## Summary

Add the Anascramble page from `main`: visitors type 3–30 letters, press "Scramble!" to see them
jumbled round a centre point, and type a candidate answer into a solution field that dims the
letters it uses. Same behaviour as main, rebuilt server-side with no hand-written JavaScript.

Technical approach (details in [research.md](research.md)):

- **Domain**: a pure `website.anascramble` module ports main's scrambling algorithm (random angle,
  growing radius, minimum spacing) and the letter-availability rules. All randomness comes from an
  injected `random.Random`, so tests are deterministic.
- **Stateless puzzle**: one POST form carries `letters`, `solution` and hidden `seed`/`arranged`.
  The server rebuilds the current arrangement from the seed on every request. Nothing is stored
  anywhere, and the letters stay out of the URL.
- **Scramble area as SVG**: `<text>` elements positioned by attributes, because the CSP blocks
  inline styles. The server fits the `viewBox` round the letters, so they always stay inside it, and
  the SVG scales to narrow screens on its own.
- **Live feedback with htmx**: `input` events post the form. The response is out-of-band fragments
  that never replace the field being typed in unless its value was corrected, so the caret and
  pending keystrokes survive. `hx-sync` drops stale requests. Without JS, the same form works by
  normal submission.
- **Solution field**: one text input laid over N server-rendered cells (one-time-passcode pattern).
  The browser's own editing provides advance, Backspace and Space-as-blank.
- **Font**: Rock Salt, self-hosted from `@fontsource/rock-salt` with its Apache-2.0 licence, and
  credited.

## Technical Context

**Language/Version**: Python 3.15 (CPython), HTML/Jinja2 templates, CSS, inline SVG

**Primary Dependencies**: FastAPI, Jinja2, Uvicorn, htmx 4.0.1 (existing). New: `python-multipart`
(Apache-2.0, needed by FastAPI for form parsing). New asset: Rock Salt woff2 (Apache-2.0).

**Storage**: N/A (FR-018: nothing stored on the server or in the browser)

**Testing**: pytest, FastAPI `TestClient`, pytest-playwright (Chromium; Firefox-marked tests for
caret behaviour), axe-playwright-python

**Target Platform**: Linux container behind Caddy. Current evergreen Chromium, Firefox and Safari.
`:has()` and inline SVG text are Baseline.

**Project Type**: Server-rendered web application (single project)

**Performance Goals**: Scramble response under 1 s and solution feedback under 0.5 s (SC-002).
Scrambling 30 letters is a few thousand distance checks, well under 1 ms.

**Constraints**:
- No hand-written JavaScript; htmx attributes use JSON values only (no `js:`, no filters), because
  the CSP has no `'unsafe-eval'`.
- CSP unchanged: no inline styles, so no `style=""` attributes in any markup.
- No cookies, browser storage or server-side state; letters not put in URLs.
- Works without JavaScript by normal form submission.
- WCAG 2.2 AA in both themes (dimmed letters exempt, marked inactive).

**Scale/Scope**: 1 domain module, 1 route module change, 2 templates (page + fragments), CSS
additions, 1 font asset, about 5 test modules.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Modern Python toolchain | One new dependency, `python-multipart`, added with `uv add`, locked in `uv.lock`. Well supported (Starlette/FastAPI maintainers), required by FastAPI for forms. | ✅ Pass |
| II. Server-rendered UI, no hand-written JS | Page and fragments are server-rendered. Live updates use the vendored htmx with JSON `hx-vals` only. The solution field relies on native editing, not scripts. Without JS the form submits normally. | ✅ Pass |
| III. Type safety & style | Domain functions and form model fully typed and docstringed. Form data is a Pydantic model. Any `S311` suppression carries a justifying comment (random is not used for security). | ✅ Pass |
| IV. Testing | Unit tests for the domain (seeded `Random`), `TestClient` for routes and fragments, Playwright for live feedback, caret behaviour, no-JS flow, narrow screens, axe in both themes. | ✅ Pass |
| V. Simplicity | Stateless: no sessions, storage or infrastructure. The font is self-hosted. Domain logic is separate from routes and templates. The `viewBox` fitting removes the need for bounds handling in the algorithm. | ✅ Pass |
| VI. Licence & attribution | Rock Salt and python-multipart are Apache-2.0, compatible with AGPL-3.0. The font's `LICENSE` is kept beside it, and a courtesy credit is added to the About page. The cookie statement stays accurate. | ✅ Pass |
| Tech constraints | CSP, Docker and Caddy unchanged. | ✅ Pass |

No violations, so Complexity Tracking is empty.

**Post-design re-check (after Phase 1)**: still passes. The contracts add one POST endpoint with no
side effects, no scripts, no inline styles and no storage. The only new third-party items are the
font (credited) and `python-multipart`.

## Project Structure

### Documentation (this feature)

```text
specs/003-anascramble-page/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── http.md          # GET/POST /anascramble, form fields, full-page vs fragment responses
│   └── page-layout.md   # DOM contract: ids, attributes, SVG, solution field, accessibility
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/website/
├── anascramble.py              # NEW: pure domain (sanitise, scramble, view box, claimed map,
│                               #   Puzzle state)
├── content.py                  # + ANASCRAMBLE page in PAGES (after HOME), + Rock Salt credit
├── routes.py                   # + GET/POST /anascramble, AnascrambleForm (Pydantic)
├── static/
│   ├── css/site.css            # + @font-face, scramble area, dimmed, solution cells, form layout
│   └── fonts/
│       ├── rock-salt-latin-400-normal.woff2   # NEW: vendored from @fontsource/rock-salt 5.3.0
│       └── rock-salt-LICENSE.txt              # NEW: Apache-2.0 licence from the package
└── templates/
    ├── anascramble.html        # NEW: page (extends base, includes the fragments)
    └── anascramble/
        └── _parts.html         # NEW: macros for scramble SVG, state, button, solution row

tests/
├── unit/
│   ├── test_anascramble.py     # NEW: domain rules and seeded scrambling (SC-003)
│   └── test_content.py         # page order, Rock Salt credit
├── integration/
│   ├── test_anascramble.py     # NEW: GET/POST, full page vs OOB fragments, tampering, no cookies
│   ├── test_navigation.py      # drawer link and aria-current for Anascramble
│   └── test_static.py          # font and licence served
└── e2e/
    ├── test_anascramble.py     # NEW: scramble, solution, caret, fast typing, no-JS, 320 px
    └── test_accessibility.py   # + Anascramble in both themes, before/after scramble, dimmed
```

**Structure Decision**: Keep the single-project layout. The domain logic gets its own module
(constitution V). Routes stay in `routes.py`, which remains small. Fragments are Jinja macros so
the full page and the htmx responses render from the same markup.

## Complexity Tracking

No constitution violations to justify.
