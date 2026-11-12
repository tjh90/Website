"""Integration tests for the About page."""

import re

from fastapi.testclient import TestClient

from website.app import create_app
from website.config import Settings

_SHA = "0123456789abcdef0123456789abcdef01234567"


def test_about_page(client: TestClient) -> None:
    """The About page states the licence, source, cookies and credits."""
    response = client.get("/about")
    assert response.status_code == 200
    html = response.text
    assert re.search(r"<title>About · Tim(&#39;|')s Page</title>", html)
    assert "<h1>About</h1>" in html
    assert re.search(
        r'<a href="https://www\.gnu\.org/licenses/agpl-3\.0\.html"[^>]*>'
        r"GNU Affero General Public License v3\.0</a>",
        html,
    )
    source = re.search(r'<a href="https://github\.com/tjh90/website"[^>]*>', html)
    assert source
    assert 'target="_blank"' in source.group(0)
    assert 'rel="noopener noreferrer"' in source.group(0)
    assert "This site does not use cookies." in html
    assert re.search(r"<h2[^>]*>Credits</h2>", html)
    assert 'href="https://fontawesome.com"' in html
    assert 'href="https://creativecommons.org/licenses/by/4.0/"' in html
    assert re.search(r"Alfred Sisley, Lady(&#39;|')s Cove \(1897\), public domain", html)
    assert "Running revision" not in html


def test_about_page_with_revision() -> None:
    """A known revision is shown in short form and linked to the source."""
    with TestClient(create_app(Settings(revision=_SHA))) as client:
        html = client.get("/about").text
    assert "Running revision" in html
    assert f'href="https://github.com/tjh90/website/tree/{_SHA}"' in html
    assert "<code>0123456</code>" in html
