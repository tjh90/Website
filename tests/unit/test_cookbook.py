"""Unit tests for :mod:`website.cookbook`."""

import re
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Final

import pytest

from tests.conftest import FIXTURE_RECIPES
from website.config import Settings
from website.cookbook import (
    IngredientEntry,
    Recipe,
    RecipeCollection,
    RecipeCollectionError,
    RecipeProblem,
    RecipeQuery,
    RecipeType,
    Vocabulary,
    filter_recipes,
    load_collection,
)

_VOCABULARY: Final = """\
types: [Drink, Breakfast, Snack]
ingredients: [Champagne, Prosecco, Cava, Gin, Lime, Vodka]
"""

_RECIPE: Final = """\
---
type: Drink
---

# Test Drink

## Ingredients

- Gin (50 ml)
- Lime

## Method

Stir.
"""


def _write(
    directory: Path, files: Mapping[str, str | bytes], vocabulary: str = _VOCABULARY
) -> Path:
    """Write a recipe folder.

    Args:
        directory: Folder to write into.
        files: File names mapped to their contents.
        vocabulary: Contents of ``vocabulary.yaml``.

    Returns:
        The folder.
    """
    (directory / "vocabulary.yaml").write_text(vocabulary, encoding="utf-8")
    for name, content in files.items():
        path = directory / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    return directory


def _problems(directory: Path) -> list[RecipeProblem]:
    """Load a folder that must be invalid.

    Args:
        directory: The recipe folder.

    Returns:
        The problems reported.
    """
    with pytest.raises(RecipeCollectionError) as raised:
        load_collection(directory)
    return list(raised.value.problems)


def _recipe_with(ingredients: str = "- Gin (50 ml)\n- Lime", recipe_type: str = "Drink") -> str:
    """Build a recipe file with the given ingredient lines and type.

    Args:
        ingredients: Markdown for the ingredients section.
        recipe_type: The preamble type.

    Returns:
        The recipe file contents.
    """
    return _RECIPE.replace("- Gin (50 ml)\n- Lime", ingredients).replace(
        "type: Drink", f"type: {recipe_type}"
    )


@pytest.fixture(scope="module")
def collection() -> RecipeCollection:
    """The valid fixture collection."""
    return load_collection(FIXTURE_RECIPES / "valid")


# --- Foundation ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("alternatives", "expected"),
    [
        (("Gin",), "Gin"),
        (("Gin", "Vodka"), "Gin or Vodka"),
        (("Champagne", "Prosecco", "Cava"), "Champagne, Prosecco or Cava"),
    ],
)
def test_display_name(alternatives: tuple[str, ...], expected: str) -> None:
    """Alternatives read as prose."""
    assert IngredientEntry(alternatives, None, optional=False).display_name == expected


def test_recipe_type_key_is_lower_case() -> None:
    """A type's query key is its lower-case name."""
    assert RecipeType("Breakfast").key == "breakfast"


def test_ingredient_keys_and_summary(collection: RecipeCollection) -> None:
    """Keys include alternatives and optional entries; the summary lists every entry."""
    french_75 = collection.by_slug["french-75"]
    assert french_75.ingredient_keys == {
        "elderflower cordial",
        "gin",
        "ice cubes",
        "lime",
        "champagne",
        "prosecco",
        "cava",
    }
    assert french_75.ingredient_summary == (
        "Elderflower cordial · Gin · Ice cubes · Lime · Champagne, Prosecco or Cava"
    )


def test_types_in_use_keep_vocabulary_order(collection: RecipeCollection) -> None:
    """Only types with recipes are offered, in vocabulary order (Snack and Dessert are unused)."""
    assert [t.name for t in collection.types_in_use] == ["Drink", "Breakfast"]


def test_ingredient_names_keep_vocabulary_order(collection: RecipeCollection) -> None:
    """Every vocabulary ingredient is suggested, used or not."""
    assert collection.ingredient_names[:3] == ("Aperol", "Bacon", "Bread")
    assert "Mint" in collection.ingredient_names


def test_error_report_lists_every_problem_sorted_by_file() -> None:
    """The error's text has a header and one ``file: message`` line per problem."""
    error = RecipeCollectionError(
        [RecipeProblem(Path("b.md"), "second"), RecipeProblem(Path("a.md"), "first")]
    )
    assert str(error).splitlines() == [
        "The recipe collection has 2 problems:",
        "a.md: first",
        "b.md: second",
    ]


