"""Integration tests for response headers common to every route."""

import re

import pytest
from fastapi.testclient import TestClient

from website.app import SECURITY_HEADERS

_PATHS = ["/", "/about", "/healthz", "/static/css/site.css", "/does-not-exist"]


@pytest.mark.parametrize("path", _PATHS)
def test_security_headers_present(client: TestClient, path: str) -> None:
    """Every response carries the exact security headers from the contract."""
    response = client.get(path)
    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get(name) == value


@pytest.mark.parametrize("htmx", [False, True], ids=["full-load", "htmx"])
@pytest.mark.parametrize("path", _PATHS)
def test_no_cookies_are_set(client: TestClient, path: str, *, htmx: bool) -> None:
    """The site never sets cookies, for full loads or htmx requests (FR-016)."""
    headers = {"HX-Request": "true"} if htmx else {}
    assert "set-cookie" not in client.get(path, headers=headers).headers


def test_csp_allows_only_own_scripts() -> None:
    """Scripts may load only from the site itself, with no inline or eval (research R8)."""
    csp = SECURITY_HEADERS["Content-Security-Policy"]
    assert "script-src 'self'" in csp
    assert "unsafe-eval" not in csp
    assert "unsafe-inline" not in csp


@pytest.mark.parametrize("path", ["/", "/about", "/does-not-exist"])
def test_html_responses_vary_on_htmx_request(client: TestClient, path: str) -> None:
    """HTML differs for htmx requests, so caches must key on HX-Request (contracts/http.md)."""
    vary = client.get(path).headers.get("vary", "")
    assert "hx-request" in [v.strip().lower() for v in vary.split(",")]


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_api_docs_are_disabled(client: TestClient, path: str) -> None:
    """The interactive API documentation is not exposed."""
    assert client.get(path).status_code == 404


def test_healthz(client: TestClient) -> None:
    """The health endpoint reports ok."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("path", ["/", "/about", "/does-not-exist"])
def test_external_links_open_in_new_tab(client: TestClient, path: str) -> None:
    """Every link to another site opens safely in a new tab; internal links do not."""
    for tag in re.findall(r"<a\s[^>]*>", client.get(path).text):
        href = re.search(r'href="([^"]*)"', tag)
        assert href, tag
        is_external = href.group(1).startswith(("http://", "https://"))
        assert ('target="_blank"' in tag) == is_external, tag
        if is_external:
            assert 'rel="noopener noreferrer"' in tag, tag
