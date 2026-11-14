# Feature Specification: Home Page, Navigation, About Page and CI

**Feature Branch**: `rewrite` (spec-kit feature id `001-home-page-and-ci`)

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Can we create the home page of the new website rewrite, using the impl
currently in main as the reference. As part of this feature, I would like to include the nav bar,
with a separate "About" page that contains the link to the website source so that we are compliant
with AGPL. Also include CI configs etc."

## Reference Implementation

The existing site on the `main` branch is the behavioural reference for this feature. Relevant
behaviour carried forward:

- **Home page** (`/`): page title "Tim's Page"; a "Links:" heading followed by three external links,
  each preceded by an icon and opening in a new tab:
  - "GitHub" (GitHub brand icon) → `https://www.github.com/tjh90`
  - "PhD Thesis" (book icon) → `https://eprints.soton.ac.uk/404274/`
  - "Paper" (document icon) → `https://ieeexplore.ieee.org/document/7029130`
  - Alongside the links, the image "Sisley - Lady's Cove (1897)" (with that alt text).
- **Site chrome**: a coloured header bar showing the current page's title, and navigation
  (a collapsible drawer on `main`) listing the site's pages, closing after a page is chosen.
  A dark-mode toggle sits in the navigation.
- **Privacy page** (`/privacy`): describes the cookies the site uses.
- **Tests on `main`** covering the above: link text/targets, links resolve, links open in a new
  tab, every page loads, navigation reaches each page, header title matches the page, navigation
  works on a mobile viewport, and dark-mode toggling.

Out of scope for this feature (to be specified separately):

- Anascramble.
- Dark mode. A future feature will add a theme that follows the system preference by default,
  plus a manual toggle remembered in a cookie (decided 2026-11-12; superseded 2026-11-14 by
  feature 002, which stores nothing and sets no cookies).
- The Privacy page. It existed only because the old framework needed cookies; instead, the About
  page states that the site uses no cookies.

## Clarifications

### Session 2026-11-12

- Q: Dark mode behaviour? → A: Follow the system preference with a manual toggle remembered in a
  cookie, deferred to a future feature to keep this one focused.
- Q: Navigation style? → A: A side drawer opened by a hamburger button on all screen sizes, as on
  the reference site.
- Q: Include a Privacy page? → A: No. The About page states that no cookies are used.
- Q: How should Font Awesome be credited? → A: Keep the licence comments in every shipped Font
  Awesome file, and also add a Credits section on the About page (Font Awesome Free under CC BY
  4.0, plus a courtesy credit for the public-domain painting).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visitor views the home page (Priority: P1)

A visitor opens the site's root address and sees the owner's landing page: a list of links to the
owner's GitHub profile, PhD thesis and published paper, each with a recognisable icon, alongside a
painting.

**Why this priority**: The home page is the site's core purpose; without it there is nothing to
navigate to.

**Independent Test**: Load `/` and verify the title, the three links (text, destination, icon,
new-tab behaviour) and the image with its alt text are present.

**Acceptance Scenarios**:

1. **Given** the site is running, **When** a visitor requests `/`, **Then** the page loads
   successfully and its title is "Tim's Page".
2. **Given** the home page is displayed, **When** the visitor looks at the "Links:" section,
   **Then** they see "GitHub", "PhD Thesis" and "Paper" links, each with its icon, pointing to the
   destinations listed in the Reference Implementation.
3. **Given** the home page is displayed, **When** the visitor clicks any of the three links,
   **Then** the destination opens in a new tab and the site remains open in the original tab.
4. **Given** the home page is displayed, **When** the visitor views it, **Then** the
   "Sisley - Lady's Cove (1897)" image is shown with that text as its alternative text.

---

### User Story 2 - Visitor navigates between pages (Priority: P1)

From any page, a visitor opens the navigation drawer with the menu button in the header and moves
to any other page of the site; the header always shows which page they are on. This works on both
desktop and phone-sized screens.

**Why this priority**: Navigation is shared by every current and future page and is required to
reach the About page.

