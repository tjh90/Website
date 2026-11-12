"""Unit tests for :mod:`website.config`."""

import logging

import pytest

from website.config import Settings

_FULL_SHA = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ambient environment variables do not leak into settings."""
    monkeypatch.delenv("WEBSITE_REVISION", raising=False)
    monkeypatch.delenv("WEBSITE_REPOSITORY_URL", raising=False)


def test_revision_defaults_to_none() -> None:
    """No revision is configured by default."""
    assert Settings().revision is None


def test_empty_revision_is_none() -> None:
    """An empty revision string is treated as unknown."""
    assert Settings(revision="").revision is None


def test_short_revision_is_normalised_to_lower_case() -> None:
    """A valid short SHA is accepted and lower-cased."""
    assert Settings(revision="ABCDEF1").revision == "abcdef1"


def test_full_revision_is_accepted() -> None:
    """A 40-character SHA is accepted unchanged."""
    assert Settings(revision=_FULL_SHA).revision == _FULL_SHA


@pytest.mark.parametrize("value", ["xyz1234", "abc12", _FULL_SHA + "a"])
def test_invalid_revision_is_ignored_with_warning(
    value: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid revisions become ``None`` and log a warning."""
    with caplog.at_level(logging.WARNING, logger="website.config"):
        settings = Settings(revision=value)
    assert settings.revision is None
    assert any("WEBSITE_REVISION" in record.getMessage() for record in caplog.records)


def test_repository_url_default() -> None:
    """The repository URL points at the public source by default."""
    assert str(Settings().repository_url).rstrip("/") == "https://github.com/tjh90/website"


def test_environment_variables_are_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings are read from ``WEBSITE_``-prefixed environment variables."""
    monkeypatch.setenv("WEBSITE_REVISION", "abcdef1")
    monkeypatch.setenv("WEBSITE_REPOSITORY_URL", "https://example.com/repo")
    settings = Settings()
    assert settings.revision == "abcdef1"
    assert str(settings.repository_url).rstrip("/") == "https://example.com/repo"
