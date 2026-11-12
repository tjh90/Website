<!--
Sync Impact Report
==================
Version change: 1.0.0 → 1.0.1 (PATCH: clarification)
Modified principles:
  - II. Server-Rendered UI, No Hand-Written JavaScript: the HTMX mandate now covers server-driven
    interactivity only; purely client-side UI state uses native HTML features (Popover API,
    <details>, <dialog>); htmx is vendored only once a feature needs it.
Added sections: None
Removed sections: None
Templates requiring updates: None (templates read the constitution at runtime)
Follow-up TODOs: None
-->

# Website Constitution

## Core Principles

### I. Modern Python Toolchain

- The application MUST be written in Python, targeting the latest stable CPython release
  (currently 3.14), declared via `requires-python` in `pyproject.toml`.
- uv MUST be the sole tool for Python installation, dependency management, virtual environments
  and task execution. `pyproject.toml` and `uv.lock` MUST be committed; ad-hoc `pip install`
  or `requirements.txt` files are prohibited.
- FastAPI MUST be the web framework, served by Uvicorn. HTML MUST be produced with Jinja2
  templates via FastAPI's `Jinja2Templates`.
- Dependencies MUST be well-supported public packages; bespoke replacements for existing
  libraries require written justification in the feature plan.

**Rationale**: A single, fast, lockfile-driven toolchain keeps builds reproducible locally, in
CI and in Docker, and keeps the stack current.

### II. Server-Rendered UI, No Hand-Written JavaScript

- Pages MUST be rendered server-side as HTML. Business logic MUST live in Python, never in the
  browser.
- Server-driven interactivity (anything that needs data or HTML from the server without a full
  page load) MUST be delivered with HTMX: server endpoints return HTML fragments that HTMX swaps
  into the page. The htmx library MUST be vendored (served from the app's static files,
  version-pinned) rather than loaded from a third-party CDN, and only once a feature needs it.
- Purely client-side UI state (e.g. opening a menu, expanding a section) MUST use native HTML
  features that need no JavaScript, such as the Popover API, `<details>`/`<summary>` or
  `<dialog>` with invoker commands, in preference to HTMX or scripts.
- The project MUST NOT contain hand-written JavaScript. Any unavoidable exception MUST be
  justified in the feature plan, kept minimal, and covered by Playwright tests.
- Core content MUST remain usable without JavaScript (progressive enhancement) where
  practical; HTMX-enhanced forms MUST degrade to standard form submissions.
- Client-side Python runtimes (PyScript/Pyodide, Brython) are out of scope: their multi-megabyte
  payloads and cold-start latency are disproportionate to this site's needs.

**Rationale**: Keeping all logic in Python means one language, one test suite and fully
typed code paths, while HTMX provides responsive UX without authoring JavaScript.

### III. Type Safety & Code Style

- All functions, methods and module-level variables MUST carry type hints using modern syntax
  (PEP 604 unions, PEP 585 built-in generics, PEP 695 type parameters where applicable).
  `Any` and `# type: ignore` MUST be justified with an inline comment.
- ty MUST pass with zero diagnostics on `src/` and `tests/`.
- Ruff MUST be used for both linting and formatting, configured in `pyproject.toml`. The lint
  rule selection MUST include at minimum: pycodestyle (`E`, `W`), Pyflakes (`F`), isort (`I`),
  pep8-naming (`N`), pydocstyle (`D`, Google convention), pyupgrade (`UP`), flake8-bugbear
  (`B`), flake8-simplify (`SIM`), flake8-annotations (`ANN`) and Ruff-specific rules (`RUF`).
- Code MUST conform to PEP 8 (enforced by Ruff format and lint) and docstrings to PEP 257
  (Google style). Every public module, class, function and method MUST have a docstring.
- Request/response and configuration data MUST be modelled with Pydantic models (and
  `pydantic-settings` for configuration) rather than untyped dicts.

**Rationale**: Static typing and automated style enforcement catch defects early and make the
codebase self-documenting.

### IV. Automated Testing & UI Verification (NON-NEGOTIABLE)

- pytest MUST be the test runner. Every feature MUST ship with tests in the same change.
- Domain logic MUST be covered by unit tests. Randomised logic MUST be testable
  deterministically via injectable seeds or random generators.
- User-facing pages and interactions MUST be covered by Playwright UI tests
  (pytest-playwright) run against the real application served by Uvicorn.
- Route/endpoint behaviour MUST be tested with FastAPI's `TestClient` (or an async httpx
  client); browser behaviour (HTMX swaps, layout, navigation) with Playwright.
- Pages SHOULD be checked for accessibility violations with axe in Playwright tests.

