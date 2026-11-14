"""Integration tests for the theme and Dark mode switch markup (feature 002)."""

import re

import pytest
from fastapi.testclient import TestClient

_HTML_PATHS = ["/", "/about", "/does-not-exist"]


@pytest.mark.parametrize("path", _HTML_PATHS)
def test_color_scheme_meta_precedes_stylesheet(client: TestClient, path: str) -> None:
    """Pages declare both colour schemes before the stylesheet loads (research R1)."""
    html = client.get(path).text
    meta = html.find('<meta name="color-scheme" content="light dark">')
    stylesheet = html.find('<link rel="stylesheet"')
    assert meta != -1
    assert -1 < meta < stylesheet < html.index("</head>")


def _drawer(html: str) -> str:
    """Return the HTML of the navigation drawer."""
    start = html.index('<nav id="nav-drawer"')
    return html[start : html.index("</nav>", start)]


@pytest.mark.parametrize("path", _HTML_PATHS)
def test_drawer_has_both_dark_mode_switches(client: TestClient, path: str) -> None:
    """The drawer holds the two preserved "Dark mode" switches before About (FR-006, FR-007)."""
    drawer = _drawer(client.get(path).text)
    item_start = drawer.index('<li class="theme-item">')
    item = drawer[item_start : drawer.index("</li>", item_start)]

    assert drawer.index('href="/"') < item_start < drawer.index('href="/about"')

    inputs = re.findall(r"<input[^>]*>", item)
    assert len(inputs) == 2
    light, dark = inputs
    for tag in inputs:
        assert 'type="checkbox"' in tag
        assert 'role="switch"' in tag
        assert re.search(r"\shx-preserve[\s>]", tag)
        # Stops Firefox restoring a toggled switch on reload (FR-014).
        assert 'autocomplete="off"' in tag
    assert 'id="dark-mode-light-device"' in light
    assert "checked" not in light
    assert 'id="dark-mode-dark-device"' in dark
    assert re.search(r"\schecked[\s>]", dark)

    labels = re.findall(r"<label[^>]*>(.*?)</label>", item, flags=re.DOTALL)
    assert len(labels) == 2
    for label in labels:
        assert re.sub(r"<[^>]+>", "", label).strip() == "Dark mode"
        assert "<input" in label
