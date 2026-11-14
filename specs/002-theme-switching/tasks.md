---

description: "Task list for feature 002: Light and Dark Theme Switching"
---

# Tasks: Light and Dark Theme Switching

**Input**: Design documents from `specs/002-theme-switching/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included. Constitution principle IV requires every feature to ship with tests. Within
each story, write the tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story, in spec order:
- US1, P1: device preference
- US2, P1: manual switch
- US3, P2: switch kept while browsing
- US4, P3: drawer slide

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: The user story this task belongs to (US1 to US4)
- Paths are relative to the repository root (single project, `src/` layout)

**Applies to every task**:
- Follow constitution III: type hints everywhere (`Final[...]` for module constants), Google-style
  docstrings on every public module, class and function, and Ruff and ty clean.
- Write no hand-written JavaScript (constitution II). JavaScript in Playwright `evaluate()` calls
  inside tests is fine.
- Locate elements by role and accessible name first (see
  [contracts/page-layout.md](contracts/page-layout.md)).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test tooling for running selected browser tests in Firefox.

- [X] T001 Register a `firefox` pytest marker in `pyproject.toml` under `[tool.pytest.ini_options].markers`. Use the description `"firefox: browser test that must also pass in Firefox; run with -m firefox --browser firefox"`. Leave `addopts` unchanged, so the default run stays Chromium-only.
- [X] T002 [P] In `.github/workflows/ci.yml`, job `test`:
  - change the browser install step to `uv run playwright install --with-deps chromium firefox`;
  - add a step after "Run tests" named "Run Firefox tests" that runs `uv run pytest -m firefox --browser firefox --junitxml=reports/junit-firefox.xml`;
  - change the test-reporter `path` to `reports/junit*.xml`.

  If the workflow file has a different name, edit whichever file under `.github/workflows/` defines the `test` job.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared test helpers used by every story's browser tests.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Create `tests/e2e/theme_helpers.py` (module docstring, typed) with these helpers:
  - `active_scheme(page: Page) -> str`: returns `getComputedStyle(document.documentElement).colorScheme`, normalised to `"light"` or `"dark"`.
  - `body_background(page: Page) -> str`: returns the computed `background-color` of `body`.
  - `dark_mode_switch(page: Page) -> Locator`: returns `page.get_by_role("switch", name="Dark mode")`.
  - `open_drawer(page: Page) -> None`: clicks the "Menu" button if `#nav-drawer` does not match `:popover-open`.
  - `assert_nothing_stored(page: Page) -> None`: asserts `page.context.cookies() == []`, `localStorage.length === 0` and `sessionStorage.length === 0`.
  - `mark_document(page)` / `is_same_document(page) -> bool`: set a `window` flag and later check it survives, which detects whether a full page load has happened. (Navigation timing entries cannot detect this, because a new document also has exactly one.)
  - `is_drawer_open(page) -> bool`.

  Also add the colour constants `LIGHT_BG = "rgb(255, 255, 255)"` and `DARK_BG = "rgb(18, 20, 23)"`, typed `Final`, matching research R2 (`#fff` / `#121417`).

**Checkpoint**: Helpers importable (`uv run ty check` passes). User stories can begin.

---

## Phase 3: User Story 1 - Site matches the visitor's device preference (Priority: P1) 🎯 MVP

**Goal**: Every page uses the dark theme when the browser reports a dark preference and the light
theme otherwise. It applies from first paint, updates live when the preference changes, and works
without JavaScript.

**Independent Test**: Load every page with `color_scheme` set to `"dark"`, `"light"` and
`"no-preference"`, and check the computed `color-scheme` and body background. Then flip the
preference with `page.emulate_media` and check the page follows without a reload.

### Tests for User Story 1 ⚠️