**Rationale**: Tests define the site's expected behaviour and guard against regressions;
browser-level tests are the only way to verify server-rendered, HTMX-driven interactions.

### V. Simplicity

- Static assets (images, icons, fonts, stylesheets) MUST be self-hosted and served by the
  app's static files mount rather than third-party CDNs.
- Features MUST be implemented in the simplest way that satisfies the spec (YAGNI). Added
  infrastructure (databases, caches, task queues) requires a spec-level justification.
- Domain logic MUST be separated from web/presentation code so it can be unit tested without
  HTTP or templates.

**Rationale**: A small personal site gains nothing from speculative complexity; every moving
part is something to maintain, secure and deploy.

### VI. Licence Compliance & Attribution

- The project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). The About
  page MUST state this licence, link to the licence text, and link to the public source
  repository, including the revision the running site was built from when that is known.
- Every third-party dependency and asset (code, fonts, icons, images, media) MUST have a licence
  that is compatible with AGPL-3.0. Its compatibility MUST be checked when it is added.
- Any third-party asset shown to visitors whose licence requires attribution (e.g. CC BY) MUST be
  credited in the About page's Credits section in the same change that adds the asset. The credit
  MUST give the work's name, its author or owner, and its licence, linking to the licence where
  one exists. A courtesy credit SHOULD also be given for public-domain works.
- Licence and copyright notices inside vendored third-party files MUST be kept, including when
  the files are cut down, minified or converted.
- When an asset or dependency is removed, its credit MUST be removed in the same change.
- Statements on the About page about the site's behaviour (e.g. cookie use) MUST be updated in
  the same change that alters that behaviour.

**Rationale**: AGPL §13 requires offering source to network users, and attribution licences
require visible credit. Keeping all of this on one page, maintained alongside each change, keeps
the site compliant without separate audits.

## Technology & Deployment Constraints

- **Runtime image**: The app MUST ship as a multi-stage Docker image built with uv (official
  `ghcr.io/astral-sh/uv` image or installer), installing from `uv.lock` with `--frozen`. The
  runtime stage MUST run as a non-root user and expose a health-check endpoint used by the
  Docker `HEALTHCHECK` and Compose `depends_on: service_healthy`.
- **Reverse proxy & TLS**: Caddy MUST front the application via Docker Compose and MUST obtain
  and renew certificates automatically from Let's Encrypt (ACME) for the configured domain.
  Caddy MUST redirect HTTP to HTTPS and send an HSTS header. Certificate data MUST be persisted
  in a named volume to avoid ACME rate limits. The app container MUST NOT publish ports
  directly to the host.
- **Configuration**: Environment-specific values (domain, ACME contact email, log level) MUST be
  supplied via environment variables / `.env`, never hard-coded. Secrets MUST NOT be committed.
- **Pinning**: Base images MUST be pinned by version and digest; GitHub Actions by major
  version or SHA. Dependabot (or equivalent) MUST be configured for `uv`, Docker and GitHub
  Actions updates.

## Development Workflow & Quality Gates

All of the following MUST pass locally before merge and MUST run in GitHub Actions on every
push and pull request to the default branch (using `astral-sh/setup-uv`):

1. `uv lock --check` — lockfile is in sync with `pyproject.toml`.
2. `uv run ruff format --check` (or `uv format --check`) — formatting.
3. `uv run ruff check` — linting.
4. `uv run ty check` — type checking.
5. `uv run pytest` — unit, integration and Playwright tests (browsers installed via
   `uv run playwright install --with-deps`), with test results reported in CI.
6. Docker image build succeeds for the runtime target.

- Changes MUST be made on feature branches and merged to the default branch via pull request.
- Commits SHOULD follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:` ...).
- pre-commit hooks for Ruff and ty are RECOMMENDED to catch failures before CI.

## Governance

- This constitution supersedes other practices for this repository. Feature specs, plans and
  tasks MUST be checked against it; violations MUST be resolved or explicitly justified in the
  plan's complexity tracking.
- Amendments MUST be made via pull request that updates this file, states the rationale and
  bumps the version per semantic versioning:
  - **MAJOR**: removal or incompatible redefinition of a principle or governance rule.
  - **MINOR**: a new principle or section, or materially expanded guidance.
  - **PATCH**: clarifications, wording and typo fixes.
- Code review MUST verify compliance with the Core Principles and Quality Gates. This includes
  checking that any added or removed third-party asset or dependency is reflected in the About
  page's Credits section. `README.md`
  MUST be kept current with build, test and deployment instructions.

**Version**: 1.0.1 | **Ratified**: 2026-11-12 | **Last Amended**: 2026-11-12
