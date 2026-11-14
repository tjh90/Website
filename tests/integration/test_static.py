"""Integration tests for vendored static assets."""

from fastapi.testclient import TestClient

HTMX_VERSION = "4.0.1"


def test_htmx_is_served(client: TestClient) -> None:
    """The pinned htmx release is served from the site's static files (research R4)."""
    response = client.get("/static/js/htmx.min.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/javascript")
    assert f'version="{HTMX_VERSION}"' in response.text
