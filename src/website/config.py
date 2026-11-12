"""Runtime configuration."""

import logging
import re
from functools import lru_cache
from typing import Final

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOGGER: Final = logging.getLogger(__name__)
_REVISION_PATTERN: Final = re.compile(r"^[0-9a-f]{7,40}$")


class Settings(BaseSettings):
    """Application settings, read from ``WEBSITE_``-prefixed environment variables.

    Attributes:
        revision: Git revision the running site was built from, or ``None`` if unknown.
        repository_url: Public source repository of the site.
    """

    model_config = SettingsConfigDict(env_prefix="WEBSITE_")

    revision: str | None = None
    repository_url: HttpUrl = HttpUrl("https://github.com/tjh90/website")

    @field_validator("revision", mode="before")
    @classmethod
    def _validate_revision(cls, value: object) -> str | None:
        """Normalise the revision, discarding values that are not a hex SHA.

        Args:
            value: Raw revision value.

        Returns:
            The lower-cased revision, or ``None`` if empty or invalid.
        """
        if value is None:
            return None
        text = str(value).strip().lower()
        if not text:
            return None
        if not _REVISION_PATTERN.fullmatch(text):
            _LOGGER.warning("Ignoring invalid WEBSITE_REVISION value %r", value)
            return None
        return text


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once from the environment.

    Returns:
        The cached settings instance.
    """
    return Settings()
