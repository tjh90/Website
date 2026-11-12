# Implementation Plan: Home Page, Navigation, About Page and CI

**Branch**: `rewrite` (feature id `001-home-page-and-ci`) | **Date**: 2026-11-12 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-home-page-and-ci/spec.md`

## Summary

Create the first part of the site: a FastAPI app that renders Jinja2 pages for Home (`/`) and
About (`/about`), plus a 404 page, all sharing one layout. The layout has a coloured header with a
hamburger menu button and the page title. The side drawer is built with the native HTML **Popover
API** (`popovertarget`), so it works without any JavaScript, and its open/closed state is
announced to assistive technology automatically. Icons are a subset of Font Awesome Free inline
SVGs that keep their licence comments. The About page shows the AGPL statement, the source link
with the build revision (from a `WEBSITE_REVISION` env var baked in at image build time), the
statement that the site sets no cookies, and the Credits section.

The plumbing that ships with the pages:

- a uv project with Ruff and ty configured;
- tests: pytest unit, `TestClient` integration and pytest-playwright E2E with axe;
- a GitHub Actions workflow covering every constitution quality gate, with a JUnit report;
- Dependabot for uv, Docker, Docker Compose and Actions;
- a multi-stage uv Dockerfile;
- Docker Compose with Caddy, which gets Let's Encrypt certificates automatically.

## Technical Context

**Language/Version**: Python 3.14 (`requires-python = ">=3.14"`)

**Primary Dependencies**: FastAPI, Uvicorn (`standard` extra), Jinja2, pydantic-settings. Dev:
Ruff, ty, pytest, pytest-playwright, axe-playwright-python, httpx2 (for Starlette's test client).
`fastapi[standard]` was rejected during implementation: it now pulls in the FastAPI Cloud CLI,
Sentry and OpenTelemetry SDKs, which this site doesn't need. The latest
versions are resolved by `uv add` at implementation time and locked in `uv.lock`.

**Storage**: N/A (stateless; no cookies, sessions or database)

**Testing**: pytest. Unit tests cover domain models and settings; integration tests use
FastAPI `TestClient` for routes, HTML and headers; E2E tests use pytest-playwright (Chromium)
against a live Uvicorn server, with axe checks. External-link checks are marked `external` and
excluded from the default run.

**Target Platform**: Linux container (Debian slim) behind Caddy, deployed with Docker Compose.
Development works on Windows, macOS and Linux via uv.

**Project Type**: Server-rendered web application (single project)

**Performance Goals**: Pages render in under 1 s (SC-004). The home page weighs under 500 KB in
total (the image is ~70 KB; the favicon is re-encoded to stay small).

**Constraints**: No hand-written JavaScript and no third-party CDNs (constitution II and V). No
cookies (FR-016). WCAG 2.2 AA (FR-018). Everything works without JS (FR-010). Strict CSP
(`default-src 'self'`).

**Scale/Scope**: A personal site with low traffic: 2 content pages + 404 page + health endpoint.
A single Uvicorn worker is enough.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Modern Python Toolchain | Python 3.14, uv only, `pyproject.toml` + `uv.lock` committed, FastAPI/Uvicorn/Jinja2 | PASS |
| II. Server-Rendered UI, No Hand-Written JS (v1.0.1) | All HTML rendered on the server; no `.js` files authored. The drawer is purely client-side UI state, so it uses the native Popover API, as principle II requires. HTMX is not vendored yet: this feature has no server-driven interactivity, so the Anascramble feature will add it | PASS |
| III. Type Safety & Code Style | Ruff rule set as mandated, Google docstrings, ty clean, settings via pydantic-settings, domain types as frozen dataclasses/Pydantic | PASS |
| IV. Automated Testing & UI Verification | Unit, integration and Playwright tests for every story; axe checks; deterministic (no randomness in this feature) | PASS |
| V. Simplicity | No DB/cache; static assets self-hosted; domain data (pages, links, credits) kept separate from web code | PASS |
| VI. Licence Compliance & Attribution | About page: AGPL statement, licence link, repo + revision link, Credits (Font Awesome CC BY 4.0, Sisley public domain); FA licence comments kept in inline SVGs | PASS |
| Technology & Deployment | Multi-stage uv image, `--locked`, non-root, `HEALTHCHECK`; Caddy + Let's Encrypt, HTTP→HTTPS, HSTS, `caddy_data` volume, app not published to host; env-driven config with `.env.example`; images pinned by digest; Dependabot | PASS |
| Quality Gates | CI runs lock check, Ruff format, Ruff lint, ty, pytest (+Playwright), Docker build, on push/PR to the default branch | PASS |

No violations, so Complexity Tracking is empty.

**Post-design re-check (after Phase 1)**: PASS. The design artifacts add no dependencies or
infrastructure beyond the above. Constitution v1.0.1 makes explicit that client-side UI state such
as the drawer uses native HTML features, and that HTMX is for server-driven interactivity, so the
popover drawer complies directly.

## Project Structure

### Documentation (this feature)

```text
specs/001-home-page-and-ci/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── http-routes.md   # Routes, status codes, headers
│   └── page-layout.md   # UI/DOM contract used by tests
└── tasks.md             # Phase 2 output (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
pyproject.toml               # Project metadata, deps, Ruff/ty/pytest config
uv.lock
.python-version              # 3.14
.pre-commit-config.yaml      # Optional local hooks: Ruff + ty
README.md

