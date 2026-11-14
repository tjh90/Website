# Feature Specification: Light and Dark Theme Switching

**Feature Branch**: `rewrite` (spec-kit feature id `002-theme-switching`)

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "I'd like to add the ability to switch between light and dark themes.
See the impl on the main branch for reference. One change I'd like to make is that the default theme
should come from the user's settings (browser/machine? Whatever is possible)."

## Reference Implementation

The site on the `main` branch is the behavioural reference. Relevant behaviour:

- A "Dark mode" item with a checkbox sits in the navigation drawer, below the page links.
  Activating either the item or its checkbox toggles between the light and dark themes.
- The site always starts in the light theme; the visitor's device preference is ignored.
- The choice lasts while the visitor moves between pages, but a reload or a new visit shows the
  light theme again. Nothing is stored.
- In the dark theme, the header bar keeps the brand blue and accent colours are lightened so they
  stay readable on the dark background.

Deliberate changes from the reference:

- The default theme follows the visitor's own light/dark preference as reported by their browser
  (which normally reflects their operating system setting), instead of always being light.
- The control shows the theme actually displayed: "Dark mode" is On whenever the dark theme is
  shown, including when it came from the device preference.

## Clarifications

### Session 2026-11-14

- Q: How should a manual switch be remembered? → A: It must not be stored at all: no cookies and no
  other browser storage. The site keeps the visitor's switch while they move between pages by
  following site links, for the rest of that visit; a reload, new tab or new visit returns to the
  device preference. (This supersedes the cookie approach noted in feature 001 on 2026-11-12.)
- Q: Which persistence approach? → A: Option C of those discussed: following a site link replaces
  the page's content in place, keeping the theme control and its state. Each page keeps its own
  address. Without JavaScript, pages load in full as they do today, so the switch lasts for the
  current page only.
- Q: How should the control be labelled? → A: Always the same label, with its state showing the
  displayed theme. Either "Theme: Light/Dark" or "Dark mode: Off/On" is acceptable; "Dark mode"
  with Off/On is used, matching the reference.
- Q: Should the navigation drawer animate more smoothly now that in-place navigation is added? →
  A: Yes: the drawer slides in from the left when opened and slides back out to the left whenever
  it closes, including after choosing a page.
- Q: How fast should the drawer slide? → A: The current 200 ms feels too fast (observed in
  Firefox). Open over about 350 ms and close over about 300 ms.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Site matches the visitor's device preference (Priority: P1)

A visitor whose device is set to dark mode opens the site and sees it in the dark theme straight
away, with no flash of the light theme; a visitor whose device is set to light mode (or who has no
preference) sees the light theme.

**Why this priority**: This is the change the owner specifically asked for, and it benefits every
visitor without them doing anything.

**Independent Test**: Load each page with the browser emulating a dark preference, then a light
preference, then no preference, and check which theme is shown from the first paint and the state
of the "Dark mode" control.

**Acceptance Scenarios**:

1. **Given** a visitor whose browser reports a dark preference, **When** they open any page,
   **Then** the page is shown in the dark theme from the first paint, and the "Dark mode" control
   is On.
2. **Given** a visitor whose browser reports a light preference or no preference, **When** they
   open any page, **Then** the page is shown in the light theme, and the "Dark mode" control is
   Off.
3. **Given** a visitor who has not switched theme, **When** they change their device preference
   while the site is open, **Then** the site and the control switch to match, without a reload.
4. **Given** a visitor with JavaScript disabled, **When** they open any page, **Then** the theme
   and control state still match their device preference.

---

### User Story 2 - Visitor switches theme manually (Priority: P1)

A visitor who prefers the other theme for this site opens the navigation drawer and turns "Dark
mode" on or off. The whole page changes theme instantly and they stay where they were.

**Why this priority**: Switching theme is the core capability requested and exists in the
reference.

