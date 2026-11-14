"""Merge gate for the shipped recipe collection (research R6).

Loads the real ``src/website/recipes`` folder exactly as the site does at start-up. It runs in the
CI ``test`` job, so a pull request with an invalid recipe or an ingredient missing from
``vocabulary.yaml`` fails CI. Authors can run it locally:

    uv run pytest tests/unit/test_shipped_recipes.py

On failure it shows only the report, one ``<file>: <message>`` line per problem.
"""

import pytest

from website.config import Settings
from website.cookbook import RecipeCollectionError, load_collection


def test_shipped_recipes_are_valid() -> None:
    """Every shipped recipe is valid against the vocabulary, and there is at least one."""
    report = ""
    try:
        collection = load_collection(Settings().recipes_dir)
    except RecipeCollectionError as error:
        report = str(error)
    if report:  # Fail outside the handler so pytest shows only the report, not the traceback.
        pytest.fail(report, pytrace=False)
    assert collection.recipes