src/website/
├── __init__.py
├── __main__.py              # `uv run python -m website` → Uvicorn (dev convenience)
├── app.py                   # create_app() factory: routes, static mount, 404 handler, headers
├── config.py                # Settings (pydantic-settings): revision, repository URL
├── content.py               # Domain data: Page registry, ExternalLink, Credit, BuildInfo
├── routes.py                # Page and health endpoints (APIRouter)
├── templating.py            # Jinja2Templates setup + shared context (nav, build info)
├── templates/
│   ├── base.html            # Layout: header, menu button, popover drawer, <main>
│   ├── home.html
│   ├── about.html
│   ├── not_found.html
│   └── icons/               # Font Awesome Free SVG subset (licence comments retained)
│       ├── github.svg
│       ├── book.svg
│       ├── file-lines.svg
│       └── bars.svg         # Hamburger icon
└── static/
    ├── css/site.css         # Theme tokens (CSS custom properties) + layout
    ├── img/sisley.jpg
    └── favicon.ico

tests/
├── conftest.py              # Shared fixtures: app, TestClient, live server (uvicorn thread)
├── unit/
│   ├── test_config.py
│   └── test_content.py
├── integration/
│   ├── test_routes.py       # Status codes, titles, links, About content, 404, health
│   └── test_headers.py      # No Set-Cookie, security headers
└── e2e/
    ├── test_home.py         # Links, new-tab behaviour, image, layout at 320px
    ├── test_navigation.py   # Drawer open/close, navigation, title, mobile, no-JS
    ├── test_about.py
    ├── test_accessibility.py # axe on every page, drawer open/closed
    └── test_external_links.py # @pytest.mark.external: real link reachability

build/
├── Dockerfile               # Multi-stage uv build → slim runtime, non-root, HEALTHCHECK
├── compose.yml              # website + caddy services, caddy_data volume
├── .env.example             # SITE_DOMAIN, ACME_EMAIL, ACME_CA (real .env is git-ignored)
└── Caddyfile                # Let's Encrypt via ACME, HSTS, reverse_proxy website:8000

.github/
├── workflows/
│   ├── ci.yml               # Quality gates + JUnit report + Docker build
│   └── external-links.yml   # Weekly + manual: pytest -m external
└── dependabot.yml           # uv, docker, docker-compose, github-actions (weekly)

.dockerignore
```

**Structure Decision**: A single project with a `src/` layout (`uv init --package`), which keeps
the importable `website` package separate from the tests and is what packaging expects. Templates
and static files live inside the package so they ship in the wheel and the Docker image. Tests
are split into unit, integration and e2e folders so the slower browser tests can be filtered by
folder.

## Complexity Tracking

No constitution violations to justify.
