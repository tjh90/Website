# Contract: HTTP Routes

The application serves on port 8000. Every response carries the common headers below and **no**
`Set-Cookie` header.

## Common response headers

| Header | Value |
|--------|-------|
| `Content-Security-Policy` | `default-src 'self'; img-src 'self'; style-src 'self'; script-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

The reverse proxy adds these (they are not tested against the app itself):

- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- HTTP → HTTPS `308` redirect

## Routes

| Method | Path | Status | Content-Type | Body |
|--------|------|--------|--------------|------|
| GET, HEAD | `/` | 200 | `text/html; charset=utf-8` | Home page (see [page-layout.md](page-layout.md)) |
| GET, HEAD | `/about` | 200 | `text/html; charset=utf-8` | About page |
| GET | `/healthz` | 200 | `application/json` | `{"status": "ok"}` |
| GET | `/static/{path}` | 200 / 404 | by file type | Static assets (CSS, images) |
| GET | `/favicon.ico` | 200 | `image/vnd.microsoft.icon` | Favicon |
| GET | any other path | 404 | `text/html; charset=utf-8` | "Page not found" page with the full layout |

## Notes

- `/docs`, `/redoc` and `/openapi.json` are **disabled**, so they return the 404 page.
- A trailing slash on `/about/` redirects to `/about` (FastAPI default `307`).
- `/healthz` is for the Docker `HEALTHCHECK` and Compose `service_healthy`. It is not linked from
  any page.
- `HEAD` requests to the HTML pages return the same status and headers as `GET`, with no body.