- [X] T004 [P] [US1] Create `tests/e2e/test_theme.py` (module docstring) with tests for US1. Mark each with `@pytest.mark.firefox`. Create contexts with `browser.new_context(base_url=base_url, color_scheme=...)`.
  - (a) Parametrise over `"/"`, `"/about"` and `"/does-not-exist"` × `color_scheme` in {`"dark"` → dark/`DARK_BG`, `"light"` → light/`LIGHT_BG`, `"no-preference"` → light/`LIGHT_BG`}. Assert `active_scheme` and `body_background` (FR-001, FR-002).
  - (b) Open `/` in light, then `page.emulate_media(color_scheme="dark")`, and assert dark with `is_same_document(page)`. Then emulate light again and assert light (FR-004).
  - (c) Repeat (a) for `/` with `java_script_enabled=False` (FR-005).
  - (d) Load `/` and assert `assert_nothing_stored` (FR-016).
- [X] T005 [P] [US1] In `tests/integration/test_navigation.py` (or `tests/integration/test_theme_markup.py` if clearer), add a `TestClient` test. It asserts every HTML page (`/`, `/about`, 404) contains `<meta name="color-scheme" content="light dark">` in `<head>`, before the stylesheet link.

### Implementation for User Story 1

- [X] T006 [US1] In `src/website/templates/base.html`, add `<meta name="color-scheme" content="light dark">` immediately after the viewport meta (research R1).
- [X] T007 [US1] In `src/website/static/css/site.css`, rewrite the token block in `:root` (research R2):
  - Set `color-scheme: light;`.
  - Turn each colour token into `light-dark(<light>, <dark>)` with exactly these pairs:

    | Token | Light | Dark |
    |---|---|---|
    | `--color-bg` | `#fff` | `#121417` |
    | `--color-text` | `#1a1a1a` | `#e6e6e6` |
    | `--color-link` | `#1a4fbf` | `#a8cfff` |
    | `--color-header-bg` | `rgb(64 128 255)` | `rgb(64 128 255)` |
    | `--color-header-text` | `#fff` | `#fff` |
    | `--color-focus` | `#1a4fbf` | `#a8cfff` |
    | `--color-icon` | `#000` | `#e6e6e6` |
    | `--color-nav-current-bg` | `#1a4fbf` | `#c0e0ff` |
    | `--color-nav-current-text` | `#fff` | `#121417` |
    | `--color-nav-hover-bg` | `#dbe6ff` | `#1f2a44` |

  - Add `@media (prefers-color-scheme: dark) { :root { color-scheme: dark; } }`.
  - Update the token-block comment to explain that `color-scheme` on `:root` picks the theme.
  - Leave non-colour tokens unchanged, and make sure no other rule in the file hard-codes a colour that should be themed. The `rgb(0 0 0 / …)` shadow and backdrop values may stay.
- [X] T008 [US1] Run `uv run pytest tests/e2e/test_theme.py tests/integration` and `uv run pytest -m firefox --browser firefox`, and make T004 and T005 pass. If axe (run in T030) later flags dark-theme contrast, adjust only the dark values in T007 and record the final values in `specs/002-theme-switching/research.md` R2.

**Checkpoint**: Site follows the device preference everywhere. Deployable as the MVP.

---

## Phase 4: User Story 2 - Visitor switches theme manually (Priority: P1)

**Goal**: A "Dark mode" switch in the drawer, between the page links and About, that is On exactly
when dark is shown. Toggling it flips the theme instantly without leaving the page, including with
JavaScript disabled.

**Independent Test**: Under each device preference, open the drawer, toggle "Dark mode", and check
the theme flips, the URL is unchanged, the drawer stays open and the switch state matches the
theme.

**Depends on**: US1 (dark palette and `color-scheme` mechanism).

### Tests for User Story 2 ⚠️

- [X] T009 [P] [US2] Add US2 tests to `tests/e2e/test_theme.py`, each marked `@pytest.mark.firefox`:
  - (a) For `color_scheme` light and dark, on `/`: open the drawer and assert exactly one `dark_mode_switch` is visible, labelled "Dark mode". Assert it is checked iff `active_scheme == "dark"` (FR-007, data-model invariant).
  - (b) Click it. Assert the scheme flipped, the switch state flipped and still matches, `page.url` is unchanged, the drawer is still open, and `is_same_document` (FR-008).
  - (c) Click the label text "Dark mode" (not the input) and assert it toggles (FR-009).
  - (d) Keyboard: focus the switch with Tab from the menu button, press Space, and assert it toggles (FR-009).
  - (e) Repeat (b) with `java_script_enabled=False` (FR-010).
  - (f) Under a dark preference with the switch turned Off, `page.emulate_media(color_scheme="light")`. Assert the light-device switch is now visible, unchecked, and the scheme is light. This documents the FR-004 behaviour.
  - (g) Assert the switch row's bounding box height is ≥ 44 px.
