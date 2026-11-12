---

description: "Task list for feature 001: Home Page, Navigation, About Page and CI"
---

# Tasks: Home Page, Navigation, About Page and CI

**Input**: Design documents from `specs/001-home-page-and-ci/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Included. Constitution principle IV requires every feature to ship with tests. Within
each story, write the tests first and confirm they fail before implementing.

**Organization**: Tasks are grouped by user story (US1–US4 from spec.md, all P1, in spec order).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: The user story this task belongs to (US1–US4)
- Paths are relative to the repository root (single project, `src/` layout)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Set up the uv project with its tooling.

- [X] T001 Run `git status --short` and confirm the working tree has no untracked files outside `specs/` (the earlier Rust leftovers have already been removed). If any unexpected untracked files exist, list them and ask the user before touching them.
- [X] T002 Initialise the uv package project at the repo root: run `uv init --package --name website --python 3.14` (or write the equivalent by hand), giving `pyproject.toml` (`requires-python = ">=3.14"`, `[build-system]` using `uv_build`), `.python-version` (`3.14`) and `src/website/__init__.py` with a module docstring. Remove any sample `main()` or `[project.scripts]` that `uv init` adds.
- [X] T003 Add runtime dependencies with `uv add "fastapi[standard]" jinja2 pydantic-settings`, and dev dependencies with `uv add --dev ruff ty pytest pytest-playwright axe-playwright-python`. Commit the resulting `uv.lock`; `pyproject.toml` is updated by uv. Then, as constitution VI requires when adding dependencies, list the licence of every resolved runtime package (`uvx pip-licenses --python .venv/Scripts/python.exe` on Windows or `--python .venv/bin/python` elsewhere, with `--packages` limited to the runtime dependency tree from `uv tree --no-dev`). Confirm each licence is compatible with AGPL-3.0, and stop and report any that isn't.
- [X] T004 Configure Ruff in `pyproject.toml` per research R11: under `[tool.ruff]`, set `target-version = "py314"` and `line-length = 100`. Under `[tool.ruff.lint]`, set `select = ["E","W","F","I","N","D","UP","B","SIM","ANN","RUF","S","PT","PTH"]`. Under `[tool.ruff.lint.pydocstyle]`, set `convention = "google"`. Under `[tool.ruff.lint.per-file-ignores]`, set `"tests/**" = ["S101"]`.
- [X] T005 [P] Configure ty in `pyproject.toml` (`[tool.ty]`) so `uv run ty check` checks `src` and `tests`, with the default (error) rule levels.
- [X] T006 [P] Configure pytest in `pyproject.toml` (`[tool.pytest.ini_options]`): `testpaths = ["tests"]`, `addopts = "--strict-markers -m 'not external'"`, and `markers = ["external: hits real third-party URLs; run with -m external"]`. Also set pytest-playwright's default browser to Chromium (`--browser chromium` in `addopts`).
- [X] T007 [P] Update `.gitignore` to ignore `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `reports/`, `test-results/` and `build/.env`. Remove any obsolete Rust-specific entries (e.g. `target/`).
- [X] T008 [P] Create `.pre-commit-config.yaml` with the official `astral-sh/ruff-pre-commit` hooks (`ruff-check --fix`, `ruff-format`) and a `local` hook that runs `uv run ty check` (`language: system`, `pass_filenames: false`).
- [X] T009 Create the package skeleton with docstring-only modules: `src/website/app.py`, `src/website/config.py`, `src/website/content.py`, `src/website/routes.py`, `src/website/templating.py`, plus the directories `src/website/templates/icons/`, `src/website/static/css/` and `src/website/static/img/`. Create `tests/__init__.py` (empty), `tests/unit/`, `tests/integration/` and `tests/e2e/` (each with an empty `__init__.py`). Check that `uv run ruff check`, `uv run ruff format --check` and `uv run ty check` pass.

  **Applies to every later task**: constitution III requires type hints on module-level variables, and neither Ruff nor ty enforces this. Annotate every module-level variable and constant, using `Final[...]` for constants (e.g. `SITE_TITLE: Final = "Tim's Page"`, `templates: Final[Jinja2Templates]`, `router: Final[APIRouter]`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Settings, the domain registry, the app factory, the base layout and the test
fixtures that every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T010 [P] Write unit tests for `Settings` in `tests/unit/test_config.py`:
  - `revision` defaults to `None`, and the empty string becomes `None`.
  - A valid SHA such as `"ABCDEF1"` is normalised to `"abcdef1"`.
  - A 40-character SHA is accepted.
  - Invalid values (`"xyz1234"`, `"abc12"`, and a 41-character string) become `None`, and a warning is logged (use `caplog`).
  - `repository_url` defaults to `https://github.com/tjh90/website`.
  - `WEBSITE_REVISION` and `WEBSITE_REPOSITORY_URL` env vars are honoured (use `monkeypatch.setenv`).
- [X] T011 [P] Write unit tests for the domain registry in `tests/unit/test_content.py`:
  - `PAGES` contains exactly `home` (`/`, "Tim's Page", "Home") and `about` (`/about`, "About", "About"), in that order.
  - Page names and paths are unique.
  - `tab_title(page)` returns `"Tim's Page"` for home and `"About · Tim's Page"` for about.
  - `BuildInfo.from_settings` sets `repository_url` to the settings URL as a string with no trailing slash (also when the setting is given with one).
  - It returns `short_revision`/`revision_url` as `None` when the revision is `None`. Otherwise `short_revision` is the first 7 characters and `revision_url` is `"{repository_url}/tree/{revision}"` with no double slash.
- [X] T012 Implement `Settings` in `src/website/config.py` as a pydantic-settings `BaseSettings` with `env_prefix="WEBSITE_"`:
  - `revision: str | None = None`: "Empty → `None`. Must match `^[0-9a-f]{7,40}$` (case-insensitive, normalised to lower case); otherwise a warning is logged and the value is treated as `None`". Implement this with a `field_validator(mode="before")` that logs through `logging.getLogger(__name__)`.
  - `repository_url: HttpUrl = HttpUrl("https://github.com/tjh90/website")`.
  - A `@lru_cache`'d `get_settings()` accessor.

  Add Google-style docstrings throughout. T010 must pass.
- [X] T013 Implement the base domain types in `src/website/content.py`:
  - A frozen, slotted `@dataclass` `Page` with `name: str`, `path: str`, `title: str` and `nav_label: str`.
  - Constants `SITE_TITLE = "Tim's Page"`, `HOME = Page("home", "/", "Tim's Page", "Home")`, `ABOUT = Page("about", "/about", "About", "About")`, `PAGES: tuple[Page, ...] = (HOME, ABOUT)` and `NOT_FOUND_TITLE = "Page not found"`.
  - `tab_title(title: str) -> str`, returning `SITE_TITLE` when `title == SITE_TITLE` and `f"{title} · {SITE_TITLE}"` otherwise.
  - A frozen `BuildInfo` with `repository_url: str` and `revision`, `short_revision` and `revision_url` (all `str | None`), and a `classmethod from_settings(settings: Settings) -> BuildInfo`. It sets `repository_url` to `str(settings.repository_url).rstrip("/")`, and derives `revision_url` by appending `/tree/{revision}` to that.

  T011 must pass.
- [X] T014 Implement `src/website/templating.py`:
  - Define a context processor `site_context(request: Request) -> dict[str, object]` that returns `nav_pages=PAGES`, `site_title=SITE_TITLE`, `build_info=BuildInfo.from_settings(request.app.state.settings)` and `tab_title=tab_title`. Templates read the repository URL as `build_info.repository_url`.
  - Create a single module-level `templates: Final[Jinja2Templates] = Jinja2Templates(directory=Path(__file__).parent / "templates", context_processors=[site_context])` (Starlette enables autoescape by default).
- [X] T015 Create the base layout `src/website/templates/base.html` per [contracts/page-layout.md](contracts/page-layout.md), without the drawer (US2 adds it):
  - `<!doctype html>`, `<html lang="en-GB">`, charset and viewport metas.
  - `<title>{{ tab_title(page_title) }}</title>`, `<link rel="stylesheet" href="{{ url_for('static', path='css/site.css') }}">` and `<link rel="icon" href="/favicon.ico">`.
  - A skip link `<a class="skip-link" href="#content">Skip to content</a>`.
  - `<header class="site-header">` containing `<h1>{{ page_title }}</h1>`.
  - `<main id="content">{% block content %}{% endblock %}</main>`.
  - Each child template sets the `page_title` and `current_page` variables.
- [X] T016 [P] Create `src/website/static/css/site.css`:
  - Define colours as custom properties on `:root`: `--color-bg`, `--color-text`, `--color-link`, `--color-header-bg` (start from `rgb(64 128 255)` and darken to at least 4.5:1 against white if axe flags it) and `--color-header-text: #fff`. This sets up the future dark-mode feature (FR-017).
  - Base typography: `font-family: system-ui, sans-serif`, plus `body { margin: 0 }`.
  - A header bar style and the skip link (visible on focus).
  - `img { max-width: 100%; height: auto }`.
  - No `@import` of external resources.
- [X] T017 Implement `create_app(settings: Settings | None = None) -> FastAPI` in `src/website/app.py`:
  - Construct `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` and store `app.state.settings = settings or get_settings()`.
  - Mount `StaticFiles(directory=<package>/static)` at `/static` with `name="static"`.
  - Include `routes.router`.
  - Add a pure-ASGI `SecurityHeadersMiddleware` (a class with `__call__(scope, receive, send)` that wraps `send` to add headers on `http.response.start`). It sets exactly:
    - `Content-Security-Policy: default-src 'self'; img-src 'self'; style-src 'self'; script-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`
    - `X-Content-Type-Options: nosniff`
    - `Referrer-Policy: strict-origin-when-cross-origin`
- [X] T018 Implement the health endpoint in `src/website/routes.py`: an `APIRouter` named `router` with `GET /healthz` returning `{"status": "ok"}` (`response_model` a Pydantic `HealthStatus(BaseModel)` with `status: Literal["ok"]`), excluded from the schema (`include_in_schema=False`).
- [X] T019 [P] Create `src/website/__main__.py` that runs `uvicorn.run("website.app:create_app", factory=True, host="127.0.0.1", port=8000)` behind an `if __name__ == "__main__":` guard (dev convenience: `uv run python -m website`).
- [X] T020 Create the shared fixtures in `tests/conftest.py`:
  - `settings` (function-scoped): `Settings(revision=None)`.
  - `app`: `create_app(settings)`.
  - `client`: `TestClient(app)`.
  - `live_server` (session-scoped): start `uvicorn.Server(uvicorn.Config(create_app(Settings(revision="0123456789abcdef0123456789abcdef01234567")), host="127.0.0.1", port=0, log_level="warning"))` in a daemon `threading.Thread`. Wait (≤10 s) until `server.started` is true, read the bound port from `server.servers[0].sockets[0].getsockname()[1]`, poll `/healthz` until 200, yield the base URL, then set `server.should_exit = True` and join the thread.
  - Override pytest-playwright's `base_url` fixture (session-scoped) to return `live_server`.
- [X] T021 Write `tests/integration/test_headers.py`, parametrised over `/`, `/about`, `/healthz`, `/static/css/site.css` and `/does-not-exist`. Assert that every response has the exact three security headers from [contracts/http-routes.md](contracts/http-routes.md) and **no** `set-cookie` header (FR-016). Also assert that `/docs`, `/redoc` and `/openapi.json` return 404, and that `GET /healthz` returns 200 with `{"status": "ok"}`. Do **not** assert status codes for the page paths here, and do not mark anything `xfail`. The middleware adds the headers whatever the status (including FastAPI's default 404 before the pages exist), so these tests pass from this phase onwards. Each story's own tests check its status codes.

**Checkpoint**: `uv run pytest` passes and `uv run uvicorn website.app:create_app --factory` serves `/healthz`.

---

## Phase 3: User Story 1 - Visitor views the home page (Priority: P1) 🎯 MVP

**Goal**: `/` shows "Tim's Page" with the GitHub, PhD Thesis and Paper icon links (opening in a new tab) and the Sisley painting.

**Independent Test**: Load `/` and check the title, the three links (text, href, icon, `target="_blank"`, `rel`) and the image with its alt text. Clicking a link opens a popup.

### Tests for User Story 1 ⚠️

> Write these first and confirm they fail.

- [X] T022 [P] [US1] Add `ExternalLink` tests to `tests/unit/test_content.py`:
  - `EXTERNAL_LINKS` equals, in order: (`"GitHub"`, `"https://www.github.com/tjh90"`, `Icon.GITHUB`), (`"PhD Thesis"`, `"https://eprints.soton.ac.uk/404274/"`, `Icon.BOOK`) and (`"Paper"`, `"https://ieeexplore.ieee.org/document/7029130"`, `Icon.FILE_LINES`).
  - Every URL starts with `https://`, and link texts are unique.
  - `Icon` has the members `GITHUB`, `BOOK`, `FILE_LINES` and `BARS`, mapping to `github.svg`, `book.svg`, `file-lines.svg` and `bars.svg`.
  - Every icon file exists under `src/website/templates/icons/` and contains `Font Awesome Free` and `License` in a leading `<!--!` comment (FR-016b).
- [X] T023 [P] [US1] Write `tests/integration/test_home.py` (`TestClient`), parsing HTML with the standard library's `html.parser` or simple regex/`in` checks:
  - `GET /` returns 200 and `text/html`, and `HEAD /` returns 200.
  - `<title>Tim's Page</title>` and `<h1>Tim's Page</h1>` are present.
  - A "Links:" `<h2>` is present.
  - For each `EXTERNAL_LINKS` item, an `<a>` has that `href`, `target="_blank"` and `rel="noopener noreferrer"`, and contains the text and an `<svg aria-hidden="true" focusable="false"`.
  - `<img src="/static/img/sisley.jpg" alt="Sisley - Lady's Cove (1897)"` is present, with `width` and `height` attributes.
- [X] T024 [P] [US1] Write `tests/e2e/test_home.py` (pytest-playwright `page` fixture, with `base_url` from T020):
  - `page.goto("/")` returns an ok response and the title is "Tim's Page".
  - For each link, `page.get_by_role("link", name=text)` has the expected `href`.
  - Clicking each link (with outbound requests stubbed: `context.route("https://**", lambda r: r.fulfill(status=200, body="ok"))`) opens a popup via `page.expect_popup()` whose URL starts with the expected URL, while the original page URL is unchanged.
  - `page.get_by_role("img", name="Sisley - Lady's Cove (1897)")` is visible.
  - At viewports 1280×800 and 1920×1080, the image's bounding box is to the right of the links section. At 320×640, it is below the links. At all three sizes, `document.documentElement.scrollWidth <= window.innerWidth` (SC-003).
- [X] T025 [P] [US1] Write `tests/e2e/test_external_links.py`, marked `@pytest.mark.external` and parametrised over `EXTERNAL_LINKS`. For each, send `httpx.head(url, follow_redirects=True, timeout=15)`, falling back to `httpx.get` on 405/403, and assert the final status is 2xx or 3xx with a message naming the URL.

### Implementation for User Story 1

- [X] T026 [P] [US1] Download the latest Font Awesome Free 7.x release and copy the SVGs for `github` (brands), `book` (solid), `file-lines` (solid) and `bars` (solid) into `src/website/templates/icons/github.svg`, `book.svg`, `file-lines.svg` and `bars.svg`.
  - Keep each file's leading `<!--! Font Awesome Free … License - https://fontawesome.com/license/free … Copyright … -->` comment exactly.
  - Add `aria-hidden="true" focusable="false" fill="currentColor" class="icon"` to the `<svg>` element.
  - Remove any `width`/`height` attributes so CSS sizes the icon.
- [X] T027 [P] [US1] Copy `sisley.jpg` from the reference branch into `src/website/static/img/sisley.jpg` (`git show main:ui/src/main/resources/net/tjh90/website/ui/views/home/sisley.jpg > src/website/static/img/sisley.jpg`, run in a shell that writes binary safely). Record its pixel width and height for T030.
- [X] T028 [P] [US1] Create `src/website/static/favicon.ico` from the reference favicon (`git show main:ui/src/main/resources/META-INF/resources/favicon.ico`), re-encoded as a multi-size (16, 32, 48 px) `.ico` of 16 KB or less, using Pillow run once via `uvx --with pillow python -c …`. Pillow must not become a project dependency.
- [X] T029 [US1] Add `Icon` (`StrEnum`, values are the SVG filenames: `GITHUB = "github.svg"`, `BOOK = "book.svg"`, `FILE_LINES = "file-lines.svg"`, `BARS = "bars.svg"`) and a frozen `ExternalLink` dataclass (`text: str`, `url: str` "Absolute `https://` URL", `icon: Icon`) to `src/website/content.py`. Also add `EXTERNAL_LINKS: tuple[ExternalLink, ...]` with the three instances in the order given in [data-model.md](data-model.md), and `PAINTING_ALT = "Sisley - Lady's Cove (1897)"`. T022 must pass.
- [X] T030 [US1] Create `src/website/templates/home.html`, extending `base.html`, with `page_title = "Tim's Page"` and `current_page = "home"`:
  - `<section class="links" aria-labelledby="links-heading">` containing `<h2 id="links-heading">Links:</h2>` and a `<ul>`. For each `EXTERNAL_LINKS` item: `<li><a href="{{ link.url }}" target="_blank" rel="noopener noreferrer">{% include "icons/" ~ link.icon %}{{ link.text }}</a></li>`.
  - `<figure class="painting"><img src="{{ url_for('static', path='img/sisley.jpg') }}" alt="{{ painting_alt }}" width="…" height="…"></figure>`, using the dimensions recorded in T027.
- [X] T031 [US1] Add `GET /` (name `home`) to `src/website/routes.py`. It returns `templates.TemplateResponse(request, "home.html", {"external_links": EXTERNAL_LINKS, "painting_alt": PAINTING_ALT})`, with `response_class=HTMLResponse` and `include_in_schema=False`. Also add `GET /favicon.ico` (`include_in_schema=False`), returning `FileResponse` of `static/favicon.ico` with `media_type="image/vnd.microsoft.icon"`.
- [X] T032 [US1] Add home styles to `src/website/static/css/site.css`:
  - `main` holds `.links` and `.painting`, stacked by default (links first).
  - At `@media (min-width: 768px)`, a two-column flex/grid with the links on the left and the painting on the right.
  - `.links li` uses `display: flex; align-items: center; gap: .5rem`, and `.icon { width: 1.25em; height: 1.25em }`.
  - `.links` keeps `padding-inline: 20px` (from the reference site).
  - Nothing may overflow at 320px.
- [X] T033 [US1] Run `uv run pytest tests/unit tests/integration/test_home.py tests/integration/test_headers.py tests/e2e/test_home.py` and fix failures until everything passes.

**Checkpoint**: The home page is fully working and tested on its own (MVP).

---

## Phase 4: User Story 2 - Visitor navigates between pages (Priority: P1)

**Goal**: Every page has a header with a "Menu" button that opens a JS-free popover drawer listing Home and About. The current page is marked, the drawer is closed on every page load, and unknown URLs return a 404 page with the full layout.

**Independent Test**: From `/`, open the drawer, choose each page, and check the URL, the `<h1>` and that the drawer is closed. Repeat at 375×812 and with JavaScript disabled. `/nope` returns 404 with the layout.

### Tests for User Story 2 ⚠️

- [X] T034 [P] [US2] Write `tests/integration/test_navigation.py` (`TestClient`):
  - For `/` and `/about`, the HTML contains `<button` with `popovertarget="nav-drawer"` and `aria-label="Menu"`, and `<nav id="nav-drawer" popover aria-label="Main">` with links `href="/"` (text "Home") and `href="/about"` (text "About").
  - Exactly one link has `aria-current="page"`, and it matches the current path.
  - `GET /does-not-exist` returns 404 and `text/html`, contains `<h1>Page not found</h1>`, `<title>Page not found · Tim's Page</title>`, the nav, a link `href="/"` in `<main>`, and no `aria-current`.
  - `GET /about/` redirects (307) to `/about`. (This needs US3's route; mark it `xfail(strict=True)` until US3 is done.)
- [X] T035 [P] [US2] Write `tests/e2e/test_navigation.py`, using helpers `is_drawer_open(page) -> bool` (`page.locator("#nav-drawer").evaluate("el => el.matches(':popover-open')")`) and `menu_button(page)` (`page.get_by_role("button", name="Menu")`):
  - (a) On load, the drawer is closed.
  - (b) Clicking Menu opens it. Clicking Menu again closes it. Pressing Escape closes it. Clicking in `main` closes it (light dismiss).
  - (c) Keyboard: focus Menu, press Enter, and the drawer opens. Press Escape, and the drawer closes and focus is back on the Menu button (`expect(menu_button(page)).to_be_focused()`).
  - (c2) Assistive-tech state (FR-009): when closed, `expect(menu_button(page)).to_have_attribute("aria-expanded", "false")` (or use the accessibility snapshot `page.accessibility`/`aria_snapshot()` showing `expanded=false`). After opening, it shows `expanded=true`. Use whichever of the attribute or the accessibility tree Chromium populates for `popovertarget`, and document the choice in a comment.
  - (d) Parametrised over `PAGES`: open the drawer, click `get_by_role("link", name=page.nav_label)` inside the nav, then assert the URL ends with `page.path`, `h1` has the text `page.title`, and the drawer is closed.
  - (e) The current page's nav link has `aria-current="page"`.
  - (f) Mobile: `browser.new_context(viewport={"width": 375, "height": 812})` repeats (d) for About, and `scrollWidth <= innerWidth`.
  - (g) No JS: `browser.new_context(java_script_enabled=False)` repeats (b) (click open and close) and (d).
  - (h) `/does-not-exist` shows the h1 "Page not found", and its Home link navigates to `/`.

  Mark the About parametrisations `xfail(strict=True)` until US3 is done.

### Implementation for User Story 2

- [X] T036 [US2] Add the drawer to `src/website/templates/base.html`:
  - Inside `<header class="site-header">`, before the `<h1>`, add `<button type="button" class="menu-button" popovertarget="nav-drawer" aria-label="Menu">{% include "icons/bars.svg" %}</button>`.
  - After the header, add `<nav id="nav-drawer" class="drawer" popover aria-label="Main"><ul>{% for p in nav_pages %}<li><a href="{{ p.path }}"{% if p.name == current_page %} aria-current="page"{% endif %}>{{ p.nav_label }}</a></li>{% endfor %}</ul></nav>`.
- [X] T037 [US2] Add drawer styles to `src/website/static/css/site.css`:
  - `.site-header`: `display: flex; align-items: center; gap: 1rem`, with background `var(--color-header-bg)` and colour `var(--color-header-text)`.
  - `.menu-button`: transparent, inherits colour, at least a 44×44px target, with a visible `:focus-visible` outline.
  - `.drawer[popover]`: `position: fixed; inset: 0 auto 0 0; margin: 0; width: min(18rem, 85vw); height: 100dvh; border: 0; padding: 1rem`, with background `var(--color-bg)` and a box-shadow.
  - `.drawer::backdrop`: a semi-transparent background.
  - `[aria-current="page"]`: bold, with an inline-start border.
  - `@media (prefers-reduced-motion: no-preference)`: an optional slide-in using `@starting-style`.
  - Fallback for browsers without popover support: `.drawer:not([popover])` is unnecessary, because unsupported browsers render the element inline (acceptable per research R1).
- [X] T038 [US2] Create `src/website/templates/not_found.html`, extending `base.html`, with `page_title = "Page not found"` (use the `NOT_FOUND_TITLE` constant passed in the context) and `current_page = None`. The body is `<p>Sorry, that page doesn't exist.</p><p><a href="/">Go to the home page</a></p>`.
- [X] T039 [US2] In `src/website/app.py`, register `@app.exception_handler(StarletteHTTPException)`. When `exc.status_code == 404`, return `templates.TemplateResponse(request, "not_found.html", {"not_found_title": NOT_FOUND_TITLE}, status_code=404)`. Otherwise delegate to `fastapi.exception_handlers.http_exception_handler`. Check that security headers still apply to 404 responses.
- [X] T040 [US2] Run `uv run pytest tests/integration/test_navigation.py tests/e2e/test_navigation.py tests/integration/test_headers.py` until everything passes, apart from the About xfails.

**Checkpoint**: The layout and navigation work across pages, with and without JS, on desktop and mobile.

---

## Phase 5: User Story 3 - Visitor finds the site's source code (Priority: P1)

**Goal**: `/about` shows the AGPL-3.0 statement and licence link, the source repository link, the running revision (when known), the "no cookies" statement and the Credits section.

**Independent Test**: Load `/about` with and without a revision, and check every item in [contracts/page-layout.md](contracts/page-layout.md) § About page.

### Tests for User Story 3 ⚠️

- [X] T041 [P] [US3] Add `Credit` and licence-constant tests to `tests/unit/test_content.py`:
  - `CREDITS` equals, in order: `Credit(work="Font Awesome Free icons", author="Fonticons, Inc.", work_url="https://fontawesome.com", licence="CC BY 4.0", licence_url="https://creativecommons.org/licenses/by/4.0/")` and `Credit(work="Lady's Cove (1897)", author="Alfred Sisley", work_url=None, licence="Public domain", licence_url=None)`.
  - `LICENCE_NAME == "GNU Affero General Public License v3.0"`.
  - `LICENCE_URL == "https://www.gnu.org/licenses/agpl-3.0.html"`.
  - `COOKIE_STATEMENT == "This site does not use cookies."`.
- [X] T042 [P] [US3] Write `tests/integration/test_about.py` (`TestClient`):
  - With the default fixture (revision `None`): `GET /about` returns 200, with `<title>About · Tim's Page</title>` and `<h1>About</h1>`.
  - It contains `href="https://www.gnu.org/licenses/agpl-3.0.html"` with the text "GNU Affero General Public License v3.0", and `href="https://github.com/tjh90/website"` with `target="_blank"` and `rel="noopener noreferrer"`.
  - It contains "This site does not use cookies.", plus a "Credits" `<h2>` with a Font Awesome link to `https://fontawesome.com`, a CC BY 4.0 link to `https://creativecommons.org/licenses/by/4.0/`, and the text "Alfred Sisley, Lady's Cove (1897), public domain".
  - It does **not** contain "Running revision".
  - With `create_app(Settings(revision="0123456789abcdef0123456789abcdef01234567"))`, it contains "Running revision", `href="https://github.com/tjh90/website/tree/0123456789abcdef0123456789abcdef01234567"` and `<code>0123456</code>`.
- [X] T043 [P] [US3] Write `tests/e2e/test_about.py`:
  - Navigating from `/` via the drawer to About works.
  - `get_by_role("link", name="Source code on GitHub")` has href `https://github.com/tjh90/website`, and clicking it (with outbound requests stubbed as in T024) opens a popup.
  - The revision link shows `0123456` (from the `live_server` revision in T020).
  - `get_by_role("heading", name="Credits")` is visible.
  - `context.cookies()` is empty after visiting `/` and `/about` (FR-016).

### Implementation for User Story 3

- [X] T044 [US3] Add to `src/website/content.py`:
  - A frozen `Credit` dataclass with these fields:
    - `work: str` ("Name of the work")
    - `author: str` ("Author or owner")
    - `work_url: str | None` ("Link to the work or its project, if any")
    - `licence: str` ("Licence name, e.g. "CC BY 4.0", "Public domain"")
    - `licence_url: str | None` ("Link to the licence text; `None` for the public domain")
  - `CREDITS: tuple[Credit, ...]` with the two instances from [data-model.md](data-model.md), and the constants `LICENCE_NAME`, `LICENCE_URL` and `COOKIE_STATEMENT` with the exact values given there.

  T041 must pass.
- [X] T045 [US3] Create `src/website/templates/about.html`, extending `base.html`, with `page_title = "About"` and `current_page = "about"`. Follow [contracts/page-layout.md](contracts/page-layout.md) § About page exactly:
  - A "Source code" section with the licence sentence and link, and `<a href="{{ build_info.repository_url }}" target="_blank" rel="noopener noreferrer">Source code on GitHub</a>`.
  - `{% if build_info.revision %}<p>Running revision <a href="{{ build_info.revision_url }}" target="_blank" rel="noopener noreferrer"><code>{{ build_info.short_revision }}</code></a></p>{% endif %}`.
  - A "Cookies" section with `{{ cookie_statement }}`.
  - A "Credits" section that loops over `credits`. For each, render the work (linked if `work_url`), the author and the licence (linked if `licence_url`). The public-domain entry must render exactly "Alfred Sisley, Lady's Cove (1897), public domain"; use a per-credit format, or special-case `licence_url is None`.
- [X] T046 [US3] Add `GET /about` (name `about`) to `src/website/routes.py`, rendering `about.html` with `{"credits": CREDITS, "licence_name": LICENCE_NAME, "licence_url": LICENCE_URL, "cookie_statement": COOKIE_STATEMENT}`, with `response_class=HTMLResponse` and `include_in_schema=False`. The repository URL and revision come from `build_info` in the shared context (T014), so they are not passed here.
- [X] T047 [US3] Remove every remaining `xfail` mark that references US3, in `tests/integration/test_navigation.py` and `tests/e2e/test_navigation.py`. Then run `uv run pytest` and fix failures until the whole default suite passes.

**Checkpoint**: All visitor-facing stories (US1–US3) work and pass their tests.

---

## Phase 6: User Story 4 - Maintainer gets automated quality checks and a deployable build (Priority: P1)

**Goal**: CI runs every constitution quality gate with a per-test report. Dependabot proposes updates. A non-root container image with a health check runs behind Caddy, which obtains Let's Encrypt certificates automatically.

**Independent Test**: Open a PR containing a formatting error and a failing test, and confirm the matching jobs fail. Fix both and confirm everything passes with a test report. Run `docker compose -f build/compose.yml up` and confirm `website` becomes healthy before Caddy serves HTTPS, and that HTTP redirects with a 308.

### Implementation for User Story 4

- [X] T048 [P] [US4] Create `.dockerignore` at the repo root. It excludes `.git`, `.venv`, `**/__pycache__`, `.pytest_cache`, `.ruff_cache`, `reports`, `test-results`, `specs`, `.specify`, `.claude`, `.github`, `tests` and `build/.env`. `src/`, `pyproject.toml`, `uv.lock`, `.python-version`, `README.md` and `LICENSE` must still be included.
- [X] T049 [US4] Write `build/Dockerfile` per research R12, using the repo root as build context:
  - **Stage `builder`**: `FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim@sha256:<digest>`.
    - Set `ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0` and `WORKDIR /app`.
    - `RUN --mount=type=cache,target=/root/.cache/uv --mount=type=bind,source=uv.lock,target=uv.lock --mount=type=bind,source=pyproject.toml,target=pyproject.toml uv sync --locked --no-dev --no-install-project`.
    - `COPY pyproject.toml uv.lock .python-version README.md LICENSE ./`, then `COPY src ./src`.
    - `RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-editable`.
  - **Stage `website-run`**: `FROM python:3.14-slim-trixie@sha256:<digest>`.
    - `RUN useradd --system --uid 10001 --no-create-home website`.
    - `COPY --from=builder --chown=website:website /app/.venv /app/.venv`.
    - `ENV PATH="/app/.venv/bin:$PATH"`, then `ARG WEBSITE_REVISION=` and `ENV WEBSITE_REVISION=${WEBSITE_REVISION}`.
    - `USER website`, `EXPOSE 8000`.
    - `HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python","-c","import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]`.
    - `CMD ["uvicorn","website.app:create_app","--factory","--host","0.0.0.0","--port","8000","--proxy-headers","--forwarded-allow-ips","*"]`.

  Look up the current digests with `docker buildx imagetools inspect <image:tag>` and pin them.
- [X] T050 [US4] Write `build/Caddyfile` exactly as in research R13:
  - A global block with `email {$ACME_EMAIL}` and `acme_ca {$ACME_CA:https://acme-v02.api.letsencrypt.org/directory}`.
  - A site block `{$SITE_DOMAIN:localhost}` with `encode zstd gzip`, `header Strict-Transport-Security "max-age=31536000; includeSubDomains"` and `reverse_proxy website:8000`.
  - A comment explaining that Caddy redirects HTTP→HTTPS (308) automatically and uses its internal CA for `localhost`.
- [X] T051 [US4] Write `build/compose.yml`, with project `name: website`:
  - Service `website`: `build: {context: .., dockerfile: build/Dockerfile, target: website-run, args: {WEBSITE_REVISION: ${WEBSITE_REVISION:-}}}`, `image: website:latest`, `restart: unless-stopped` and `expose: ["8000"]`, with **no** `ports`.
  - Service `caddy`: `image: caddy:<latest 2.x>-alpine@sha256:<digest>`, `ports: ["80:80", "443:443", "443:443/udp"]` and `environment: {SITE_DOMAIN: ${SITE_DOMAIN:-localhost}, ACME_EMAIL: ${ACME_EMAIL:-}, ACME_CA: ${ACME_CA:-https://acme-v02.api.letsencrypt.org/directory}}`.
    - Volumes: `./Caddyfile:/etc/caddy/Caddyfile:ro`, `caddy_data:/data` and `caddy_config:/config`.
    - `depends_on: {website: {condition: service_healthy}}` and `restart: unless-stopped`.
  - Top-level `volumes: {caddy_data: {}, caddy_config: {}}`, with a comment that `caddy_data` must be kept to avoid ACME rate limits.
- [X] T052 [P] [US4] Create `build/.env.example` documenting `SITE_DOMAIN=example.com`, `ACME_EMAIL=you@example.com`, an optional commented `# ACME_CA=https://acme-staging-v02.api.letsencrypt.org/directory` (for trial runs), and an optional `WEBSITE_REVISION=` (set by `--build-arg` or CI). It must contain no real values.
- [X] T053 [US4] Write `.github/workflows/ci.yml`:
  - Name `CI`, triggered `on: push: branches: [main]` and `pull_request: branches: [main]`, with `permissions: contents: read`.
  - `concurrency` cancels in-progress runs for the same ref.
  - **Job `checks`** (ubuntu-latest):
    - `actions/checkout@v6`, then `astral-sh/setup-uv@v7` (or the current major) with `enable-cache: true`.
    - Separately named steps: `uv lock --check`, `uv run ruff format --check`, `uv run ruff check --output-format=github` and `uv run ty check`.
  - **Job `test`**: checkout and setup-uv, then `uv sync --locked`, then `uv run playwright install --with-deps chromium`, then `uv run pytest --junitxml=reports/junit.xml`.
    - Then `dorny/test-reporter@v3` with `if: ${{ !cancelled() }}`, `name: pytest results`, `path: reports/junit.xml` and `reporter: java-junit`.
    - The job has `permissions: {contents: read, checks: write}`.
  - **Job `docker`**: checkout, then `docker/setup-buildx-action@v4`, then `docker/build-push-action@v7` with `context: .`, `file: build/Dockerfile`, `target: website-run`, `push: false`, `build-args: WEBSITE_REVISION=${{ github.sha }}`, `cache-from: type=gha` and `cache-to: type=gha,mode=max`.

  Check every action's current major version at implementation time.
- [X] T054 [P] [US4] Write `.github/workflows/external-links.yml`:
  - Name `External links`, triggered `on: schedule: - cron: "0 6 * * 1"` and `workflow_dispatch`, with `permissions: contents: read`.
  - One job: checkout and setup-uv, then `uv sync --locked`, then `uv run pytest -m external`.
- [X] T055 [P] [US4] Create `.github/dependabot.yml` with `version: 2` and four weekly update entries, each grouping all updates under one group (`patterns: ["*"]`):
  - `package-ecosystem: "uv"` (directory `/`)
  - `"docker"` (directory `/build`)
  - `"docker-compose"` (directory `/build`)
  - `"github-actions"` (directory `/`)
- [X] T056 [P] [US4] Append `*.jpg binary`, `*.png binary`, `*.ico binary`, `*.woff2 binary` and `*.svg text eol=lf` to `.gitattributes`, keeping the existing `* text=auto eol=lf` line first. This stops images being given LF line endings or diffed as text.
- [X] T057 [US4] Validate the container locally:
  - `docker build -f build/Dockerfile --target website-run --build-arg WEBSITE_REVISION=$(git rev-parse HEAD) -t website:test .` succeeds.
  - `docker run --rm -d -p 8000:8000 --name website-test website:test`. Then `docker inspect --format '{{.State.Health.Status}}' website-test` becomes `healthy`, `docker exec website-test id -u` is not 0, and `curl -s localhost:8000/about` contains the 7-character revision.
  - Stop the container.
  - Then `docker compose -f build/compose.yml up -d` (with `build/.env` copied from the example, using `SITE_DOMAIN=localhost`). `curl -kI https://localhost` returns 200 with `strict-transport-security`, and `curl -I http://localhost` returns 308.
  - Tear down with `docker compose -f build/compose.yml down` (keep the volumes).

  Report the results. If Docker is unavailable, say so.

**Checkpoint**: All quality gates are automated and the site is deployable with automatic HTTPS.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, compliance review and final validation.

- [X] T058 Write `tests/e2e/test_accessibility.py`, using the pytest-playwright `page` fixture:
  - For `/`, `/about` and `/does-not-exist`, with the drawer closed and then open (click Menu), run `Axe().run(page)` (axe-playwright-python).
  - Assert there are no violations with `impact in {"serious", "critical"}`, and include `results.generate_report()` in the failure message (FR-018, SC-005).
  - If axe flags the header colour contrast, darken `--color-header-bg` in `site.css` until it passes.
- [X] T059 [P] Rewrite `README.md`:
  - The CI badge pointing at `.github/workflows/ci.yml`.
  - A pages table: `/` Home and `/about` About. Remove the Anascramble row until that feature lands.
  - Prerequisites: uv, Docker with Compose v2.
  - Local run (`uv sync`, `uv run playwright install chromium`, `uv run uvicorn website.app:create_app --factory --reload`).
  - Each quality-gate command, as in [quickstart.md](quickstart.md) §2, plus `uv run pytest -m external`.
  - Optional `pre-commit install`.
  - Deployment: copy `build/.env.example`, set the domain and email, `docker compose -f build/compose.yml up -d --build`, DNS and ports 80/443, and the staging CA tip.
  - Licence: AGPL-3.0.

  Use separate fenced code blocks for each command.
- [X] T060 [P] Do a licence-compliance review (constitution VI):
  - Confirm all four icon SVGs keep their Font Awesome comment.
  - Confirm the About page's Credits cover every third-party asset shipped (Font Awesome icons and the Sisley painting).
  - Re-run the dependency licence listing from T003 against the final `uv.lock`, in case resolution changed. Confirm every runtime dependency's licence is still compatible with AGPL-3.0, and record the result in the PR description.
- [X] T061 Measure the home page weight: sum `Content-Length` for `/`, `site.css`, `sisley.jpg` and `favicon.ico` with `TestClient` or `curl`. Confirm it is under 500 KB (SC-004) and fix it if not.
- [ ] T062 Run the full local quality-gate sequence: `uv lock --check`, `uv run ruff format --check`, `uv run ruff check`, `uv run ty check` and `uv run pytest`. Then:
  - Walk through every manual scenario in the [quickstart.md](quickstart.md) §3 table, and report pass/fail for each.
  - Grep `src/` and `tests/` for module-level assignments without annotations (constitution III) and fix any you find.
  - Record `/` and `/about` render time from the Playwright trace or browser DevTools; it must be under 1 s (SC-004).
  - Once the first PR's CI run finishes, record its total duration; it must be under 10 minutes (SC-006).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 first (working-tree check). Then T002 → T003 → T004. T005–T008 can run in parallel after T003. T009 runs last.
- **Foundational (Phase 2)**: Depends on Setup and blocks all stories. T010 and T011 (tests) run before T012 and T013. T014 needs T012 and T013. T015 needs T014. T017 needs T012 and T014. T018 and T019 need T017. T020 needs T017 and T018. T021 needs T020.
- **US1 (Phase 3)**, **US2 (Phase 4)** and **US3 (Phase 5)**: Each depends only on Foundational. They touch some shared files (`routes.py`, `content.py`, `site.css`, `base.html`), so they run **sequentially in the order US1 → US2 → US3**. The xfail marks keep each story's tests independent of the stories that come later.
- **US4 (Phase 6)**: Every US4 task except the container validation depends only on Setup and Foundational (config files), so they can run in parallel with US1–US3. The container validation (last task in Phase 6) needs US1–US3 to be complete.
- **Polish (Phase 7)**: Depends on all stories. The accessibility test task comes first in Polish, because it covers the pages from US1–US3.

### Within Each User Story

- Tests are written first and must fail. Then come domain types (`content.py`), then templates, then routes, then styles, then the story's test run.

## Parallel Opportunities

- Phase 1: T005, T006, T007 and T008.
- Phase 2: T010 and T011; T016 and T019 alongside T014–T018.
- US1: T022–T025 (tests) together; T026–T028 (assets) together.
- US2: T034 and T035 together.
- US3: T041–T043 together.
- US4: T048, T052, T054, T055 and T056 together, and alongside the US1–US3 work. (T056 should
  land before T027 and T028 commit binary files.)
- Polish: T059 and T060 together.

## Parallel Example: User Story 1

```bash
# Tests first (different files):
Task: "T023 [US1] Integration tests for / in tests/integration/test_home.py"
Task: "T024 [US1] Playwright tests for / in tests/e2e/test_home.py"
Task: "T025 [US1] External link reachability in tests/e2e/test_external_links.py"

# Then assets in parallel:
Task: "T026 [US1] Font Awesome SVG subset in src/website/templates/icons/"
Task: "T027 [US1] sisley.jpg into src/website/static/img/"
Task: "T028 [US1] Re-encoded favicon in src/website/static/favicon.ico"
```

## Parallel Example: User Story 4 (alongside US1–US3)

```bash
Task: "T048 [US4] .dockerignore"
Task: "T052 [US4] build/.env.example"
Task: "T054 [US4] .github/workflows/external-links.yml"
Task: "T055 [US4] .github/dependabot.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup → Phase 2: Foundational.
2. Phase 3: US1 (home page).
3. **Stop and validate**: `uv run pytest`. The home page renders on its own (with just the header title, no drawer yet).

### Incremental Delivery

1. Setup and Foundational give a running app with `/healthz`.
2. US1 adds the home page (MVP).
3. US2 adds the drawer navigation and the 404 page.
4. US3 adds the About page (needed for AGPL compliance **before any public deployment**).
5. US4 adds CI, Dependabot, Docker and Caddy. The config files can land earlier, in parallel.
6. Polish adds the README, the compliance review and the final validation.

## Notes

- [P] means different files with no dependency on an incomplete task. [USn] traces a task to its spec story.
- Do not deploy publicly until US3 is complete (AGPL §13).
- Commit after each task or logical group, using Conventional Commits (`feat:`, `test:`, `ci:`, `build:`, `docs:`).
- Never use `pip`. Every Python command runs through `uv` (constitution I).
- Do not author any `.js` files (constitution II).
