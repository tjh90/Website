# Contract: HTTP changes

This contract extends [feature 001's HTTP routes contract](../../001-home-page-and-ci/contracts/http-routes.md).
Routes and status codes are unchanged.

## New static asset

| Method | Path | Status | Content-Type |
|---|---|---|---|
| GET/HEAD | `/static/js/htmx.min.js` | 200 | `text/javascript` (charset optional) |

## Request variants

Every HTML route (`/`, `/about`, and 404 responses) behaves as follows:

| Request header | Response body difference |
|---|---|
| none (full load) | Full page; `<h1>` without `autofocus` |
| `HX-Request: true` (boosted link or history restore) | Full page; `<h1 tabindex="-1" autofocus>` |

- The response is always a complete HTML document (FR-012), whether the request comes from htmx or
  not.
- HTML responses include `Vary: HX-Request`.

## Response headers

| Header | Value |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'` |
| `Set-Cookie` | never present (FR-016) |
| other security headers | unchanged |