- [X] T010 [P] [US2] Add a `TestClient` test in `tests/integration/test_navigation.py`. For `/`, `/about` and 404, the drawer `<nav id="nav-drawer">` must contain, between the last non-About page link and the About link:
  - an `<li class="theme-item">` with two `<input type="checkbox" role="switch">` elements;
  - ids `dark-mode-light-device` (not `checked`) and `dark-mode-dark-device` (`checked`), each with the `hx-preserve` attribute;
  - each wrapped in a `<label>` whose text is "Dark mode".

  Use `html.parser`-based parsing (stdlib `html.parser` or a regex on a normalised string), with no new dependency.

### Implementation for User Story 2

- [X] T011 [US2] In `src/website/templates/base.html`, render the theme item inside the drawer `<ul>` before the last page's `<li>`. Use `{% if loop.last %}` inside the existing `nav_pages` loop, keeping the About-last convention documented in `src/website/content.py`. Use the markup from [contracts/page-layout.md](contracts/page-layout.md):

  ```html
  <li class="theme-item">
    <label class="theme-switch theme-switch--light-device"><input type="checkbox" role="switch" id="dark-mode-light-device" hx-preserve> Dark mode</label>
    <label class="theme-switch theme-switch--dark-device"><input type="checkbox" role="switch" id="dark-mode-dark-device" checked hx-preserve> Dark mode</label>
  </li>
  ```

  `hx-preserve` is inert until htmx is added in US3; adding it now keeps the markup stable.
- [X] T012 [US2] In `src/website/static/css/site.css`, add the switch rules (research R3):
  - `.theme-switch--dark-device { display: none; }`, plus, inside `@media (prefers-color-scheme: dark)`, `.theme-switch--light-device { display: none; }` and `.theme-switch--dark-device { display: flex; }`. The hidden switch must use `display: none` so it leaves the accessibility tree.
  - `@media not (prefers-color-scheme: dark) { :root:has(#dark-mode-light-device:checked) { color-scheme: dark; } }`
  - `@media (prefers-color-scheme: dark) { :root:has(#dark-mode-dark-device:not(:checked)) { color-scheme: light; } }`
  - Style `.theme-switch` to match the drawer links: same padding, full width, `min-height: var(--menu-button-size)`, `cursor: pointer`, and the hover background `var(--color-nav-hover-bg)`.
  - Use `justify-content: space-between`, with the visible input after the text. Swap the order in the markup if needed, but keep the label wrapping the input.
  - Style the input as a switch using only tokens: `appearance: none`, a track, and a thumb via a background gradient or box-shadow. Use `--color-nav-current-bg` for On, give it a visible `:focus-visible` outline, and make sure it meets 3:1 non-text contrast in both themes.
- [X] T013 [US2] Run `uv run pytest` and `uv run pytest -m firefox --browser firefox`, and make T009 and T010 pass without breaking existing navigation tests in `tests/e2e/test_navigation.py`, `tests/integration/test_navigation.py` and the drawer's About-pinned layout.

**Checkpoint**: US1 + US2 give a working theme switch on every page (resets on each page load).

---

## Phase 5: User Story 3 - Switch lasts while browsing (Priority: P2)

**Goal**: Following site links and using Back/Forward keeps the visitor's manual switch for the
rest of the visit, with no storage. Reload, new tab or no-JS navigation returns to the device
preference. Focus lands on the new page heading.

**Independent Test**: Switch to the theme opposite the device preference, follow a drawer link,
then go Back and Forward. Check the theme, URL, header, tab title, `aria-current`, the focused
heading and that no full page load happened. Then reload and check the device preference returns,
and check nothing is stored.

