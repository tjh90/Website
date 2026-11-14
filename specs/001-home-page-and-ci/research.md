# Research: Home Page, Navigation, About Page and CI

> **Implementation notes (2026-11-12)**: These decisions were adjusted during implementation.
>
> - **R1**: The drawer opens below the header (`top: var(--header-height)`), so the Menu button
>   stays clickable to close it again.
> - **R3**: Font Awesome Free 7.3.1 puts its licence comment inside `<svg>`. The comment is moved
>   to the top of each partial unchanged, so tests can check it.
> - **R8**: The live server binds its own socket and passes it to `Server.run(sockets=...)`.
>   `httpx2` replaces `httpx`, which Starlette's test client now deprecates.
> - **R10**: External-link tests use `httpx2`.
> - **R14**: Current action majors are `actions/checkout@v7` and `astral-sh/setup-uv@v10`.
> - **Testing**: On machines where the downloaded Chromium can't run (antivirus or TLS
>   interception), the browser tests run on installed Edge with `--browser-channel msedge`. CI
>   uses Playwright's Chromium. The new-tab tests accept `www.`-less redirects, as the reference
>   tests did, because Edge doesn't route `noopener` popups through `context.route`.
> - **R13**: `ACME_EMAIL` is required (`${ACME_EMAIL:?…}` in Compose). Caddy rejects an empty
>   `email` directive, so an unset value made Caddy crash-loop.
> - **Build backend**: `uv_build>=0.13.8,<0.14.0`, matching the uv in the pinned builder image.
> - **FR-009 test**: Playwright's ARIA snapshot only reads `aria-expanded` attributes, so the
>   button's native expanded state is read from the browser accessibility tree over CDP.

All Technical Context items were resolved; no `NEEDS CLARIFICATION` remains. Exact package and
image versions are resolved at implementation time (`uv add`, image digests) and then kept
current by Dependabot.

## R1. Drawer navigation without JavaScript

- **Decision**: A `<button popovertarget="nav-drawer">` in the header toggles a
  `<nav id="nav-drawer" popover>` that CSS styles as a fixed left-hand drawer.
- **Rationale**: The Popover API is Baseline "widely available". It gives us, with no JS:
  - toggling from the button;
  - the button's expanded/collapsed state exposed to assistive technology;
  - closing on Esc or a click outside (light dismiss);
  - rendering in the top layer, so no z-index fights.

  Every navigation is a full page load, so the drawer is naturally closed on the new page
  (FR-008). It needs no cookie or server state.
- **Alternatives considered**:
  - `<details>`/`<summary>`: also JS-free, but it has no light dismiss, it pushes content around
    unless absolutely positioned, and it is announced as a disclosure widget rather than a menu
    button.
  - The CSS "checkbox hack": poor accessibility semantics.
  - HTMX: needs JS to be enabled, and offers nothing here because no server interaction is
    involved.
- **Degradation**: In a browser without popover support, the `[popover]` element renders inline
  as a normal list of links, so every page stays reachable (FR-010).

## R2. No-JS verification in tests

- **Decision**: The E2E navigation tests also run in a Playwright context created with
  `java_script_enabled=False`.
- **Rationale**: This proves FR-010 and SC-003 directly, because popover toggling is native
  browser behaviour.

## R3. Icons and Font Awesome licensing

- **Decision**: Ship only the needed icons (`github`, `book`, `file-lines`, `bars`) as inline SVG
  partials copied from the latest Font Awesome Free 7.x release. Each SVG keeps its
  `<!--! Font Awesome Free … License … -->` comment, which Jinja passes into the HTML unchanged.
  Icons get `aria-hidden="true"` and `focusable="false"`, and use `fill="currentColor"`.
- **Rationale**: This removes the ~1 MB webfont and CSS bundle the reference site shipped, needs
  no extra HTTP requests, and colours icons with CSS. It also meets FR-003, FR-016b and the
  page-weight target (SC-004). Font Awesome's own guidance is that the embedded comment counts as
  attribution, and the About page Credits section adds a visible credit (constitution VI).
- **Alternatives considered**:
  - Vendoring the full webfont and CSS: heavy, and needs a font-loading CSP allowance.
  - An icon-font subset tool: adds a build step for 4 icons.

## R4. Build revision on the About page

- **Decision**: `Settings.revision: str | None`, read from the `WEBSITE_REVISION` env var.
  - It is validated as a 7–40 character hex string; an invalid value is ignored with a logged
    warning.
  - The Dockerfile takes `ARG WEBSITE_REVISION` and sets `ENV WEBSITE_REVISION=$WEBSITE_REVISION`.
  - CI passes `${{ github.sha }}`; local `docker compose build` can pass
    `--build-arg WEBSITE_REVISION=$(git rev-parse HEAD)`.
  - The About page shows the first 7 characters, linked to
    `https://github.com/tjh90/website/tree/<full sha>`.
