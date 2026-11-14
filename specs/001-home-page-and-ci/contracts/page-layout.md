# Contract: Page Layout (UI/DOM)

This is the structure that the Playwright and `TestClient` tests rely on. Tests SHOULD locate
elements by role and accessible name first, and use the IDs and classes below only where roles
cannot identify an element.

## Common layout (every page, including 404)

> Feature 002 extends this layout with the colour-scheme and htmx `<head>` entries, `hx-boost` on
> `<body>`, the "Dark mode" switches in the drawer and the focusable heading after in-place
> navigation. See [002's page layout contract](../../002-theme-switching/contracts/page-layout.md).

```text
<html lang="en-GB">
  <head>
    <title>  {tab title, per data-model.md}
    <link rel="stylesheet" href="/static/css/site.css">
    <link rel="icon" href="/favicon.ico">
  <body>
    <a class="skip-link" href="#content">Skip to content</a>
    <header class="site-header">                       role=banner
      <button popovertarget="nav-drawer"
              aria-label="Menu">                       role=button, name "Menu"
        {bars icon, aria-hidden}
      <h1>{page title}</h1>                            role=heading level 1
    <nav id="nav-drawer" popover aria-label="Main">    role=navigation, name "Main"
      <ul>
        <li><a href="/" [aria-current="page"]>Home</a>
        <li><a href="/about" [aria-current="page"]>About</a>
    <main id="content">                                role=main
      {page content}
```

**Rules**:

- `aria-current="page"` is set on exactly one nav link (the current page), and on none for 404.
- The drawer is closed on load (`:popover-open` does not match).
- Activating the "Menu" button opens it. Activating it again, pressing Esc or clicking outside
  closes it.
- When popovers are supported, the browser exposes `aria-expanded` on the button.
- With JavaScript disabled, all of the above still works.
- At viewport widths of 320px or more, `document.documentElement.scrollWidth` must not exceed
  `window.innerWidth`.

## Home page (`/`)

```text
<main>
  <section class="links" aria-labelledby="links-heading">
    <h2 id="links-heading">Links:</h2>
    <ul>
      <li><a href="https://www.github.com/tjh90" target="_blank" rel="noopener noreferrer">
            {github icon}GitHub</a>
      <li><a href="https://eprints.soton.ac.uk/404274/" target="_blank" rel="noopener noreferrer">
            {book icon}PhD Thesis</a>
      <li><a href="https://ieeexplore.ieee.org/document/7029130" target="_blank" rel="noopener noreferrer">
            {file-lines icon}Paper</a>
  <figure class="painting">
    <img src="/static/img/sisley.jpg" alt="Sisley - Lady's Cove (1897)" width=… height=…>
```

- Icons: `<svg aria-hidden="true" focusable="false">`, each preceded by its Font Awesome licence
  comment.
- Layout: links and painting sit side by side at ≥ 768px and stack (links first) below that.

## About page (`/about`)

```text
<main>
  <section aria-labelledby="source-heading">
    <h2 id="source-heading">Source code</h2>
    <p>… free software licensed under the
       <a href="https://www.gnu.org/licenses/agpl-3.0.html">GNU Affero General Public License v3.0</a>.
    <p><a href="https://github.com/tjh90/website" target="_blank" rel="noopener noreferrer">
         Source code on GitHub</a>
    [<p>Running revision
       <a href="https://github.com/tjh90/website/tree/{sha}" target="_blank" rel="noopener noreferrer">
         <code>{sha[:7]}</code></a>]          ← only when the revision is known
  <section aria-labelledby="cookies-heading">
    <h2 id="cookies-heading">Cookies</h2>
    <p>This site does not use cookies.
  <section aria-labelledby="credits-heading">
    <h2 id="credits-heading">Credits</h2>
    <ul>
      <li><a href="https://fontawesome.com">Font Awesome Free</a> icons by Fonticons, Inc.,
          licensed under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.
      <li>Alfred Sisley, Lady's Cove (1897), public domain.
```

## 404 page

The heading reads "Page not found", followed by a short message and a link back to Home
(`<a href="/">`). The status code is 404.
