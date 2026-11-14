# Quickstart: validating Light and Dark Theme Switching

## Prerequisites

As for feature 001: uv installed, then:

```bash
uv sync
```

```bash
uv run playwright install --with-deps chromium firefox
```

## Automated validation

```bash
uv run pytest
```

Expected: all tests pass, including the new `tests/e2e/test_theme.py` and
`tests/e2e/test_boosted_navigation.py`. The full quality gate set (`uv lock --check`, `ruff format
--check`, `ruff check`, `ty check`, Docker build) must also pass, as in the constitution.

Check that the vendored htmx file matches the pinned release:

```bash
curl -s https://registry.npmjs.org/htmx.org/4.0.1 | python -c "import json,sys;print(json.load(sys.stdin)['dist']['integrity'])"
```

Compare it with the value recorded in [research.md](research.md) R4.

## Manual validation

Start the site:

```bash
uv run website
```

Then work through the scenarios below in a browser. Use DevTools' "Emulate CSS
prefers-color-scheme" (Rendering panel) or the OS setting.

| # | Steps | Expected | Spec |
|---|---|---|---|
| 1 | Set the device to dark; open `/` | Dark from first paint; drawer shows "Dark mode" On | US1, FR-002/003/007 |
| 2 | Set the device to light; open `/` | Light; "Dark mode" Off | US1 |
| 3 | With the page open, flip the device setting | Theme and switch follow without a reload | FR-004 |
| 4 | Open the drawer; toggle "Dark mode" | Theme flips instantly; drawer stays open; URL unchanged | US2, FR-008 |
| 5 | After step 4, click About in the drawer | Drawer slides out left; About shown in the chosen theme; URL `/about`; header "About" | US3, US4, FR-011/022 |
| 6 | Press Back, then Forward | Correct pages; chosen theme kept | FR-013 |
| 7 | Reload | Device preference shown again | FR-014 |
| 8 | DevTools → Application: Cookies, Local and Session storage | All empty | FR-016, SC-004 |
| 9 | Open/close the drawer with the menu button, Escape and by clicking outside | Slides in over about 350 ms and out over about 300 ms, from and to the left; check in Firefox too | US4, FR-023 |
| 10 | Emulate `prefers-reduced-motion: reduce`; repeat 5 and 9 | No sliding | FR-025 |
| 11 | Disable JavaScript; repeat 1, 2 and 4 | Same results | FR-005/010 |
| 12 | Disable JavaScript; toggle, then click About | Full page load; device preference shown | FR-015 |
| 13 | Keyboard only: Tab to the menu button, open it, Tab to "Dark mode", press Space; then follow a link | Switch toggles; after navigation focus is on the page heading | FR-009/021 |

See [contracts/page-layout.md](contracts/page-layout.md) for the DOM details the tests rely on.
