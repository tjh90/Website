"""Integration tests for vendored static assets."""

from fastapi.testclient import TestClient

HTMX_VERSION = "4.0.1"


def test_htmx_is_served(client: TestClient) -> None:
    """The pinned htmx release is served from the site's static files (research R4)."""
    response = client.get("/static/js/htmx.min.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/javascript")
    assert f'version="{HTMX_VERSION}"' in response.text


def test_rock_salt_font_is_served(client: TestClient) -> None:
    """The self-hosted Rock Salt font is served with a font media type (research R8)."""
    response = client.get("/static/fonts/rock-salt-latin-400-normal.woff2")
    assert response.status_code == 200
    assert response.headers["content-type"] == "font/woff2"


def test_rock_salt_licence_is_served(client: TestClient) -> None:
    """The font's Apache licence is kept and served alongside it (constitution VI)."""
    response = client.get("/static/fonts/rock-salt-LICENSE.txt")
    assert response.status_code == 200
    assert "Apache License" in response.text