**Depends on**: US2 (the switches and `hx-preserve` markup).

### Tests for User Story 3 ⚠️

- [X] T014 [P] [US3] Create `tests/e2e/test_boosted_navigation.py` (module docstring) for a light-preference context:
  - (a) Toggle dark, follow the "About" link in the drawer, and wait for `page.wait_for_url("**/about")`. Assert:
    - `active_scheme == "dark"`;
    - the switch is checked;
    - `is_same_document` (in-place);
    - the header `h1` is "About" and the title is `tab_title("About")`;
    - the About link has `aria-current="page"` and Home has none;
    - the drawer is closed;
    - the focused element is the `h1` (`page.evaluate("document.activeElement.tagName") == "H1"`) (FR-011, FR-021).
  - (b) `page.go_back()`: the URL is `/`, the content is the home page, and the scheme is dark. Then `page.go_forward()`: the URL is `/about` and the scheme is dark (FR-013).
  - (c) `page.reload()`: the scheme is light and the switch is unchecked (FR-014).
  - (d) Toggle dark, then open `/about` with `page.goto`. The scheme is light (typed address, FR-014).
  - (e) `java_script_enabled=False`: toggle dark, follow About, and assert a full load (light scheme) on `/about` (FR-015).
  - (f) External links (`target="_blank"`) on `/` are not boosted: clicking GitHub opens a popup page and the original page is still the same document. Use `page.expect_popup()`, then close the popup without waiting for a third-party load (`route` it to an empty 200 response).
  - (g) After (a) and (b), call `assert_nothing_stored(page)` (FR-016, SC-004).
  - (h) Navigate from the 404 page via the "Go to the home page" link with dark toggled, and assert dark is kept.

  Mark (a) to (c) `@pytest.mark.firefox`.
- [X] T015 [P] [US3] In `tests/integration/test_headers.py`:
  - Update the CSP expectation to read `SECURITY_HEADERS` (already imported), and add an explicit test asserting `"script-src 'self'"` is in the CSP and `"unsafe-eval"` and `"unsafe-inline"` are not (research R8).
  - Add a test that HTML responses for `/`, `/about` and 404 include `vary` containing `HX-Request` (contracts/http.md).
  - Keep `test_no_cookies_are_set`, and also run it with the request header `HX-Request: true`.
- [X] T016 [P] [US3] In `tests/integration/test_navigation.py`, add tests:
  - (a) `<body>` has `hx-boost:inherited="transition:true"`.
  - (b) `<head>` contains `<meta name="htmx-config" content='{"includeIndicatorCSS":false}'>` and `<script src="/static/js/htmx.min.js" defer></script>`.
  - (c) Without `HX-Request`, the `<h1>` has neither `autofocus` nor `tabindex`.
  - (d) With header `HX-Request: true`, the `<h1>` has `tabindex="-1"` and `autofocus`, and the response is still a complete document with `<html>`, `<head>` and the drawer (FR-012). Test this for `/`, `/about` and 404.
- [X] T017 [P] [US3] Create `tests/integration/test_static.py` (module docstring). Assert `GET /static/js/htmx.min.js` returns 200 with a `content-type` starting `text/javascript`, and that the body contains `version="4.0.1"` or `'4.0.1'`. Check the actual minified string when writing the test and assert on it.
- [X] T018 [P] [US3] In `tests/unit/test_content.py`, assert `CREDITS` contains a `Credit` with:
  - `work="htmx"`
  - `author="Big Sky Software"`
  - `work_url="https://htmx.org"`
  - `licence="BSD Zero Clause License"`
  - `licence_url="https://opensource.org/license/0bsd"`

### Implementation for User Story 3

