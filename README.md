# Website

[![CI](https://github.com/tjh90/website/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tjh90/website/actions/workflows/ci.yml)

Simple personal website, served by FastAPI with server-rendered Jinja2 templates.

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Landing page with external links (GitHub, PhD thesis, published paper) and a painting |
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

Check that the external links on the home page are reachable (run in CI on every PR as a non-blocking job):

```bash
uv run pytest -m external
```

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
