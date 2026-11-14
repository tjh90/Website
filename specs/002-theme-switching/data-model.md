# Data Model: Light and Dark Theme Switching

The feature has no persisted data. The entities below are the client-side state and server-side
values the design relies on.

## Theme (client-side, derived)

| Field | Values | Source |
|---|---|---|
| active theme | `light`, `dark` | the computed `color-scheme` of `:root` |

**Derivation** (evaluated continuously by CSS):

| Device preference | Visible switch | Switch default | Switch state | Active theme |
|---|---|---|---|---|
| light / none | `#dark-mode-light-device` | Off | Off | light |
| light / none | `#dark-mode-light-device` | Off | On | dark |
| dark | `#dark-mode-dark-device` | On | On | dark |
| dark | `#dark-mode-dark-device` | On | Off | light |

Invariant: the visible switch is On ⇔ the active theme is dark (FR-007).

## Dark mode switch (client-side, DOM state)

| Field | Type | Notes |
|---|---|---|
| `id` | `dark-mode-light-device` \| `dark-mode-dark-device` | Stable; required by `hx-preserve` |
| `checked` | bool | Initial: `false` for the light-device switch, `true` for the dark-device switch |
| visible | bool | By media query; exactly one is visible (and in the accessibility tree) |

**State transitions**:

- Visitor activates the visible switch → `checked` toggles → the active theme flips.
- In-place navigation or Back/Forward (JS on) → the elements are preserved, so `checked` is kept.
- Full load (reload, new tab, typed URL, no JS) → new elements with their initial `checked` values,
  so the device preference applies.
- Device preference changes → the other switch becomes visible with whatever state it has (its
  initial value unless the visitor used it earlier on this page; see research R3 known limitation).

## HTMX request flag (server-side, per request)

| Field | Type | Rule |
|---|---|---|
| `is_htmx_request` | `bool` | `True` when the request header `HX-Request` equals `true` |

Effect: the page `<h1>` is rendered with `tabindex="-1" autofocus`, and every HTML response carries
`Vary: HX-Request`.

## Credit (existing entity, new instance)

| Field | Value |
|---|---|
| work | htmx |
| work URL | `https://htmx.org` |
| author | Big Sky Software |
| licence | BSD Zero Clause License |
| licence URL | `https://opensource.org/license/0bsd` |