**Independent Test**: On each page, under both emulated device preferences, open the drawer, use
the control, and check that the theme changes, the address and scroll position are unchanged, and
the control's state matches the theme shown.

**Acceptance Scenarios**:

1. **Given** any page shown in the light theme, **When** the visitor turns "Dark mode" On, **Then**
   the page is shown in the dark theme and the visitor is still on the same page.
2. **Given** any page shown in the dark theme (whether from the device preference or a previous
   switch), **When** the visitor turns "Dark mode" Off, **Then** the page is shown in the light
   theme.
3. **Given** the drawer is open, **When** the visitor views the control, **Then** its label is
   always "Dark mode", and it is On exactly when the dark theme is shown, both visually and to
   assistive technology.
4. **Given** a keyboard-only visitor, **When** they reach the control, **Then** they can operate it
   with the keyboard alone.
5. **Given** a visitor with JavaScript disabled, **When** they use the control, **Then** the theme
   still changes immediately on the current page.

---

### User Story 3 - Switch lasts while browsing (Priority: P2)

A visitor who has switched theme keeps seeing their chosen theme as they move between pages using
the site's own links and the browser's Back and Forward buttons, for the rest of the visit.

**Why this priority**: Without this, a visitor who prefers the other theme must switch again on
every page, which makes the control of little use on a multi-page site.

**Independent Test**: Switch to the theme opposite to the emulated device preference, follow links
to every other page, use Back and Forward, and check the chosen theme and control state on each
page; then reload and check the device preference is used again.

**Acceptance Scenarios**:

1. **Given** a visitor switched theme, **When** they follow a link in the navigation drawer to
   another page, **Then** the new page is shown in the chosen theme with no flash of the other
   theme, the address shows the new page, and the header, tab title and current-page indicator
   update as they do today.
2. **Given** a visitor switched theme and then visited another page, **When** they use the browser's
   Back or Forward button, **Then** the page shown keeps the theme the visitor is currently using.
3. **Given** a visitor switched theme, **When** they reload the page, open a page in a new tab, type
   an address, or return later, **Then** the site shows their device preference again.
4. **Given** a visitor with JavaScript disabled who switched theme, **When** they follow a link,
   **Then** the new page loads normally and shows their device preference.
5. **Given** any visitor, **When** they use the site, **Then** the site stores nothing in their
   browser (no cookies or other browser storage).

---

### User Story 4 - Drawer slides smoothly in and out (Priority: P3)

A visitor opens the navigation drawer and it slides in smoothly from the left edge; when they close
it, whether with the menu button, by clicking outside it, by pressing Escape or by choosing a page,
it slides smoothly back out to the left.

**Why this priority**: A polish improvement. Today the drawer slides when opened and closed with
the menu button, but simply vanishes when the visitor chooses a page, because the whole page is
replaced. In-place navigation makes a consistent slide-out possible.

**Independent Test**: With motion allowed, open and close the drawer by each method and check it
moves in from and out to the left rather than appearing or disappearing abruptly; repeat with
reduced motion preferred and check it opens and closes instantly.

**Acceptance Scenarios**:

1. **Given** the drawer is closed, **When** the visitor activates the menu button, **Then** the
   drawer slides in from the left edge and the page behind is gradually dimmed.
2. **Given** the drawer is open, **When** the visitor closes it with the menu button, by clicking
   outside it or by pressing Escape, **Then** it slides out to the left and the dimming fades away.
3. **Given** the drawer is open, **When** the visitor chooses another page, **Then** the drawer
   slides out to the left while the new page's content appears, and the visitor is never shown a
   blank page.
4. **Given** a visitor who prefers reduced motion, **When** they open or close the drawer by any
   method, **Then** it appears and disappears without sliding.
5. **Given** a visitor with JavaScript disabled, **When** they choose another page, **Then** the new
   page loads normally with the drawer closed (no slide-out is required).

---

### Edge Cases

- **Device preference changes after a manual switch**: the site follows the new device preference
  and the control shows the new state. If the preference changes back during the same visit, the
  earlier manual switch for that preference may reappear (see FR-004).