- **Rationale**: Baking the value in at build time ties it to the code actually running (AGPL
  §13). An env var keeps it out of code, as the constitution's configuration rule requires. When
  it is absent (local dev), the revision line is hidden (spec edge case).
- **Alternatives considered**:
  - Reading `.git` at runtime: `.git` is not in the image.
  - Generating a `_version.py` at build time: more moving parts.
  - `setuptools-scm`/`hatch-vcs`: overkill for a single value.

## R5. App structure and configuration

- **Decision**:
  - An app factory `create_app(settings: Settings | None = None) -> FastAPI` builds the app.
  - The page registry in `content.py` is the single source for routes, titles and nav labels, so
    the templates and tests share the same constants (as `HomeView.TITLE` did on the reference
    site).
  - `Jinja2Templates` gets a context processor that injects `nav_pages`, `site_title`,
    `tab_title` and `build_info`. `BuildInfo` carries the tidied `repository_url` as well as the
    revision, so templates never need the raw `Settings`. Each template sets `current_page`.
  - The interactive API docs (`/docs`, `/redoc`, `/openapi.json`) are disabled
    (`docs_url=None`, etc.).
- **Rationale**: The factory lets tests inject settings, for example a revision. API docs are not
  part of the site and would expand its attack surface.

## R6. 404 handling

- **Decision**: An exception handler for `StarletteHTTPException` with status 404 renders
  `not_found.html` (title "Page not found") with the full layout and returns status 404. Other
  HTTP errors keep FastAPI's default behaviour.
- **Rationale**: This satisfies the spec's edge case and FR-012.

## R7. Security headers and no cookies

- **Decision**: A small pure-ASGI middleware in `app.py` adds these headers to every response:
  - `Content-Security-Policy: default-src 'self'; img-src 'self'; style-src 'self'; script-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`

  HSTS is added by Caddy, because it only makes sense over TLS. Integration tests assert that no
  response carries `Set-Cookie` (FR-016).
- **Rationale**: The site has no scripts, so `script-src 'none'` is possible. Setting the headers
  in the app keeps them testable without Caddy.
- **Alternatives considered**:
  - Setting the headers in Caddy only: they couldn't be tested in CI.
  - A third-party security-headers package: unnecessary for three static headers.

## R8. Live server for Playwright

- **Decision**: A session-scoped fixture starts `uvicorn.Server` in a background thread on a free
  port (port 0, then reads the bound socket). It waits for `/healthz`, then overrides
  pytest-playwright's `base_url` fixture. The tests use the `page` and `browser` fixtures that
  pytest-playwright provides.
- **Rationale**: This runs in-process (fast, works on Windows and in CI) and matches the
  reference site's approach of booting the real app on a random port.
- **Alternatives considered**: `pytest-xprocess` or subprocess management: slower and more brittle
  on Windows.

## R9. Accessibility checks

- **Decision**: `axe-playwright-python` (`Axe().run(page)`) runs on `/`, `/about` and a 404 page,
  with the drawer both closed and open. The test fails on any violation with impact `serious` or
  `critical` (SC-005).
- **Rationale**: This package is the maintained Python binding for axe-core with Playwright, and
  the constitution recommends axe.

## R10. External link checks

- **Decision**: The external link tests are marked `@pytest.mark.external` and deselected by
  default (`addopts = "-m 'not external'"`). They send HEAD requests (falling back to GET) to each
  home-page link with a 15 s timeout and expect a 2xx/3xx status. A separate workflow,
  `external-links.yml`, runs `pytest -m external` weekly and on `workflow_dispatch`.
- **Rationale**: This follows the spec assumption that third-party outages must not block merges,
  while keeping the reference site's `linksAreValid` coverage. It uses `httpx`, which already
  comes with FastAPI's test client, so no new dependency is needed.

## R11. Lint, format and type-check configuration

- **Decision** (all in `pyproject.toml`):
  - **Ruff**: `target-version = "py314"`, `line-length = 100`.
  - **Lint rules**: `select = ["E","W","F","I","N","D","UP","B","SIM","ANN","RUF","S","PT","PTH"]`
    with `pydocstyle.convention = "google"`. The `S` rules are relaxed for `tests/` (`S101`
    assert).
  - **ty**: `[tool.ty]` checks `src` and `tests`, with all rules at their default (error) level.
  - **pytest**: `--strict-markers`, the `external` marker, and `testpaths = ["tests"]`.
- **Rationale**: These are the rules the constitution mandates, plus `S` (bandit), `PT` (pytest
  style) and `PTH` (pathlib), which are low-noise and useful. A 100-character line limit matches
  the repository's Markdown style.
- **Format gate**: `uv run ruff format --check`. Ruff is a pinned dev dependency, so local runs
  and CI use the same version from `uv.lock`.

## R12. Container image