**Independent Test**: From each page, use the navigation to reach every other page and check the
resulting address and header title, on both a desktop and a 375×812 viewport.

**Acceptance Scenarios**:

1. **Given** any page is displayed, **When** the visitor first sees it, **Then** the navigation
   drawer is closed and a menu button is visible in the header.
2. **Given** the drawer is closed, **When** the visitor activates the menu button (by mouse,
   touch or keyboard), **Then** the drawer opens and lists every page; activating the button again
   closes it.
3. **Given** the drawer is open, **When** the visitor selects a navigation item, **Then** they
   are taken to that page's address and the drawer is closed on the new page.
4. **Given** any page is displayed, **When** the visitor views the header, **Then** it shows the
   current page's title ("Tim's Page" for Home, "About" for About).
5. **Given** a phone-sized viewport (375×812), **When** the visitor opens the drawer and
   selects a page, **Then** they reach that page and the drawer no longer obscures the content.
6. **Given** JavaScript is disabled in the browser, **When** the visitor uses the drawer,
   **Then** it still opens and closes and every page is reachable.
7. **Given** the drawer is open, **When** the visitor views it, **Then** the item for the
   current page is shown as current, both visually and to assistive technology.

---

### User Story 3 - Visitor finds the site's source code (Priority: P1)

A visitor opens the About page and finds a link to the complete source code of the website they are
using, along with the licence it is published under, satisfying the AGPL obligation to offer source
to network users.

**Why this priority**: Licence compliance is a legal obligation from the moment the site is
publicly deployed.

**Independent Test**: Navigate to the About page and verify the source link, licence name and
version reference are present and the link resolves.

**Acceptance Scenarios**:

1. **Given** any page, **When** the visitor selects "About" in the navigation, **Then** the About
   page loads at `/about`.
2. **Given** the About page is displayed, **When** the visitor looks for the source, **Then** they
   see a link to the public source repository (`https://github.com/tjh90/website`) and a statement
   that the site is licensed under the GNU Affero General Public License v3.0.
3. **Given** the deployed site was built from a specific revision, **When** the visitor views the
   About page, **Then** they see that revision identifier, linked to the corresponding source
   revision in the repository.
4. **Given** the About page is displayed, **When** the visitor clicks the source link, **Then** the
   repository opens in a new tab.
5. **Given** the About page is displayed, **When** the visitor reads it, **Then** it states that
   the site does not use cookies.
6. **Given** the About page is displayed, **When** the visitor views the Credits section, **Then**
   it credits Font Awesome Free with a link to its licence (CC BY 4.0), and credits the painting
   as "Alfred Sisley, Lady's Cove (1897), public domain".

---

### User Story 4 - Maintainer gets automated quality checks and a deployable build (Priority: P1)

When the maintainer pushes a change or opens a pull request, automated checks verify formatting,
linting, typing, the lockfile, all tests (including browser tests) and the deployable container
image, so broken changes cannot be merged unnoticed. Dependency updates are proposed automatically.
The site can be deployed behind a reverse proxy that obtains and renews HTTPS certificates
automatically.

**Why this priority**: The constitution's quality gates apply from the first change; without them
nothing in this feature can be verified or deployed.

**Independent Test**: Open a pull request with a deliberate formatting error and a failing test and
confirm the checks fail; fix them and confirm the checks pass and test results are reported.
Deploy with the provided configuration on a host with a public domain and confirm the site is served
over HTTPS with a valid certificate and HTTP redirects to HTTPS.

**Acceptance Scenarios**:

1. **Given** a push or pull request to the default branch, **When** the checks run, **Then** each
   quality gate in the constitution runs and the overall result is reported on the change.
2. **Given** any quality gate fails, **When** the checks complete, **Then** the change is marked
   as failing and the failing gate is identifiable from the report.
3. **Given** the checks have run, **When** the maintainer views the change, **Then** a per-test
   results report is available.
4. **Given** a new version of a dependency, base image or CI action is published, **When** the
   weekly update scan runs, **Then** an update proposal is opened automatically.
