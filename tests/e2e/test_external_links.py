"""Reachability checks for third-party links; run with ``pytest -m external``."""

import httpx2
import pytest

from website.content import EXTERNAL_LINKS, ExternalLink

pytestmark = pytest.mark.external


@pytest.mark.parametrize("link", EXTERNAL_LINKS, ids=lambda link: link.text)
def test_external_link_reachable(link: ExternalLink) -> None:
    """Each home page link resolves to a successful response."""
    response = httpx2.head(link.url, follow_redirects=True, timeout=15)
    if response.status_code in {403, 405}:
        response = httpx2.get(link.url, follow_redirects=True, timeout=15)
    assert response.status_code < 400, f"{link.url} returned {response.status_code}"
