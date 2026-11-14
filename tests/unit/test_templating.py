"""Unit tests for :mod:`website.templating`."""

import pytest
from starlette.requests import Request

from website.templating import is_htmx_request


def _request(headers: dict[str, str]) -> Request:
    """Build a minimal HTTP request with the given headers."""
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "method": "GET", "path": "/", "headers": raw})


@pytest.mark.parametrize(
    ("headers", "expected"),
    [({"HX-Request": "true"}, True), ({}, False), ({"HX-Request": "false"}, False)],
    ids=["true", "absent", "false"],
)
def test_is_htmx_request(headers: dict[str, str], *, expected: bool) -> None:
    """Only ``HX-Request: true`` marks a request as coming from htmx."""
    assert is_htmx_request(_request(headers)) is expected
