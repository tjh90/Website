# Research: Light and Dark Theme Switching

All Technical Context unknowns are resolved below. Sources: htmx 4.0.1 source (`dist/htmx.js`,
read directly), the htmx 4 docs (four.htmx.org) and the npm registry.

## R1. Reading the device preference

- **Decision**: Use the `prefers-color-scheme` media feature through the CSS `color-scheme`
  property, plus `<meta name="color-scheme" content="light dark">` so the browser paints the canvas
  correctly before the stylesheet loads.
- **Rationale**: This is the only standard, cross-browser way for a site to see the OS/browser
  preference. It works without JavaScript, applies from first paint and updates live when the
  device setting changes (FR-002 to FR-005). `color-scheme` also themes scrollbars and form
  controls (FR-019).
- **Alternatives considered**:
  - `Sec-CH-Prefers-Color-Scheme` client hint for server-side detection: Chromium only, and needs
    `Critical-CH` round trips. Not needed, because CSS does it on the client.
  - Reading the OS setting directly: not possible from a web page.

## R2. Defining two themes

- **Decision**: Rewrite every token in `:root` as `light-dark(<light>, <dark>)`. Set
  `color-scheme: light` on `:root`, and `color-scheme: dark` inside
  `@media (prefers-color-scheme: dark)`. Manual-switch rules (R3) override `color-scheme` only.
- **Rationale**: Changing a single property switches the whole palette and the browser-drawn UI
  together. Feature 001 already routes every colour through tokens (FR-017 of 001), so no page CSS
  changes. `light-dark()` has been Baseline since May 2024.
- **Dark palette (starting values; axe contrast tests are the gate)**:

  | Token | Light | Dark |
  |---|---|---|
  | `--color-bg` | `#fff` | `#121417` |
  | `--color-text` | `#1a1a1a` | `#e6e6e6` |
  | `--color-link` | `#1a4fbf` | `#a8cfff` |
  | `--color-header-bg` | `rgb(64 128 255)` | `rgb(64 128 255)` (brand blue kept, FR-018) |
  | `--color-header-text` | `#fff` | `#fff` |
  | `--color-focus` | `#1a4fbf` | `#a8cfff` |
  | `--color-icon` | `#000` | `#e6e6e6` |
  | `--color-nav-current-bg` | `#1a4fbf` | `#c0e0ff` (reference accent) |
  | `--color-nav-current-text` | `#fff` | `#121417` |
  | `--color-nav-hover-bg` | `#dbe6ff` | `#1f2a44` |

- **Alternatives considered**: a `[data-theme=dark]` attribute block. It needs JavaScript or the
  server to set the attribute, which is not possible here without storage.

## R3. A "Dark mode" switch with a fixed label and accurate state, without JavaScript

- **Problem**: The switch must be On exactly when dark is shown (FR-007), but the server cannot
  know the device preference, and CSS cannot set a checkbox's checked state.
- **Decision**: Render two switches, each an `<input type="checkbox" role="switch">` inside a
  `<label>` reading "Dark mode":
  - `#dark-mode-light-device`, unchecked by default, shown only when the device prefers light (or
    reports nothing);
  - `#dark-mode-dark-device`, `checked` by default, shown only under
    `prefers-color-scheme: dark`.

  The hidden one is `display: none`, so it is removed from the accessibility tree and tab order.
  Rules:

  ```css
  :root:has(#dark-mode-light-device:checked) { color-scheme: dark; }
  @media (prefers-color-scheme: dark) {
    :root:has(#dark-mode-dark-device:not(:checked)) { color-scheme: light; }
  }
  ```

  The `:has()` rule for the light-device switch must be scoped so it does not apply under a dark
  preference, by wrapping it in `@media not (prefers-color-scheme: dark)`.
- **Rationale**: The label never changes, the visible switch's checked state always equals "dark is
  shown", and `role="switch"` makes screen readers announce "Dark mode, switch, on/off". This
  matches the owner's chosen "Dark mode: Off/On". Wrapping the input in its label makes the whole
  row toggle it, as on the reference (FR-009). It is pure HTML and CSS, so it complies with the
  constitution and works without JavaScript (FR-010). `:has()` has been Baseline since Dec 2023.
- **Known limitation**: each switch keeps its own state for the life of the page. Suppose a visitor
  switches under one device preference, the device preference changes (the other switch, at its
  default, takes over, so the site follows the device as FR-004 requires), and then it changes back
  again. The first switch reappears with its earlier state. Resetting it would need JavaScript. The
  spec's FR-004 and edge case are amended to describe this behaviour. It is rare and harmless.
