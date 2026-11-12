# Data Model: Home Page, Navigation, About Page and CI

There is no persistent storage. The entities below are immutable, in-memory domain values defined
in `src/website/content.py` and `src/website/config.py`. They are the single source of truth for
templates and tests.

## Page

An addressable page that appears in the navigation.

| Field | Type | Rules |
|-------|------|-------|
| `name` | `str` | Route name used with `url_for`; unique; `snake_case` |
| `path` | `str` | Starts with `/`; unique |
| `title` | `str` | Shown in the header `<h1>` and the browser tab |
| `nav_label` | `str` | Text of the drawer link |

**Instances (navigation order)**:

| name | path | title | nav_label |
|------|------|-------|-----------|
| `home` | `/` | Tim's Page | Home |
| `about` | `/about` | About | About |

The 404 page is **not** a `Page` (it has no nav entry). It uses the title "Page not found".

**Browser tab title rule**: Home → `Tim's Page`; any other page → `{title} · Tim's Page`.

## ExternalLink

A link shown on the home page.

| Field | Type | Rules |
|-------|------|-------|
| `text` | `str` | Visible link text; unique |
| `url` | `str` | Absolute `https://` URL |
| `icon` | `Icon` (enum) | One of `GITHUB`, `BOOK`, `FILE_LINES` |

**Instances (display order)**:

| text | url | icon |
|------|-----|------|
| GitHub | `https://www.github.com/tjh90` | `GITHUB` |
| PhD Thesis | `https://eprints.soton.ac.uk/404274/` | `BOOK` |
| Paper | `https://ieeexplore.ieee.org/document/7029130` | `FILE_LINES` |

## Icon

An enum mapping to an SVG partial in `templates/icons/`: `GITHUB → github.svg`,
`BOOK → book.svg`, `FILE_LINES → file-lines.svg`, `BARS → bars.svg`. Every partial MUST keep its
Font Awesome licence comment (FR-016b).

## Credit

A third-party work credited on the About page (constitution VI).

| Field | Type | Rules |
|-------|------|-------|
| `work` | `str` | Name of the work |
| `author` | `str` | Author or owner |
| `work_url` | `str \| None` | Link to the work or its project, if any |
| `licence` | `str` | Licence name, e.g. "CC BY 4.0", "Public domain" |
| `licence_url` | `str \| None` | Link to the licence text; `None` for the public domain |

**Instances**:

| work | author | work_url | licence | licence_url |
|------|--------|----------|---------|-------------|
| Font Awesome Free icons | Fonticons, Inc. | `https://fontawesome.com` | CC BY 4.0 | `https://creativecommons.org/licenses/by/4.0/` |
| Lady's Cove (1897) | Alfred Sisley | `None` | Public domain | `None` |

## Settings

Runtime configuration (pydantic-settings `BaseSettings`, env prefix `WEBSITE_`).

| Field | Env var | Type | Default | Rules |
|-------|---------|------|---------|-------|
| `revision` | `WEBSITE_REVISION` | `str \| None` | `None` | Empty → `None`. Must match `^[0-9a-f]{7,40}$` (case-insensitive, normalised to lower case); otherwise a warning is logged and the value is treated as `None` |
| `repository_url` | `WEBSITE_REPOSITORY_URL` | `HttpUrl` | `https://github.com/tjh90/website` | Public source repository |

## BuildInfo

Derived from `Settings` for display on the About page. It is the only route by which templates
reach configuration values.

| Field | Type | Derivation |
|-------|------|------------|
| `repository_url` | `str` | `str(Settings.repository_url)` with any trailing `/` removed |
| `revision` | `str \| None` | `Settings.revision` |
| `short_revision` | `str \| None` | First 7 characters of `revision` |
| `revision_url` | `str \| None` | `{repository_url}/tree/{revision}` |

**State**: There are only two cases, revision known or unknown. When it is unknown, the About page
leaves out the revision line but still shows the repository link and licence.

## Licence statement (constants)

| Constant | Value |
|----------|-------|
| `LICENCE_NAME` | GNU Affero General Public License v3.0 |
| `LICENCE_URL` | `https://www.gnu.org/licenses/agpl-3.0.html` |
| `COOKIE_STATEMENT` | "This site does not use cookies." |