- **Decision**: A multi-stage `build/Dockerfile`:
  1. **builder**: `ghcr.io/astral-sh/uv:python3.14-trixie-slim` (pinned by digest).
     - Sets `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy` and `UV_PYTHON_DOWNLOADS=0`.
     - Runs `uv sync --locked --no-dev --no-install-project` with cache mounts (dependency layer),
       then copies the source and runs `uv sync --locked --no-dev --no-editable`.
  2. **runtime** (`website-run`): `python:3.14-slim-trixie` (pinned by digest).
     - Copies `/app/.venv` and creates a non-root user `website`.
     - Sets `ENV PATH=/app/.venv/bin:$PATH` and the `WEBSITE_REVISION` ARG/ENV, and exposes 8000.
     - `HEALTHCHECK` runs `python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"`.
     - `CMD ["uvicorn", "website.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]`.
- **Rationale**: This follows Astral's documented Docker pattern. The runtime image has no uv and
  no build tooling. Trusting proxy headers from any IP is safe because the container is reachable
  only on the internal Compose network.
- **Alternatives considered**: A distroless runtime: smaller, but the slim image keeps debugging
  simple and the health check can use Python.

## R13. Reverse proxy and Let's Encrypt

- **Decision**: `build/Caddyfile`:

  ```caddyfile
  {
      email {$ACME_EMAIL}
      acme_ca {$ACME_CA:https://acme-v02.api.letsencrypt.org/directory}
  }
  {$SITE_DOMAIN:localhost} {
      encode zstd gzip
      header Strict-Transport-Security "max-age=31536000; includeSubDomains"
      reverse_proxy website:8000
  }
  ```

  - In `compose.yml`, Caddy is pinned by digest and publishes 80, 443 and 443/udp.
  - The `caddy_data` and `caddy_config` volumes persist certificates.
  - `website` uses `expose: 8000` only, with `depends_on: website: condition: service_healthy`.
  - `.env.example` documents `SITE_DOMAIN`, `ACME_EMAIL` and an optional `ACME_CA` (for example,
    the Let's Encrypt staging URL, for trial deployments that avoid rate limits).
- **Rationale**: Caddy redirects HTTP to HTTPS and renews certificates automatically. Setting
  `acme_ca` explicitly makes Let's Encrypt the issuer, as the user asked, instead of Caddy's
  default mix of Let's Encrypt and ZeroSSL. With `localhost`, Caddy uses its internal CA, so the
  same file works for local trials.
- **Alternatives considered**: Traefik or nginx + certbot: more configuration for the same result.

## R14. CI workflow

- **Decision**: `.github/workflows/ci.yml`, triggered on push and pull_request to `main` (the
  default branch). Actions are pinned by major version (or SHA), and Dependabot keeps them
  current.
  1. **checks**: `actions/checkout`, then `astral-sh/setup-uv` (with caching), then:
     - `uv lock --check`
     - `uv run ruff format --check`
     - `uv run ruff check --output-format=github`
     - `uv run ty check`
  2. **test**: setup-uv, then `uv sync --locked`, then
     `uv run playwright install --with-deps chromium`, then
     `uv run pytest --junitxml=reports/junit.xml`. Then `dorny/test-reporter` (with
     `reporter: java-junit`) publishes the per-test report (FR-021).
  3. **docker**: `docker/setup-buildx-action`, then `docker/build-push-action` with
     `context: .`, `file: build/Dockerfile`, `target: website-run`, `push: false`,
     `build-args: WEBSITE_REVISION=${{ github.sha }}`, and the GHA cache.
- **Rationale**: Running the jobs in parallel keeps a clean run under 10 minutes (SC-006), and
  GitHub annotations make the failing gate easy to identify (US4-2).
- **Permissions**: `contents: read`, plus `checks: write` for the test reporter.

## R15. Dependabot

- **Decision**: `.github/dependabot.yml` sets up weekly updates for:
  - `uv` (directory `/`);
  - `docker` (directory `/build`);
  - `docker-compose` (directory `/build`);
  - `github-actions` (directory `/`).

  Each ecosystem's updates are grouped into one PR.
- **Rationale**: This satisfies FR-022 and the constitution's pinning rule. Dependabot supports
  all four ecosystems natively.

## R16. Images and assets

- **Decision**:
  - Reuse `sisley.jpg` (70 KB) from the reference site, with explicit `width`/`height` to avoid
    layout shift.
  - Re-encode the favicon (160 KB on the reference site) as a small multi-size `.ico`
    (≤ 16 KB).
  - The CSS defines its colours as custom properties on `:root`, ready for the future dark-mode
    feature (FR-017).
  - The header uses the reference site's primary blue (`rgb(64 128 255)`) with white text,
    darkened if needed to reach AA contrast.
- **Rationale**: This meets the page-weight target, keeps the page visually stable, and prepares
  for dark mode without building it now.