- **Browser reports no preference** (or an old browser that cannot report one): the light theme is
  used and "Dark mode" is Off.
- **Switching while on the 404 page**: the theme changes and the visitor stays on the 404 page;
  following a link from it keeps the theme.
- **Following an external link**: the destination opens in a new tab as today; the site's own tab
  keeps its theme.
- **Navigation fails mid-visit** (e.g. connection drops): the visitor sees the browser's usual error
  or the site's error page; no blank or half-updated page is left behind.
- **Reduced motion**: theme-switch transitions (if any) and the drawer slide are suppressed for
  visitors who prefer reduced motion.
- **Rapid open/close**: activating the menu button again mid-slide reverses the drawer smoothly
  from its current position without jumping, and it always ends fully open or fully closed.
- **Browsers without exit-animation support**: the drawer still opens and closes correctly; it may
  disappear without sliding out.
- **Images and icons**: the painting is shown unchanged in both themes; icons remain visible against
  both backgrounds.
- **Browser-drawn elements** (scrollbars, form controls, focus rings): they match the active theme.

## Requirements *(mandatory)*

### Functional Requirements

#### Default theme

- **FR-001**: The site MUST provide a light theme and a dark theme covering every page and all site
  chrome (header, drawer, skip link, 404 page).
- **FR-002**: Unless the visitor has switched theme during the current visit, the site MUST show the
  theme matching the light/dark preference reported by their browser, and MUST use the light theme
  when no preference is reported.
- **FR-003**: The correct theme MUST be applied from the first paint of every page, with no visible
  flash of the other theme.
- **FR-004**: When the device preference changes while a page is open, the site MUST switch to
  match it without a reload. A manual switch applies only to the device preference it was made
  under; if the preference later changes back during the same visit, that earlier switch may apply
  again.
- **FR-005**: Default-theme behaviour MUST work with JavaScript disabled.

#### Manual switching

- **FR-006**: The navigation drawer MUST contain a theme control, placed after the page links and
  before the bottom-pinned About link, as in the reference.
- **FR-007**: The control MUST always carry the same accessible name and visible label, "Dark mode",
  and MUST be On exactly when the dark theme is shown and Off when the light theme is shown,
  regardless of whether the theme came from the device preference or a manual switch. Its state
  MUST be conveyed both visually and to assistive technology.
- **FR-008**: Using the control MUST change the theme of the whole page immediately, without
  reloading the page or changing the address or scroll position.
- **FR-009**: The control MUST be keyboard-operable and meet the site's existing touch-target size;
  activating its label MUST toggle it, as in the reference.
- **FR-010**: The control MUST work with JavaScript disabled.

#### Keeping the switch while browsing

- **FR-011**: Following an internal link MUST keep the visitor's current theme and control state on
  the new page for the rest of the visit, while still updating the address, header title, tab title,
  page content, current-page indicator and closed drawer exactly as a full page load would.
- **FR-012**: Every page MUST remain available at its own address and MUST render completely when
  opened directly, reloaded, or loaded with JavaScript disabled.
- **FR-013**: The browser's Back and Forward buttons MUST show the correct page content and keep the
  visitor's current theme and control state.
- **FR-014**: A reload, new tab, typed address or new visit MUST show the device preference.
- **FR-015**: Without JavaScript, internal links MUST work as full page loads; the theme then
  follows the device preference on each newly loaded page.
- **FR-016**: The site MUST NOT set cookies or use any other browser storage. The About page's
  existing statement that the site does not use cookies MUST remain accurate.

#### Drawer animation

- **FR-022**: The navigation drawer MUST slide in from the left edge when opened and slide out to
  the left whenever it closes: via the menu button, clicking outside it, pressing Escape, or choosing
  a page. The backdrop dimming MUST fade in and out with it.