def test_load_valid_collection(collection: RecipeCollection) -> None:
    """The fixture loads sorted by name, without README.md, and French 75 parses exactly."""
    assert [r.name for r in collection.recipes] == [
        "Aperol Spritz",
        "French 75",
        "Full English",
        "Moscow Mule",
    ]
    french_75 = collection.by_slug["french-75"]
    assert french_75.type == RecipeType("Drink")
    assert len(french_75.ingredients) == 5
    assert french_75.ingredients[0] == IngredientEntry(
        ("Elderflower cordial",), "10 ml", optional=True
    )
    assert french_75.ingredients[-1] == IngredientEntry(
        ("Champagne", "Prosecco", "Cava"), None, optional=False
    )
    assert "<ol>" in french_75.method_html
    assert french_75.method_html.count("<li>") == 4


def test_unsafe_content_is_neutralised() -> None:
    """Raw HTML is escaped, javascript: links are not linked and images are not rendered."""
    recipe = load_collection(FIXTURE_RECIPES / "unsafe").by_slug["unsafe"]
    assert "<script" not in recipe.method_html
    assert "&lt;script&gt;" in recipe.method_html
    assert 'href="javascript:' not in recipe.method_html
    assert "<img" not in recipe.method_html
    assert recipe.name == "Unsafe <b>name</b>"


# --- Structure (US2) -------------------------------------------------------------------------


_STRUCTURE_CASES: Final[list[tuple[str, str, str]]] = [
    ("no-preamble", _RECIPE.split("---\n", 2)[2], "preamble"),
    ("not-mapping", _RECIPE.replace("type: Drink", "- Drink"), "preamble"),
    ("extra-key", _RECIPE.replace("type: Drink", "type: Drink\nserves: 2"), 'only "type"'),
    ("bad-yaml", _RECIPE.replace("type: Drink", "type: [Drink"), "not valid YAML"),
    ("no-name", _RECIPE.replace("# Test Drink\n", ""), 'exactly one "#" recipe name heading'),
    ("two-names", _RECIPE.replace("# Test Drink\n", "# A\n\n# B\n"), "found 2"),
    ("no-method", _RECIPE.split("## Method")[0], 'missing section "Method"'),
    ("typo", _RECIPE.replace("## Ingredients", "## Ingrediants"), 'unknown section "Ingrediants"'),
    (
        "misordered",
        _RECIPE.replace("## Ingredients", "## TEMP")
        .replace("## Method", "## Ingredients")
        .replace("## TEMP", "## Method"),
        "section",
    ),
    ("duplicate", _RECIPE + "\n## Ingredients\n\n- Gin\n", "section"),
    ("paragraph", _recipe_with("Gin and lime"), "single bulleted list"),
    ("numbered", _recipe_with("1. Gin\n2. Lime"), "single bulleted list"),
    ("nested", _recipe_with("- Gin\n  - Lime"), "single bulleted list"),
    ("stray", _RECIPE.replace("# Test Drink\n", "# Test Drink\n\nA lovely drink.\n"), "before"),
    ("unbalanced", _recipe_with("- Gin (50 ml"), "unbalanced parentheses"),
    ("empty-amount", _recipe_with("- Gin ()"), "empty amount"),
    ("two-amounts", _recipe_with("- Gin (50 ml) (double)"), "is not in the form"),
    ("empty-alternative", _recipe_with("- Gin//Vodka"), "empty alternative"),
    ("repeated-alternative", _recipe_with("- Gin/gin"), 'lists "Gin" more than once'),
    ("lower-optional", _recipe_with("- [optional] Gin"), 'unknown ingredient "[optional] Gin"'),
    ("empty-method", _RECIPE.replace("Stir.\n", ""), "method section is empty"),
]


@pytest.mark.parametrize(
    ("content", "expected"),
    [case[1:] for case in _STRUCTURE_CASES],
    ids=[case[0] for case in _STRUCTURE_CASES],
)
def test_structural_problems(tmp_path: Path, content: str, expected: str) -> None:
    """Each authoring mistake gives exactly one problem naming the file."""
    problems = _problems(_write(tmp_path, {"broken.md": content}))
    assert len(problems) == 1, problems
    assert problems[0].source.name == "broken.md"
    assert expected in problems[0].message


def test_bad_file_name(tmp_path: Path) -> None:
    """File names must be lower-case words joined by hyphens."""
    problems = _problems(_write(tmp_path, {"French_75.md": _RECIPE}))
    assert [p.message for p in problems] == [
        "file name must be lower-case words joined by hyphens, e.g. french-75.md"
    ]


