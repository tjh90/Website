# Quickstart & Validation: Home Page, Navigation, About Page and CI

This guide runs the site and proves the feature works. For details, see
[contracts/http-routes.md](contracts/http-routes.md), [contracts/page-layout.md](contracts/page-layout.md)
and [data-model.md](data-model.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (latest)
- Docker with Compose v2 (for the deployment checks only)
- Git

## 1. Install and run locally

```bash
uv sync
```

```bash
uv run playwright install chromium
```

```bash
uv run uvicorn website.app:create_app --factory --reload
```

Open <http://127.0.0.1:8000>.

**Expected**:

- `/` shows the "Tim's Page" header, three icon links and the painting.
- The "Menu" button opens a drawer with Home and About.
- `/about` shows the licence, the source link and the cookie statement, plus Credits. There is no
  revision line in local dev unless `WEBSITE_REVISION` is set.
- `/nope` shows "Page not found" with status 404.

## 2. Run the quality gates (same as CI)

```bash
uv lock --check
```

```bash
uv run ruff format --check
```

```bash
uv run ruff check
```

```bash
uv run ty check
```

```bash
uv run pytest
```

**Expected**: all commands exit 0. `pytest` runs the unit, integration and e2e tests (Chromium,
headless). The `external` tests are deselected.

Optional, to check that the real external links are reachable:

```bash
uv run pytest -m external
```

## 3. Validate scenarios manually

| Scenario | Steps | Expected |
|----------|-------|----------|
| US1 links | On `/`, click "PhD Thesis" | Opens in a new tab; the site stays in the original tab |
| US2 drawer | Click "Menu", then "About" | Arrives at `/about`; header shows "About"; drawer closed |
| US2 keyboard | Tab to "Menu" and press Enter, then Esc | Drawer opens, then closes; focus returns to the button |
| US2 no-JS | Disable JavaScript in DevTools and repeat the drawer scenario | Same result |
| US2 mobile | DevTools device mode 375×812 | Drawer usable; no horizontal scroll; links stack above the painting |
| US3 revision | Run the server with `WEBSITE_REVISION=$(git rev-parse HEAD)` | The About page shows a 7-character revision linking to that commit |
| FR-016 | DevTools → Application → Cookies | None set |

## 4. Container and deployment

Build and run locally (Caddy uses its internal CA for `localhost`):

```bash
cp build/.env.example build/.env
```

```bash
docker compose -f build/compose.yml build --build-arg WEBSITE_REVISION=$(git rev-parse HEAD)
```

```bash
docker compose -f build/compose.yml up -d
```

**Expected**:

- `docker compose -f build/compose.yml ps` shows `website` as `healthy` before `caddy` starts.
- `https://localhost` serves the site (after you trust Caddy's local CA, or accept the warning).
- `http://localhost` redirects to HTTPS with a 308.
- The response includes `Strict-Transport-Security`.
- The `website` container publishes no host ports.

Production: set `SITE_DOMAIN` and `ACME_EMAIL` in `build/.env` on a host whose DNS points at it,
with ports 80 and 443 open. Within about 5 minutes (SC-007), Caddy obtains a Let's Encrypt
certificate. To do a trial run without hitting rate limits, first set
`ACME_CA=https://acme-staging-v02.api.letsencrypt.org/directory`.

## 5. CI

Push a branch and open a PR against `main`. **Expected**:

- The `checks`, `test` and `docker` jobs run, and a "pytest results" check lists each test.
- Breaking formatting or a test makes the matching job fail, with annotations.