- **FR-023**: Opening MUST slide in over about 350 ms, decelerating as it arrives. Closing, by any
  method, MUST slide out over about 300 ms, accelerating as it leaves. Each may vary by ±50 ms. The
  durations MUST be defined in one place so they can be tuned without other changes.
- **FR-024**: When the visitor chooses a page, the drawer's slide-out and the new content appearing
  MUST NOT leave the visitor looking at a blank or partially updated page.
- **FR-025**: For visitors who prefer reduced motion, the drawer MUST open and close without
  sliding.
- **FR-026**: The animation MUST NOT change the drawer's existing behaviour: it still works without
  JavaScript, and the menu button stays reachable and reports the drawer's state.

#### Appearance and accessibility

- **FR-017**: Both themes MUST meet WCAG 2.2 AA contrast for text, links, focus indicators, icons,
  the theme control and the current-page indicator in the drawer.
- **FR-018**: The dark theme MUST keep the site's visual identity from the reference: the header
  stays brand blue and accent colours are lightened for readability on the dark background.
- **FR-019**: Browser-drawn elements (scrollbars, form controls) MUST match the active theme.
- **FR-020**: Automated accessibility scans MUST report no serious or critical violations on any page
  in either theme, with the drawer open and closed.
- **FR-021**: After in-place navigation, keyboard focus and screen-reader announcements MUST leave
  the visitor oriented on the new page (e.g. the new page title is announced or focus moves to the
  start of the page), comparable to a full page load.

### Key Entities

- **Theme**: a named colour scheme applied to the whole site; values Light and Dark.
- **Device preference**: the visitor's light/dark preference as reported by their browser (light,
  dark or none); read-only to the site.
- **Manual switch**: the visitor's use of the "Dark mode" control during the current visit. Held
  only in the open page, never stored; cleared by a reload, new tab, new visit or a change in device
  preference. The theme shown is the opposite of the device preference if a manual switch is in
  effect, otherwise the device preference, otherwise Light.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For 100% of pages, a visitor sees the theme matching their device preference from the
  first paint, with the control in the matching state.
- **SC-002**: A visitor can switch theme from any page in at most 2 actions (open drawer, use
  control); the new theme is shown in under 100 ms and the visitor remains on the same page.
- **SC-003**: After a switch, 100% of pages reached by site links or Back/Forward during the visit
  show the chosen theme, with no flash of the other theme.
- **SC-004**: The site sets zero cookies and writes nothing to browser storage in any scenario.
- **SC-005**: Automated accessibility scans report zero serious or critical violations, including
  colour contrast, on every page in both themes.
- **SC-006**: Every acceptance scenario above is covered by a passing automated test, including the
  JavaScript-disabled scenarios.
- **SC-007**: Moving between pages by site links is no slower than a full page load today (within
  the existing 1-second page load target).
- **SC-008**: With motion allowed, the drawer visibly slides (rather than appearing or vanishing)
  for 100% of opens and closes by every method in browsers that support exit animations, and each
  slide matches the FR-023 durations, in Chromium and Firefox.

## Assumptions

- "The user's settings" is interpreted as the light/dark preference that browsers expose to
  websites, which normally mirrors the operating system setting (or a browser-level override). The
  site cannot read operating system settings directly. Browsers too old to report a preference get
  the light theme.
- Losing a manual switch on reload, in a new tab or on a new visit is acceptable: the owner chose
  storing nothing over remembering the switch.
- Without JavaScript, the switch lasting only for the current page is acceptable, in line with the
  constitution's progressive-enhancement principle.
- Theme colours for the dark mode are derived from the existing light-theme tokens and the
  reference's dark-mode accents; exact values are a design detail for the plan, constrained by
  FR-017 and FR-018.
- Anascramble and any other future pages inherit both themes and in-place navigation automatically
  through the shared layout and colour tokens.
- Adding a small, self-hosted third-party library to provide in-place navigation is acceptable;
  the constitution already allows the vendored htmx library once a feature needs it.
