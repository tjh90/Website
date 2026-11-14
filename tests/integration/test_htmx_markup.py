"""Integration tests for the htmx wiring and htmx-aware rendering (feature 002, US3)."""

import re

import pytest
from fastapi.testclient import TestClient

_HTML_PATHS = ["/", "/about", "/does-not-exist"]
_HTMX = {"HX-Request": "true"}


@pytest.mark.parametrize("path", _HTML_PATHS)
def test_body_boosts_links_with_view_transitions(client: TestClient, path: str) -> None:
    """Links inside ``<body>`` are boosted with view transitions (research R5)."""
    assert '<body hx-boost:inherited="transition:true">' in client.get(path).text


@pytest.mark.parametrize("path", _HTML_PATHS)
def test_head_loads_htmx_with_config(client: TestClient, path: str) -> None:
    """``<head>`` configures and loads the vendored htmx (contracts/page-layout.md)."""
    html = client.get(path).text
    head = html[: html.index("</head>")]
    assert """<meta name="htmx-config" content='{"includeIndicatorCSS":false}'>""" in head
    assert '<script src="/static/js/htmx.min.js" defer></script>' in head


@pytest.mark.parametrize("path", _HTML_PATHS)
def test_heading_not_focused_on_full_load(client: TestClient, path: str) -> None:
    """Full page loads render a plain ``<h1>`` (research R7)."""
    h1 = re.search(r"<h1[^>]*>", client.get(path).text)
    assert h1 is not None
    assert h1.group(0) == "<h1>"


@pytest.mark.parametrize("path", _HTML_PATHS)
def test_heading_focused_after_htmx_request(client: TestClient, path: str) -> None:
    """Requests from htmx get an autofocused heading and still a full page (FR-012, FR-021)."""
    html = client.get(path, headers=_HTMX).text
    assert '<h1 tabindex="-1" autofocus>' in html
    for fragment in ("<html", "<head>", 'id="nav-drawer"', "</html>"):
        assert fragment in html