- **Alternatives considered**:
  - A single checkbox meaning "use the other theme": its state would read Off while dark is shown
    for dark-preference visitors. Rejected by the owner (fixed label, accurate state).
  - A single checkbox with CSS-swapped label text: screen readers would still announce the wrong
    state.
  - The Safari-only `switch` attribute: not cross-browser. `role="switch"` plus CSS styling gives
    the same result everywhere.

## R4. In-place navigation library and version

- **Decision**: htmx **4.0.1** (released 2026-11-01, npm `next` tag), vendored at
  `src/website/static/js/htmx.min.js` from the npm tarball. It is verified against the registry
  integrity value
  `sha512-oF7JgXhDW9UXCy/k1ZYFUQgzu/rm19ORWPSPNL91vPluB2PB9+MV55tyQdH/w7o2EAbTYUG5SDW1R60mdkdqGg==`
  and loaded with `<script src="…" defer>` in `<head>`.
- **Rationale**:
  - The constitution names HTMX, requires a vendored, pinned copy and asks for the latest tooling.
    4.x is the current major release, while 2.x stays npm `latest` only for compatibility until
    early 2027.
  - Crucially for FR-016, htmx 4 removed the DOM snapshot history cache: htmx 2 wrote it to
    `localStorage`. On Back/Forward, htmx 4 re-fetches the page from the server with an
    `HX-History-Restore-Request` header and swaps it into `<body>`. The 2.x behaviour is only
    available through the opt-in `hx-history-cache` extension, which will not be loaded.
- **Alternatives considered**:
  - htmx 2.0.11: needs `historyCacheSize: 0` to avoid localStorage and is a superseded major.
  - Cross-document View Transitions alone (`@view-transition { navigation: auto }`): these give
    animation on full page loads but cannot carry the switch state across pages. Rejected.
  - Turbo or Unpoly: not the stack the constitution names.
- **Update process**: Dependabot cannot update vendored files. The README documents the manual
  update steps (download the tarball, verify integrity, replace the file, bump the version in the
  credit and the research notes).

## R5. htmx configuration and markup

- **Decision**:
  - `<body hx-boost:inherited="transition:true">`. htmx 4 makes attribute inheritance opt-in
    (`implicitInheritance: false`), so the `:inherited` suffix is required for links inside
    `<body>` to be boosted. The `transition:true` value turns on View Transitions for boosted swaps.
  - `<meta name="htmx-config" content='{"includeIndicatorCSS":false}'>`: no indicators are used, so
    nothing is injected. The other defaults are kept: `history: true`, `mode: same-origin`.
  - Both switches have stable `id`s and `hx-preserve`.
- **Behaviour confirmed in the 4.0.1 source**:
  - Boosted links swap into `document.body` using the default `innerHTML` and push the URL. The
    first push replaces the initial history entry with an htmx state, so Back to the first page also
    works. The page `<title>` comes from the response, and the view scrolls to the top (FR-011).
  - Only same-origin, non-`_blank` links without a hash-only `href` are boosted. External links,
    which use `target="_blank"`, are untouched. The skip link (`#content`) is untouched.
  - `hx-preserve` moves the live elements into a temporary holder before the swap and back
    afterwards, using `moveBefore` where available. The checkbox element itself survives, along with
    its checked state. While it is in the holder it stays inside `<html>`, so the `:root:has()` rule
    keeps matching during the swap and the theme does not flash (FR-003, FR-011).
  - History restore goes through the same insert path, so `hx-preserve` also applies on Back/Forward
    (FR-013).
  - After a swap htmx focuses the first `[autofocus]` element in the new content (FR-021, see R7).
- **Without JavaScript**: links are ordinary links, the switches still work through CSS, and each
  full load shows the device preference (FR-015).

## R6. Drawer slide-out, including after choosing a page

- **Current state**: `site.css` already slides the popover drawer in, using `@starting-style`, and
  out, using `translate`, `overlay` and `display` with `allow-discrete`. This covers the menu button,
  Escape and light-dismiss. On a full page load the drawer vanishes, because the old document is
  discarded.
- **Decision**:
  - Keep the popover transitions for open and close within a page. Use `ease-out` when opening and
    `ease-in` when closing. Fade the `::backdrop` opacity in step. Define the durations as custom
    properties on `:root`, `--drawer-open-duration: 350ms` and `--drawer-close-duration: 300ms`,
    and use them for every drawer animation (FR-023). This replaces the current 200 ms, which the
    owner found too fast in Firefox. Because the transition on the closed state is the one that runs
    when closing, the open and closed states each carry their own duration.
  - For navigation, give the drawer `view-transition-name: nav-drawer` and the header
    `view-transition-name: site-header`, so the header stays still instead of cross-fading. In the
    new page the drawer is closed (`display: none`), so the transition has only an "old" snapshot of
    it. Style `::view-transition-old(nav-drawer)` with a keyframe animation from `translate: 0` to
    `translate: -100% 0`, `var(--drawer-close-duration)`, `ease-in`. Shorten the root cross-fade to about 150 ms, since the
    htmx docs call the 250 ms default too slow for swaps.
  - Reduced motion: under `@media (prefers-reduced-motion: reduce)`, set `animation: none` on all
    `::view-transition-*` pseudo-elements. The existing popover transitions are already limited to
    `no-preference`.