- [X] T019 [US3] Vendor htmx 4.0.1 (research R4):
  1. Download the npm tarball from `https://registry.npmjs.org/htmx.org/-/htmx.org-4.0.1.tgz` into a fresh empty temporary directory.
  2. Verify its SHA-512 against the registry integrity value `sha512-oF7JgXhDW9UXCy/k1ZYFUQgzu/rm19ORWPSPNL91vPluB2PB9+MV55tyQdH/w7o2EAbTYUG5SDW1R60mdkdqGg==`, by base64-encoding the SHA-512 digest of the `.tgz`. Stop and report if it does not match.
  3. Extract `package/dist/htmx.min.js` to `src/website/static/js/htmx.min.js`, unmodified.

  Do not use a CDN at runtime. Mark the file in `.gitattributes` as `-diff linguist-vendored` if a `.gitattributes` exists, or create one with that single line for `src/website/static/js/htmx.min.js`.
- [X] T020 [US3] In `src/website/app.py`, change `script-src 'none'` to `script-src 'self'` in `SECURITY_HEADERS["Content-Security-Policy"]`. Change nothing else.
- [X] T021 [US3] In `src/website/templating.py`:
  - Add `is_htmx_request(request: Request) -> bool`, returning `request.headers.get("HX-Request") == "true"`, with a docstring.
  - Add `"is_htmx_request": is_htmx_request(request)` to `site_context`.
  - Add a `render(request: Request, name: str, context: dict[str, object] | None = None, status_code: int = 200) -> HTMLResponse` helper. It calls `templates.TemplateResponse(...)` and appends `HX-Request` to the response's `Vary` header (merging with any existing value), with a Google-style docstring.

  Add unit tests for `is_htmx_request`, covering `"true"`, absent and `"false"`, in `tests/unit/test_templating.py`.
- [X] T022 [US3] Replace `templates.TemplateResponse(...)` with `render(...)` in `src/website/routes.py` (home, about) and in `_handle_http_exception` in `src/website/app.py` (404, `status_code=404`). Remove the now-unused `templates` imports.
- [X] T023 [US3] In `src/website/templates/base.html` (contracts/page-layout.md):
  - add `<meta name="htmx-config" content='{"includeIndicatorCSS":false}'>` and `<script src="{{ url_for('static', path='js/htmx.min.js').path }}" defer></script>` to `<head>`, after the stylesheet link;
  - change `<body>` to `<body hx-boost:inherited="transition:true">`;
  - render the header as `<h1{% if is_htmx_request %} tabindex="-1" autofocus{% endif %}>{{ page_title }}</h1>`.

  The rendered script `src` must equal `/static/js/htmx.min.js`.
- [X] T024 [US3] In `src/website/content.py`, append to `CREDITS`: `Credit(work="htmx", author="Big Sky Software", work_url="https://htmx.org", licence="BSD Zero Clause License", licence_url="https://opensource.org/license/0bsd")`. Confirm the About page renders it via the existing template (constitution VI).
- [X] T025 [US3] Run `uv run pytest` and `uv run pytest -m firefox --browser firefox`, and make T014 to T018 and the T021 unit tests pass. If Back/Forward loses the switch state in either browser, check that both switches have stable ids and `hx-preserve` (research R5). Do not add any htmx extension or `hx-on` attribute.

**Checkpoint**: Theme switch persists across in-place navigation for the visit; nothing stored.

---

## Phase 6: User Story 4 - Drawer slides smoothly in and out (Priority: P3)

**Goal**: The drawer slides in from the left over about 350 ms and out to the left over about 300 ms
however it closes, including when the visitor chooses a page. The backdrop fades with it, and
there is no motion under reduced-motion settings.

**Independent Test**: With motion allowed, check the computed open and close durations, and that
choosing a page runs a view-transition animation on the old drawer. With `reduced_motion="reduce"`,
check no drawer transition or view-transition animation runs.

**Depends on**: US3 for the slide-out on choosing a page (scenario 3). Scenarios 1, 2 and 4 depend
only on the existing drawer.

### Tests for User Story 4 ⚠️