5. **Given** the deployment configuration and a configured public domain, **When** the site is
   started, **Then** it is reachable over HTTPS with a publicly trusted certificate that renews
   automatically, HTTP requests redirect to HTTPS, and HSTS is sent.
6. **Given** the application container is running, **When** its health endpoint is checked,
   **Then** it reports healthy, and the proxy only starts routing traffic once it does.

---

### Edge Cases

- **Unknown address**: a request for a page that does not exist returns a "page not found" page
  (HTTP 404) that still shows the header and navigation so the visitor can recover. (The reference
  returns 200 for unknown routes; this is intentionally corrected.)
- **External link down**: if an external destination is temporarily unavailable, the site still
  loads; link availability is checked by a separately runnable test that does not block merges on
  third-party outages.
- **Image fails to load**: the alt text is shown and the page layout remains intact.
- **Narrow screens**: at 320px width no horizontal scrolling occurs and the links and image stack
  vertically.
- **No revision information at build time** (e.g. local development): the About page still links
  to the repository and states the licence, omitting the revision.
- **JavaScript disabled or blocked**: all pages and navigation remain usable.

## Requirements *(mandatory)*

### Functional Requirements

#### Home page

- **FR-001**: The site MUST serve the home page at `/` with the page title "Tim's Page".
- **FR-002**: The home page MUST display a "Links:" heading followed by the GitHub, PhD Thesis and
  Paper links with the exact text and destinations listed in the Reference Implementation.
- **FR-003**: Each home page link MUST be preceded by its icon (GitHub brand, book, document) and
  icons MUST be decorative (hidden from assistive technology) since the link text is descriptive.
- **FR-004**: External links MUST open in a new tab and MUST NOT give the destination page access
  to the opening page.
- **FR-005**: The home page MUST display the "Sisley - Lady's Cove (1897)" image with that alt text,
  laid out beside the links on wide screens and below them on narrow screens.

#### Site layout and navigation

- **FR-006**: Every page MUST share a common layout consisting of a coloured header bar containing
  a menu button and the current page title, and a navigation drawer (behaviour per FR-008) listing
  all pages in this feature (Home, About).
- **FR-007**: Each navigation item MUST link to its page's address; the current page MUST be
  indicated visually and to assistive technology.
- **FR-008**: Navigation MUST be a side drawer opened and closed by the menu button on all
  screen sizes. The drawer MUST be closed when a page first loads, including after navigating.
- **FR-009**: The menu button MUST be keyboard-operable and MUST expose whether the drawer is open
  to assistive technology. While the drawer is open, it MUST NOT permanently obscure the page:
  activating the menu button again MUST close it.
- **FR-010**: Navigation (including opening and closing the drawer) and all page content MUST
  function without JavaScript.
- **FR-011**: The browser tab title of each page MUST include the page title.
- **FR-012**: Requests for unknown addresses MUST return a 404 page that uses the common layout.

#### About page

- **FR-013**: The site MUST serve an About page at `/about` with the page title "About", reachable
  from the navigation on every page.
- **FR-014**: The About page MUST state that the site is free software licensed under the GNU
  Affero General Public License v3.0, link to the licence text, and link to the public source
  repository `https://github.com/tjh90/website`.
- **FR-015**: When the build has revision information, the About page MUST display the revision
  identifier of the running site, linked to that revision in the source repository.
- **FR-016**: The About page MUST state that the site does not use cookies, and the site MUST NOT
  set any cookies.
- **FR-016a**: The About page MUST include a Credits section that credits Font Awesome Free
  (linked to `https://fontawesome.com`) under CC BY 4.0 (linked to the licence), and credits the
  painting as "Alfred Sisley, Lady's Cove (1897), public domain".
- **FR-016b**: Every Font Awesome file the site ships (stylesheet, font or icon image) MUST keep
  Font Awesome's original licence and attribution comment, including when icons are cut down to
  the subset used.

#### Appearance and accessibility

- **FR-017**: The site MUST use a single light theme in this feature. The colour scheme MUST be
  defined centrally, so that the future dark-mode feature can add a second theme without
  restructuring pages.
