# Implementation Plan: Light and Dark Theme Switching

**Branch**: `rewrite` (spec-kit feature id `002-theme-switching`) | **Date**: 2026-11-14 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-theme-switching/spec.md`

## Summary

Add a dark theme that follows the visitor's device preference by default, a "Dark mode" switch in
the navigation drawer, in-place page navigation that keeps a manual switch for the rest of the
visit, and a drawer that slides out to the left whenever it closes. Nothing is stored in the
browser.

Technical approach (details in [research.md](research.md)):

- **Theme**: every colour token becomes a CSS `light-dark()` pair. The `color-scheme` property on
  the root element picks which half applies. It defaults to the device preference via
  `prefers-color-scheme`, which also themes scrollbars and form controls.
- **Switch, pure CSS**: the drawer holds two "Dark mode" switches (checkbox, `role="switch"`), one
  for each device preference, and CSS shows only the matching one. The one shown to dark-preference
  visitors starts checked, so the switch is On exactly when dark is shown. A `:root:has(...)` rule
  flips `color-scheme` when the visible switch differs from its default. This needs no JavaScript.
- **Keeping the switch while browsing**: vendored **htmx 4.0.1**, with `hx-boost` on `<body>`.
  Internal links swap the new page's `<body>` content in place and push the URL. Both switches carry
  `hx-preserve`, so the existing elements and their checked state survive the swap and htmx 4's
  server-fetched history restores. htmx 4 has no localStorage or sessionStorage history cache, so
  nothing is stored.
- **Drawer slide-out on navigation**: boosted swaps run inside a View Transition
  (`hx-boost:inherited="transition:true"`). The drawer gets `view-transition-name: nav-drawer`, and
  its old snapshot is animated off to the left. The existing popover CSS transitions keep handling
  open, close, Escape and light-dismiss. Reduced motion disables both.
- **Focus after in-place navigation**: when a request comes from htmx (`HX-Request` header), the
  server renders the page `<h1>` with `tabindex="-1" autofocus`. htmx then focuses it, so screen
  readers announce the new page.

## Technical Context

**Language/Version**: Python 3.15 (CPython), HTML/Jinja2 templates, CSS

**Primary Dependencies**: FastAPI, Jinja2, Uvicorn (existing). New: htmx 4.0.1, vendored as a
static file (BSD-0-Clause, 37 KB minified, 13 KB gzipped).

**Storage**: N/A (the feature MUST NOT store anything, per FR-016)

**Testing**: pytest, FastAPI `TestClient`, pytest-playwright (Chromium), axe-playwright-python

**Target Platform**: Linux container behind Caddy. Browsers: current evergreen Chromium, Firefox,
Safari. `light-dark()`, `:has()`, popover and View Transitions are Baseline in all three.

**Project Type**: Server-rendered web application (single project)

**Performance Goals**: Theme switch under 100 ms (CSS only, effectively instant). In-place
navigation within the existing 1-second page load budget (SC-007). Drawer opens over ~350 ms and closes over ~300 ms.

**Constraints**:
- No hand-written JavaScript.
- No cookies or browser storage.
- Works without JavaScript (theme and switch fully, navigation as full page loads).
- CSP stays strict apart from `script-src 'self'`.
- WCAG 2.2 AA in both themes.

**Scale/Scope**: 3 templates (base, plus the existing pages unchanged in content), 1 stylesheet,
1 vendored script, about 6 test modules touched.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Modern Python toolchain | No new Python dependencies; uv/FastAPI/Jinja2 unchanged | ✅ Pass |
| II. Server-rendered UI, no hand-written JS | Pages stay server-rendered. In-place navigation uses HTMX, vendored and version-pinned, added now because this feature needs it. The theme switch uses a native checkbox and CSS only. No hand-written JS: htmx config is a JSON `<meta>` tag. Without JS, pages are fully usable and links are plain links. | ✅ Pass |
| III. Type safety & style | New Python (HTMX request detection, credit entry) is typed, docstringed, Ruff/ty clean | ✅ Pass |
| IV. Testing | Unit (content), `TestClient` (headers, HTMX-aware rendering, markup), Playwright (themes, switch, boosted nav, history, no-JS, drawer animation, reduced motion), axe in both themes | ✅ Pass |
| V. Simplicity | Self-hosted script; no new infrastructure; theme logic is a handful of CSS rules; domain logic (credits, pages) stays separate from templates | ✅ Pass |
| VI. Licence & attribution | htmx is BSD-0-Clause, AGPL-compatible. 0BSD needs no attribution, but a courtesy credit is added. The minified file has no licence header to keep. About cookie statement stays accurate (still no cookies). | ✅ Pass |
| Tech constraints | CSP `script-src` changes from `'none'` to `'self'`; no `unsafe-eval`/`unsafe-inline` needed (htmx eval only for `hx-on`/filters, unused; indicator CSS uses constructable stylesheets and is disabled anyway) | ✅ Pass |

No violations, so Complexity Tracking is empty.

**Post-design re-check (after Phase 1)**: still passes. The design adds no JS of our own, no
storage and no infrastructure. The only new third-party asset is htmx, which is credited.

## Project Structure

### Documentation (this feature)

```text
specs/002-theme-switching/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── page-layout.md   # Changes to the 001 DOM contract (switches, htmx attributes, focus)
│   └── http.md          # Header and request-variant changes
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/website/
├── app.py                      # CSP: script-src 'self'
├── content.py                  # + htmx credit
├── templating.py               # + is_htmx_request in shared context; render() helper adds
│                               #   Vary: HX-Request
├── routes.py                   # pages rendered via render()
├── app.py (404 handler)        # 404 page rendered via render()
├── static/
│   ├── css/site.css            # light-dark() tokens, color-scheme rules, switch, view transitions
│   └── js/htmx.min.js          # NEW: vendored htmx 4.0.1
└── templates/
    ├── base.html               # color-scheme meta, htmx meta config + script, hx-boost,
    │                           # Dark mode switches in drawer, h1 autofocus on HTMX requests
    └── not_found.html          # (inherits base; unchanged)

tests/
├── unit/test_content.py        # htmx credit present
├── integration/
│   ├── test_headers.py         # CSP script-src 'self', Vary: HX-Request, still no cookies
│   ├── test_navigation.py      # switches in drawer, hx-boost/hx-preserve markup, h1 autofocus
│   └── test_static.py          # NEW: htmx served from /static with JS content type
└── e2e/
    ├── test_theme.py           # NEW: device preference, live change, switch, no-JS, no storage
    ├── test_boosted_navigation.py  # NEW: theme kept across links and Back/Forward, reload resets,
    │                           # header/title/aria-current update, focus on h1
    ├── test_navigation.py      # drawer slide timings (incl. after choosing a page), reduced
    │                           # motion; animation tests also run in Firefox
    └── test_accessibility.py   # axe in light and dark, drawer open and closed
```

**Structure Decision**: Keep the existing single-project layout from feature 001. All changes are
in the shared layout, stylesheet and a new vendored static file; no new modules beyond tests.

## Complexity Tracking

No constitution violations to justify.