- [X] T026 [P] [US4] Add tests to `tests/e2e/test_drawer_motion.py` (a separate module, for focus), marked `@pytest.mark.firefox` except (c):
  - (a) On `/`, read `getComputedStyle(drawer).transitionDuration` and `transitionTimingFunction` for the `translate` entry while open: expect `0.35s` and `ease-out`. After closing, read them again while the closing transition runs: expect `0.3s` and `ease-in`. Assert the `::backdrop` opacity transition uses the same durations. Read the custom properties `--drawer-open-duration` and `--drawer-close-duration` from `:root` and assert they are `350ms` and `300ms` (FR-023).
  - (b) Open the drawer, then close it with the menu button. During the close, assert `document.getAnimations()` contains a running `CSSTransition` on the drawer for `translate`. Repeat for Escape and an outside click (FR-022).
  - (c) Chromium only: open the drawer and click the About link. Poll `document.getAnimations().some(a => a.effect?.pseudoElement === '::view-transition-old(nav-drawer)')` and assert it becomes true within the transition. When it ends, the URL is `/about` and the drawer is closed (FR-022, FR-024).
  - (d) With `browser.new_context(reduced_motion="reduce")`, open and close the drawer, then follow a link. Assert no `CSSTransition` on the drawer and no `::view-transition-*` animation (FR-025).
  - (e) Rapid toggle: click the menu button twice within 100 ms. After 500 ms, assert the drawer is fully closed (not `:popover-open`), and that its computed `translate` is the off-screen value.

### Implementation for User Story 4

- [X] T027 [US4] In `src/website/static/css/site.css` (research R6), add `--drawer-open-duration: 350ms;` and `--drawer-close-duration: 300ms;` to `:root`. Then rework the reduced-motion `no-preference` block for the drawer:
  - The open state (`.drawer[popover]:popover-open`) uses `transition: translate var(--drawer-open-duration) ease-out, overlay var(--drawer-open-duration) allow-discrete, display var(--drawer-open-duration) allow-discrete`.
  - The closed state (`.drawer[popover]:not(:popover-open)`) uses the same properties with `var(--drawer-close-duration) ease-in`.
  - Keep `@starting-style` for the slide-in.
  - Add a matching `opacity` transition on `.drawer::backdrop`, from 0 when closed or starting to the current value when open, with the same durations and `@starting-style`.
  - Remove the old `0.2s` values.
- [X] T028 [US4] In `src/website/static/css/site.css`, add the view-transition rules:
  - `.drawer { view-transition-name: nav-drawer; }` and `.site-header { view-transition-name: site-header; }`.
  - `@keyframes drawer-slide-out { from { translate: 0 0; } to { translate: -100% 0; } }`.
  - Inside `@media (prefers-reduced-motion: no-preference)`:
    - `::view-transition-old(nav-drawer) { animation: drawer-slide-out var(--drawer-close-duration) ease-in both; }`
    - `::view-transition-new(nav-drawer) { animation: none; }`
    - `::view-transition-group(root), ::view-transition-old(root), ::view-transition-new(root) { animation-duration: 150ms; }`
  - `@media (prefers-reduced-motion: reduce) { ::view-transition-group(*), ::view-transition-old(*), ::view-transition-new(*) { animation: none; } }`.
- [X] T029 [US4] Run `uv run pytest tests/e2e/test_navigation.py` and `uv run pytest -m firefox --browser firefox`, and make T026 pass. Check manually in Firefox (quickstart step 9) that the slide-out on the menu button is visible. If Firefox lacks `overlay` support and the exit is not visible, report it rather than adding JavaScript; the spec accepts this as an edge case.

**Checkpoint**: All four stories complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T030 [P] Extend `tests/e2e/test_accessibility.py` so `test_no_serious_violations` is also parametrised over `color_scheme` in {`"light"`, `"dark"`}, using a context created with that scheme. Also add a case with the switch toggled (light preference + switch On). Fix any contrast failures by adjusting dark token values only (FR-017, FR-020, SC-005).
- [X] T031 [P] Update `README.md`:
  - Under "Prerequisites" or "Quality checks", note that Firefox is also installed for Playwright (`uv run playwright install --with-deps chromium firefox`) and how to run `uv run pytest -m firefox --browser firefox`.
  - Add a "Vendored htmx" subsection with the update procedure from research R4: download the tarball, verify integrity against the registry, replace `src/website/static/js/htmx.min.js`, and update the version in `tests/integration/test_static.py` and research.md. Explain that Dependabot cannot update it.
