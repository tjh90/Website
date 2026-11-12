"""Integration tests for the shared layout, navigation and 404 page."""

import re

import pytest
from fastapi.testclient import TestClient

from website.content import PAGES, Page


@pytest.mark.parametrize("page", PAGES, ids=lambda page: page.name)
def test_layout_has_drawer(client: TestClient, page: Page) -> None:
    """Each page has the menu button, the drawer and exactly one current link."""
    response = client.get(page.path)
    assert response.status_code == 200
    html = response.text
    assert re.search(r'<button[^>]*popovertarget="nav-drawer"[^>]*aria-label="Menu"', html)
    assert re.search(r'<nav id="nav-drawer"[^>]*popover[^>]*aria-label="Main"', html)
    for nav_page in PAGES:
        assert re.search(rf'<a href="{nav_page.path}"[^>]*>{nav_page.nav_label}</a>', html)
    current = re.findall(r'<a href="([^"]+)" aria-current="page"', html)
    assert current == [page.path]


def test_not_found_page(client: TestClient) -> None:
    """Unknown paths return a 404 page that keeps the layout."""
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert "<h1>Page not found</h1>" in html
    assert re.search(r"<title>Page not found · Tim(&#39;|')s Page</title>", html)
    assert 'id="nav-drawer"' in html
    main = html[html.index("<main") :]
    assert 'href="/"' in main
    assert "aria-current" not in html


def test_about_trailing_slash_redirects(client: TestClient) -> None:
    """``/about/`` redirects to the canonical ``/about``."""
    response = client.get("/about/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].endswith("/about")