def test_non_utf8_file(tmp_path: Path) -> None:
    """A file that is not UTF-8 is reported, not crashed on."""
    problems = _problems(_write(tmp_path, {"latin.md": _RECIPE.encode("utf-8") + b"\xff\xfe"}))
    assert len(problems) == 1
    assert "UTF-8" in problems[0].message


def test_duplicate_names_name_both_files(tmp_path: Path) -> None:
    """Names that differ only in case clash, and the report names both files."""
    files = {
        "french-75.md": _RECIPE.replace("Test Drink", "French 75"),
        "french-seventy-five.md": _RECIPE.replace("Test Drink", "french 75"),
    }
    problems = _problems(_write(tmp_path, files))
    assert len(problems) == 1
    assert problems[0].source.name == "french-seventy-five.md"
    assert "is also used by french-75.md" in problems[0].message


def test_every_problem_reported_at_once(tmp_path: Path) -> None:
    """Problems in several files are all reported in one error (FR-008)."""
    files = {
        "one.md": _recipe_with("- Gin ()"),
        "two.md": _RECIPE.split("## Method")[0],
        "three.md": _recipe_with("- Limes"),
    }
    problems = _problems(_write(tmp_path, files))
    assert sorted(p.source.name for p in problems) == ["one.md", "three.md", "two.md"]


def test_readme_examples_are_valid(tmp_path: Path) -> None:
    """Every recipe example in the authoring guide loads with the real vocabulary (FR-005)."""
    recipes_dir = Settings().recipes_dir
    guide = (recipes_dir / "README.md").read_text(encoding="utf-8")
    examples = re.findall(r"```markdown\n(.*?)```", guide, flags=re.DOTALL)
    assert examples
    vocabulary = (recipes_dir / "vocabulary.yaml").read_text(encoding="utf-8")
    for index, example in enumerate(examples):
        folder = tmp_path / str(index)
        folder.mkdir()
        _write(folder, {"example.md": example}, vocabulary)
        assert len(load_collection(folder).recipes) == 1


# --- Filtering (US3) -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (RecipeQuery(), ["Aperol Spritz", "French 75", "Full English", "Moscow Mule"]),
        (RecipeQuery(type=["drink"]), ["Aperol Spritz", "French 75", "Moscow Mule"]),
        (
            RecipeQuery(type=["drink", "BREAKFAST"]),
            ["Aperol Spritz", "French 75", "Full English", "Moscow Mule"],
        ),
        (
            RecipeQuery(type=["bogus"]),
            ["Aperol Spritz", "French 75", "Full English", "Moscow Mule"],
        ),
        (RecipeQuery(name="FRENCH"), ["French 75"]),
        (RecipeQuery(name="  spritz "), ["Aperol Spritz"]),
        (RecipeQuery(ingredient="prosecco"), ["Aperol Spritz", "French 75"]),
        (RecipeQuery(ingredient="elderflower cordial"), ["French 75"]),
        (RecipeQuery(ingredient="mushroom"), ["Full English"]),
        (RecipeQuery(ingredient="gin"), ["French 75"]),
        (RecipeQuery(ingredient="mint"), []),
        (RecipeQuery(ingredient="limes"), []),
        (RecipeQuery(type=["breakfast"], ingredient="gin"), []),
    ],
)
def test_filter_recipes(
    collection: RecipeCollection, query: RecipeQuery, expected: list[str]
) -> None:
    """Filters match as documented and combine with AND."""
    assert [r.name for r in filter_recipes(collection, query).recipes] == expected


def test_filter_summary(collection: RecipeCollection) -> None:
    """Unknown types are dropped and active filters are counted."""
    unfiltered = filter_recipes(collection, RecipeQuery(type=["bogus"], name="  "))
    assert not unfiltered.is_filtered
    assert unfiltered.active_filter_count == 0
    assert unfiltered.query.type == []

    search = filter_recipes(
        collection, RecipeQuery(type=["drink", "breakfast", "dessert"], ingredient="gin")
    )
    assert search.is_filtered
    assert search.active_filter_count == 3
    assert search.query.type == ["drink", "breakfast"]


def test_query_is_lenient() -> None:
    """Long text is truncated and odd values never raise."""
    query = RecipeQuery.model_validate({"name": "x" * 150, "type": "Drink", "ingredient": 5})
    assert query.name == "x" * 100
    assert query.type == ["drink"]
    assert query.ingredient == ""