- **Rationale**: This is pure CSS. View Transitions keep the old content on screen until the new
  content is ready, so there is never a blank page (FR-024). Browsers without View Transitions fall
  back to an instant swap, which the spec's edge case accepts.
- **Alternatives considered**:
  - Preserving the whole drawer and closing it after the swap: this needs `hx-on` (inline JS,
    `unsafe-eval`) and loses the `aria-current` update. Rejected.
  - Targeting `<main>` only with out-of-band header updates: more markup, and it still needs the
    drawer closed. Rejected.

## R7. Keeping screen-reader users oriented after in-place navigation

- **Decision**: Add `is_htmx_request` (true when the `HX-Request: true` header is present) to the
  shared template context. When it is true, `base.html` renders `<h1 tabindex="-1" autofocus>`.
  htmx then focuses the heading after the swap, so the new page title is announced. Full page loads
  render the plain `<h1>`, leaving default browser behaviour and the skip link untouched. Responses
  carry `Vary: HX-Request`, because the markup differs by that header. A `render()` helper in
  `templating.py` sets this header, and it is used by all page routes and the 404 handler.
- **Rationale**: This keeps the logic in Python, which the constitution prefers, and uses a built-in
  htmx behaviour. It meets FR-021.
- **Alternatives considered**:
  - An `aria-live` region announcing the title: needs JS to populate it.
  - Always autofocusing the `<h1>`: this changes behaviour on full page loads too, putting focus
    past the skip link.

## R8. Content Security Policy

- **Decision**: Change `script-src 'none'` to `script-src 'self'`. Everything else is unchanged.
- **Rationale**:
  - htmx only uses `new Function()` for `hx-on`, event filters and `js:` values, none of which are
    used, so `unsafe-eval` is not needed.
  - Indicator CSS would use constructable stylesheets, which `style-src` does not restrict, and is
    disabled anyway.
  - `fetch` requests are same-origin, so `default-src 'self'` covers `connect-src`.
  - The htmx config `<meta>` is not a script.
  - View Transitions need no CSP change.

## R9. Testing approach

- **Device preference**: Playwright `browser.new_context(color_scheme="dark"|"light"|"no-preference")`,
  and `page.emulate_media(color_scheme=…)` for live changes. Assert the computed `background-color`
  of `body` and the `color-scheme` of `:root`.
- **Switch state**: locate it with `get_by_role("switch", name="Dark mode")`. Assert
  `is_checked()`, and check that exactly one switch is in the accessibility tree.
- **No storage**: after exercising the switch and navigation, assert `context.cookies() == []`,
  `localStorage.length === 0` and `sessionStorage.length === 0`.
- **Boosted navigation**: after clicking a nav link, assert that the URL changed, that
  `performance.getEntriesByType("navigation")` still has one entry (no full reload), and that the
  theme, header, title and `aria-current` are correct. Then call `page.go_back()` and
  `page.go_forward()` and assert the theme and content. Finally `page.reload()` and assert the
  device preference is shown.
- **Drawer slide**: assert the computed open and close transition durations are 350 ms and 300 ms. During a boosted
  navigation, assert that `document.getAnimations()` includes an animation on
  `::view-transition-old(nav-drawer)`. Under `reduced_motion="reduce"`, assert no such animation and
  no popover transition.
- **No JavaScript**: use `java_script_enabled=False` contexts for the switch (FR-010) and plain
  navigation (FR-015).
- **Firefox**: the owner uses Firefox, and its handling of popover exit transitions differs (no
  `overlay` property support at the time of writing), so the drawer-animation and theme tests are
  also run in Firefox. Mark them with a pytest `firefox` marker, or parametrise them over the
  browser, and install Firefox in CI alongside Chromium. The rest of the suite stays
  Chromium-only to keep CI fast.
- **Accessibility**: axe on every page × {light, dark} × {drawer open, closed}.
- **Server**: `TestClient` checks for the CSP, `Vary`, the h1 `autofocus` only when the `HX-Request`
  header is sent, both switches with `hx-preserve`, `hx-boost:inherited` on body, htmx served from
  static files, and no `Set-Cookie`.