- [X] T032 [P] Update `specs/001-home-page-and-ci/contracts/page-layout.md`: add one line under "Common layout" pointing to `specs/002-theme-switching/contracts/page-layout.md` for the theme switch, htmx attributes and focus changes. Update the CSP line in `specs/001-home-page-and-ci/contracts/http-routes.md` to `script-src 'self'`, if it lists the CSP.
- [X] T033 Run the full quality gates from the constitution and fix any failures:
  - `uv lock --check`
  - `uv run ruff format --check`
  - `uv run ruff check`
  - `uv run ty check`
  - `uv run pytest`
  - `uv run pytest -m firefox --browser firefox`
  - the Docker build (`docker build -f build/Dockerfile .`)

  Make sure the Docker image includes `static/js/htmx.min.js`; the static directory is already copied with the package.
- [ ] T034 Walk through [quickstart.md](quickstart.md) manual scenarios 1 to 13 in Firefox and Chromium against `uv run website`. Record any deviation as a note under that scenario in quickstart.md, and fix it or raise it with the user.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: none.
- **Foundational (Phase 2)**: depends on Setup (T001 marker). Blocks all stories.
- **US1 (Phase 3)**: depends on Foundational.
- **US2 (Phase 4)**: depends on US1 (T007 tokens and the `color-scheme` mechanism).
- **US3 (Phase 5)**: depends on US2 (T011 switch markup with ids and `hx-preserve`).
- **US4 (Phase 6)**: T026(a,b,d,e), T027 and T028 depend only on Foundational, so they can be done any time after Phase 2. T026(c) depends on US3 (boosted navigation with view transitions).
- **Polish (Phase 7)**: after all stories.

### Within Each User Story

- Write the tests first and see them fail, then implement, then run the verification task.
- Templates and CSS in the same story touch shared files (`base.html`, `site.css`), so do them
  sequentially.

### Parallel Opportunities

- T001 and T002 (different files).
- Within each story, all test tasks marked [P] (different test files).
- US3: T019 (vendor), T020 (CSP), T021 (templating) and T024 (credit) touch different files and
  can run in parallel after the tests. T022 and T023 follow T021.
- US4's CSS tasks (T027 and T028) can be developed alongside US2 or US3 by a second person, but
  they edit `site.css`, so coordinate the merges.
- Polish: T030, T031 and T032 are independent.

---

## Parallel Example: User Story 3

```text
# Tests together:
T014 tests/e2e/test_boosted_navigation.py
T015 tests/integration/test_headers.py
T016 tests/integration/test_navigation.py
T017 tests/integration/test_static.py
T018 tests/unit/test_content.py

# Then implementation in parallel:
T019 src/website/static/js/htmx.min.js
T020 src/website/app.py (CSP)
T021 src/website/templating.py
T024 src/website/content.py
# then T022 (routes.py, app.py handler) and T023 (base.html)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2.
2. Phase 3 (US1): the site follows the device preference.
3. **Stop and validate**: quickstart steps 1 to 3 and 11. Deployable on its own.

### Incremental Delivery

1. US1, the device-preference theme: MVP.
2. + US2: manual switch (resets per page load).
3. + US3: switch persists across in-place navigation; htmx introduced.
4. + US4: smoother drawer, including slide-out on navigation.
5. Polish: accessibility in both themes, docs, full gates.

Each increment passes all quality gates before moving on.

---

## Notes

- [P] = different files, no dependencies on incomplete tasks.
- Commit after each task or logical group, using Conventional Commits (e.g.
  `feat(theme): follow device colour preference`).
- Never add an htmx extension, `hx-on` or inline script. If something seems to need JavaScript,
  stop and raise it with the user (constitution II).
- Implementation note (2026-11-14): Playwright's Firefox cannot start on the development machine
  (Windows reports a missing `mozglue` side-by-side assembly), so the `firefox`-marked tests and
  the Firefox halves of T008, T013, T025, T029 and T034 were not run locally. They run in CI, which
  installs Firefox (T002). T034, the manual walk-through, is left for the owner.