def test_500_recipes_load_and_filter_quickly(tmp_path: Path) -> None:
    """Loading 500 recipes takes under 5 s and filtering under 0.1 s (SC-002, SC-003)."""
    files = {f"recipe-{n}.md": _RECIPE.replace("Test Drink", f"Recipe {n}") for n in range(500)}
    _write(tmp_path, files)
    start = time.perf_counter()
    collection = load_collection(tmp_path)
    loaded = time.perf_counter()
    search = filter_recipes(collection, RecipeQuery(type=["drink"], name="9", ingredient="lime"))
    filtered = time.perf_counter()
    assert len(collection.recipes) == 500
    assert search.recipes
    assert loaded - start < 5
    assert filtered - loaded < 0.1


# --- Vocabulary (US4) ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("vocabulary", "expected"),
    [
        ("types: []\ningredients: [Gin]\n", "types"),
        ("types: [Drink]\ningredients: []\n", "ingredients"),
        ("types: [Drink]\ningredients: [Lime, 'lime ']\n", 'duplicate ingredient "lime"'),
        ("types: [Drink, drink]\ningredients: [Gin]\n", 'duplicate type "drink"'),
        ("types: [Drink]\ningredients: [Gin/Vodka]\n", 'must not contain "/" or parentheses'),
        ("types: [Drink]\ningredients: [Gin (dry)]\n", 'must not contain "/" or parentheses'),
        ("types: [Drink]\ningredients: [Gin]\nmethods: [Stir]\n", "methods"),
        ("types: [Drink\n", "not valid YAML"),
        ("- Drink\n", "mapping"),
    ],
)
def test_invalid_vocabulary(tmp_path: Path, vocabulary: str, expected: str) -> None:
    """A bad vocabulary is reported against vocabulary.yaml and recipes are not checked."""
    problems = _problems(_write(tmp_path, {"broken.md": "not a recipe"}, vocabulary))
    assert {p.source.name for p in problems} == {"vocabulary.yaml"}
    assert any(expected in p.message for p in problems), problems


def test_missing_vocabulary(tmp_path: Path) -> None:
    """A folder without vocabulary.yaml is reported."""
    (tmp_path / "test.md").write_text(_RECIPE, encoding="utf-8")
    problems = _problems(tmp_path)
    assert [(p.source.name, p.message) for p in problems] == [
        ("vocabulary.yaml", "vocabulary file is missing")
    ]


def test_vocabulary_lookups_ignore_case() -> None:
    """Lookups ignore case and surrounding spaces."""
    vocabulary = Vocabulary(types=[" Drink "], ingredients=["Ice cubes"])
    assert vocabulary.types == ["Drink"]
    assert vocabulary.canonical_type("DRINK") == "Drink"
    assert vocabulary.canonical_ingredient(" ice CUBES") == "Ice cubes"
    assert vocabulary.canonical_ingredient("Ice cube") is None


def test_unknown_ingredient_has_no_suggestion(tmp_path: Path) -> None:
    """An unlisted ingredient is named as written, with no "did you mean"."""
    problems = _problems(_write(tmp_path, {"test.md": _recipe_with("- Limes")}))
    assert [p.message for p in problems] == ['unknown ingredient "Limes"']


def test_only_the_misspelt_alternative_is_reported(tmp_path: Path) -> None:
    """Each alternative is checked on its own."""
    problems = _problems(_write(tmp_path, {"test.md": _recipe_with("- Champagne/Prosseco")}))
    assert [p.message for p in problems] == ['unknown ingredient "Prosseco"']


def test_unknown_type(tmp_path: Path) -> None:
    """An unlisted type is named as written."""
    problems = _problems(_write(tmp_path, {"test.md": _recipe_with(recipe_type="DRNK")}))
    assert [p.message for p in problems] == ['unknown type "DRNK"']


def test_names_use_vocabulary_spelling(tmp_path: Path) -> None:
    """Ingredients and types written in another case are shown with the vocabulary spelling."""
    folder = _write(tmp_path, {"test.md": _recipe_with("- gin\n- LIME", recipe_type="drink")})
    recipe: Recipe = load_collection(folder).recipes[0]
    assert recipe.type.name == "Drink"
    assert [entry.display_name for entry in recipe.ingredients] == ["Gin", "Lime"]
