# Contract: Page Layout changes (UI/DOM)

This contract extends [feature 001's page layout contract](../../001-home-page-and-ci/contracts/page-layout.md).
Everything not listed here is unchanged. Tests locate elements by role and accessible name first.

## `<head>` additions

```text
<meta name="color-scheme" content="light dark">
<meta name="htmx-config" content='{"includeIndicatorCSS":false}'>
<script src="/static/js/htmx.min.js" defer></script>
```

## `<body>`

```text
<body hx-boost:inherited="transition:true">
```

## Header title

```text
<h1>{page title}</h1>                                    ← full page load
<h1 tabindex="-1" autofocus>{page title}</h1>            ← request with HX-Request: true
```

## Navigation drawer

The "Dark mode" item sits after the page links and before the bottom-pinned About link.

```text
<nav id="nav-drawer" popover aria-label="Main">
  <ul>
    <li><a href="/" …>Home</a>
    <li class="theme-item">
      <label class="theme-switch theme-switch--light-device">
        <input type="checkbox" role="switch" id="dark-mode-light-device" hx-preserve>
        Dark mode
      <label class="theme-switch theme-switch--dark-device">
        <input type="checkbox" role="switch" id="dark-mode-dark-device" checked hx-preserve>
        Dark mode
    <li><a href="/about" …>About</a>
```

**Rules**:

- Exactly one switch is rendered visibly, and only that one is exposed to assistive technology
  (`role=switch`, name "Dark mode"). Under a light or no device preference it is
  `#dark-mode-light-device`; under a dark preference it is `#dark-mode-dark-device`. The other is
  `display: none`.
- The visible switch is checked if and only if `:root` computes `color-scheme: dark`.
- Activating anywhere on the label toggles the switch. The switch is keyboard-focusable and toggles
  with Space. The row meets the 44 px minimum target height.
- The switch does not close the drawer.
- With JavaScript disabled, all of the above still works.

## Styling hooks (CSS contract)

| Selector | Purpose |
|---|---|
| `:root` | `color-scheme: light`, or `dark` under `prefers-color-scheme: dark`; tokens use `light-dark()` |
| `:root:has(#dark-mode-light-device:checked)` (light/none preference only) | `color-scheme: dark` |
| `:root:has(#dark-mode-dark-device:not(:checked))` (dark preference only) | `color-scheme: light` |
| `.drawer` | `view-transition-name: nav-drawer`; slides in over `--drawer-open-duration` (350 ms, ease-out) and out over `--drawer-close-duration` (300 ms, ease-in) |
| `.site-header` | `view-transition-name: site-header` |
| `::view-transition-old(nav-drawer)` | slides to `translate: -100% 0` over `--drawer-close-duration` |
| `@media (prefers-reduced-motion: reduce)` | no drawer transition, no view-transition animation |

## In-place navigation behaviour (JavaScript enabled)

| Trigger | Result |
|---|---|
| Click an internal link (same origin, no `target`, not hash-only) | `GET` with `HX-Request: true` and `HX-Boosted: true`; `<body>` contents replaced; URL pushed; `<title>` updated; scroll to top; `<h1>` focused; both switches preserved |
| Click an external link (`target="_blank"`) or the skip link | Unchanged browser behaviour |
| Back / Forward to a boosted entry | `GET` with `HX-Request: true` and `HX-History-Restore-Request: true`; `<body>` replaced; switches preserved |
| Reload, new tab, typed URL | Normal full page load; switches at their initial state |
