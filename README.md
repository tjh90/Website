# Website

[![CI](https://github.com/tjh90/website/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tjh90/website/actions/workflows/ci.yml)

Simple personal website, served by FastAPI with server-rendered Jinja2 templates. The theme
follows the visitor's light/dark preference, with a "Dark mode" switch in the navigation drawer;
in-place navigation is provided by a vendored copy of [htmx](https://htmx.org). The site sets no
cookies and stores nothing in the browser.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Landing page with external links (GitHub, PhD thesis, published paper) and a painting |
| `/anascramble` | Anascramble | Anagram solving aid: scrambles letters and tracks a partial solution |
| `/about` | About | Licence, source code link, and running revision, cookie statement and credits |

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Docker with Compose v2 (for deployment only)

## Running locally

Install dependencies:

```bash
uv sync
```

Start the development server (with auto-reload) at <http://127.0.0.1:8000>:

```bash
uv run website
```

Set `WEBSITE_REVISION` to a git SHA to see the revision on the About page.

## Quality checks

These run in CI on every push and pull request to `main`.

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

The browser tests need a Playwright browser. Install Chromium once:

```bash
uv run playwright install chromium
```

If Chromium can't be downloaded or launched on your machine (e.g. because of antivirus or TLS
interception), run the browser tests against an installed Microsoft Edge or Google Chrome
instead:

```bash
uv run pytest --browser-channel msedge
```

Some browser tests (themes, the Dark mode switch, in-place navigation and drawer animations) must
also pass in Firefox, and CI runs them there. Install Firefox once and run them with:

```bash
uv run playwright install firefox
```

```bash
uv run pytest -m firefox --browser firefox
```

Check that the external links on the home page are reachable (run in CI on every PR as a non-blocking job):

```bash
uv run pytest -m external
```

## Vendored htmx

htmx is served from `src/website/static/js/htmx.min.js` (currently 4.0.1) rather than a CDN.
Dependabot cannot update it, so update it by hand:

1. Download the release tarball from the npm registry,
   `https://registry.npmjs.org/htmx.org/-/htmx.org-<version>.tgz`, into an empty temporary
   directory.
2. Check its integrity: the base64-encoded SHA-512 of the `.tgz` must match the `dist.integrity`
   value from `https://registry.npmjs.org/htmx.org/<version>`:

   ```bash
   echo "sha512-$(openssl dgst -sha512 -binary htmx.org-<version>.tgz | base64 -w0)"
   ```

3. Extract `package/dist/htmx.min.js` and replace `src/website/static/js/htmx.min.js` with it,
   unmodified.
4. Update `HTMX_VERSION` in `tests/integration/test_static.py`, read the release notes for
   breaking changes, and run all the quality checks (including the Firefox tests).

## Deploying with Docker

The site runs behind [Caddy](https://caddyserver.com/), which obtains and renews HTTPS
certificates from Let's Encrypt automatically.

1. Point your domain's DNS at the host and open ports 80 and 443.
2. Create the environment file and set `SITE_DOMAIN` and `LETSENCRYPT_EMAIL`:

   ```bash
   cp build/.env.example build/.env
   ```

3. Build and start the site, recording the source revision for the About page:

   ```bash
   WEBSITE_REVISION=$(git rev-parse HEAD) docker compose -f build/compose.yml up -d --build
   ```

To try a deployment without using up Let's Encrypt rate limits, first set
`LETSENCRYPT_CA=https://acme-staging-v02.api.letsencrypt.org/directory` in `build/.env`. With the
default `SITE_DOMAIN=localhost`, Caddy uses its own local certificate authority instead.

Keep the `caddy_data` volume between deployments; it holds the certificates.

## Licence

[GNU Affero General Public License v3.0](LICENSE). Third-party credits are listed on the site's
About page.
