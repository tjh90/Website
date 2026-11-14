# Quickstart: Anascramble Page

Validation guide for feature 003. Details of markup and responses are in
[contracts/page-layout.md](contracts/page-layout.md) and [contracts/http.md](contracts/http.md).

## Prerequisites

- uv installed; dependencies synced (`uv sync`), including the new `python-multipart`.
- Playwright browsers installed (`uv run playwright install --with-deps chromium firefox`).

## Automated checks

All quality gates from the constitution:

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

Caret-preservation tests also run in Firefox:

```bash
uv run pytest -m firefox --browser firefox
```

## Manual walkthrough

Start the site (`uv run website`) and open `/anascramble`.

| # | Do | Expect |
|---|---|---|
| 1 | Open the drawer | "Anascramble" sits between Home and About; current page marked |
| 2 | Look at the empty page | Scramble area, letters field, disabled "Scramble!"; no solution row |
| 3 | Type `le` then `7` | `7` disappears; button still disabled |
| 4 | Type `tter` | Button enabled; "Solution:" shows 6 cells |
| 5 | Press "Scramble!" twice | L E T T E R in a handwritten font, non-overlapping, new layout each time |
| 6 | Type `t` `t` `t` in the solution | `TT` kept, third T removed; two scrambled T dimmed |
| 7 | Type space then `e` | Blank cell then E; one E dimmed; caret stays in place |
| 8 | Backspace twice | E and blank removed; E undimmed |
| 9 | Scramble again | Solution kept; matching letters dimmed in the new layout |
| 10 | Edit the letters | Scramble cleared; solution reset to empty cells of the new length |
| 11 | Type 30 letters, scramble | All letters visible inside the area (smaller), no overlaps |
| 12 | Switch Dark mode on | Everything readable; dimmed letters still distinguishable; puzzle kept |
| 13 | Narrow the window to 320 px | No page sideways scroll; scramble area shrinks |
| 14 | Disable JavaScript, repeat 3–9 by pressing Enter/"Scramble!" | Same results after each submission (re-scrambles on each submit) |
| 15 | Check DevTools → Application | No cookies or storage; letters not in the URL |
| 16 | About page | Credits list Rock Salt (Apache License 2.0) |