- **FR-018**: All pages MUST meet WCAG 2.2 AA for contrast, keyboard operability and landmarks, and
  MUST report no serious or critical automated accessibility violations.
- **FR-019**: All fonts, icons, images and styles MUST be served by the site itself (no third-party
  CDNs).

#### Quality gates, CI and deployment

- **FR-020**: Every push and pull request to the default branch MUST automatically run all quality
  gates defined in the constitution (lockfile check, formatting, linting, type checking, all tests
  including browser tests, container image build) and report results on the change.
- **FR-021**: CI MUST publish a per-test results report.
- **FR-022**: Automated weekly update proposals MUST be configured for application dependencies,
  container base images and CI actions.
- **FR-023**: The repository MUST provide a container image definition for the site that runs as a
  non-root user and exposes a health check.
- **FR-024**: The repository MUST provide a deployment configuration that runs the site behind a
  reverse proxy which automatically obtains and renews a publicly trusted certificate for a
  configurable domain, redirects HTTP to HTTPS, sends HSTS, persists certificate data
  across restarts, and only routes traffic once the site reports healthy.
- **FR-025**: Domain name, certificate contact email and similar environment-specific values MUST
  be configurable without code changes, with an example configuration file committed and real
  values excluded from version control.
- **FR-026**: The README MUST document prerequisites, how to run the site locally, how to run each
  quality gate, and how to deploy.

### Key Entities

- **Page**: an addressable page of the site with an address, a page title (shown in the header and
  browser tab) and a navigation label. Pages in this feature: Home, About.
- **External Link**: text, destination address and icon, displayed on the home page.
- **Build Information**: the source revision the running site was built from, used by the About
  page; may be absent in development.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the reference site's home-page and navigation behaviours listed in the
  Reference Implementation (excluding the out-of-scope items) are covered by passing automated
  tests.
- **SC-002**: A visitor can reach the source code link from any page in at most 2 clicks.
- **SC-003**: Every page is fully usable (all content visible, all pages reachable) with JavaScript
  disabled and at viewport widths from 320px to 1920px without horizontal scrolling.
- **SC-004**: Every page loads and renders in under 1 second on a typical broadband connection,
  with a total page weight under 500 KB for the home page (image included).
- **SC-005**: Automated accessibility scans report zero serious or critical violations on every
  page, with the drawer both open and closed.
- **SC-006**: A change introducing a formatting, lint, type or test failure is flagged as failing
  by CI in 100% of cases, and a clean change completes all checks in under 10 minutes.
- **SC-007**: A fresh deployment on a host with a public domain serves the site over HTTPS with a
  valid certificate within 5 minutes of start-up, with no manual certificate steps.

## Assumptions

- The navigation in this feature lists only the pages that exist after this feature (Home and
  About). Anascramble's own feature adds it to the navigation.
- The canonical source repository is `https://github.com/tjh90/website` (the repository's
  `origin`), which is public.
- Linking to the public repository plus the running revision satisfies the AGPL §13 requirement to
  offer Corresponding Source to network users.
- The painting image and Font Awesome icons can be reused from the reference implementation
  (the painting is public domain; Font Awesome Free is CC BY 4.0 / SIL OFL 1.1 / MIT, all
  compatible with AGPL). Only the three icons used need be shipped; attribution is handled by
  FR-016a and FR-016b.
- The decorative "Rock Salt" web font on the reference site is used only by Anascramble and is out
  of scope.
- The site has no user accounts, forms or server-side state in this feature, so it needs no
  session or CSRF cookies (unlike the reference). Feature 002 (dark mode) also sets no cookies, so
  the About page's cookie statement stays accurate.
- The external-link reachability test runs separately (e.g. scheduled or on demand) rather than as a
  merge-blocking gate, to avoid failures caused by third-party outages.
- CI runs on GitHub Actions, as on the reference repository; deployment uses Docker Compose with
  Caddy obtaining certificates from Let's Encrypt, per the constitution.
