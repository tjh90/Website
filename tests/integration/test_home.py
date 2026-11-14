"""Integration tests for the home page."""

import re

import pytest
from fastapi.testclient import TestClient

from website.content import EXTERNAL_LINKS, PAINTING_ALT, ExternalLink


@pytest.fixture
def html(client: TestClient) -> str:
    """Rendered home page HTML."""
    return client.get("/").text


def test_home_page_loads(client: TestClient) -> None:
    """``/`` returns HTML for both GET and HEAD."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert client.head("/").status_code == 200


def test_home_titles(html: str) -> None:
    """The tab and header both show the site title."""
    assert "<title>Tim&#39;s Page</title>" in html or "<title>Tim's Page</title>" in html
    assert re.search(r"<h1>Tim(&#39;|')s Page</h1>", html)


def test_links_heading(html: str) -> None:
    """The links section has a "Links:" heading."""
    assert re.search(r"<h2[^>]*>Links:</h2>", html)


@pytest.mark.parametrize("link", EXTERNAL_LINKS, ids=lambda link: link.text)
def test_external_link_markup(html: str, link: ExternalLink) -> None:
    """Each link opens safely in a new tab and has a decorative icon."""
    anchor = re.search(rf'<a href="{re.escape(link.url)}"[^>]*>(.*?)</a>', html, flags=re.S)
    assert anchor, f"No anchor for {link.url}"
    tag = anchor.group(0)
    assert 'target="_blank"' in tag
    assert 'rel="noopener noreferrer"' in tag
    assert link.text in anchor.group(1)
    assert re.search(r'<svg[^>]*aria-hidden="true"[^>]*focusable="false"', anchor.group(1))


def test_painting(html: str) -> None:
    """The painting has the expected source, alt text and intrinsic size."""
    alt = PAINTING_ALT.replace("'", "&#39;")
    img = re.search(r'<img src="/static/img/sisley\.jpg"[^>]*>', html)
    assert img
    assert f'alt="{alt}"' in img.group(0) or f'alt="{PAINTING_ALT}"' in img.group(0)
    assert re.search(r'width="\d+"', img.group(0))
    assert re.search(r'height="\d+"', img.group(0))
