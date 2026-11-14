"""Domain logic for the recipe collection.

Recipes are markdown files checked against a master vocabulary of types and ingredients
(``vocabulary.yaml``). Everything is loaded once into an immutable :class:`RecipeCollection`;
:func:`filter_recipes` answers the list page's filters. This module is pure: it has no web
framework imports.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Final

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.front_matter import front_matter_plugin
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    StringConstraints,
    ValidationError,
    field_validator,
)
from pydantic_core import ErrorDetails

VOCABULARY_FILE: Final = "vocabulary.yaml"
README_FILE: Final = "README.md"
MAX_QUERY_LENGTH: Final = 100

_SLUG_PATTERN: Final = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_INGREDIENT_PATTERN: Final = re.compile(
    r"^(?P<optional>\[OPTIONAL\]\s+)?(?P<names>[^()]+?)(?:\s*\((?P<amount>[^()]*)\))?$"
)
_EMPTY_AMOUNT_PATTERN: Final = re.compile(r"\(\s*\)\s*$")
_INGREDIENTS_SECTION: Final = "Ingredients"
_METHOD_SECTION: Final = "Method"
_SECTIONS: Final = (_INGREDIENTS_SECTION, _METHOD_SECTION)
_FLAT_LIST_MESSAGE: Final = "ingredients must be a single bulleted list, one ingredient per item"
_SUMMARY_SEPARATOR: Final = " · "

# Raw HTML is shown as text and images are disabled; markdown-it also refuses
# javascript:, vbscript:, file: and data: links. This is what makes ``method_html`` safe.
_MARKDOWN: Final = (
    MarkdownIt("commonmark", {"html": False}).use(front_matter_plugin).disable("image")
)

type _Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# --- Vocabulary -----------------------------------------------------------------------------


def _duplicates(names: Iterable[str]) -> list[str]:
    """Return the names that repeat an earlier name, ignoring case.

    Args:
        names: Names in file order.

    Returns:
        Every repeat, as written, in order.
    """
    seen: set[str] = set()
    repeats: list[str] = []
    for name in names:
        key = name.casefold()
        if key in seen:
            repeats.append(name)
        seen.add(key)
    return repeats


class Vocabulary(BaseModel):
    """The recognised recipe types and the master ingredient list, from ``vocabulary.yaml``.

    Attributes:
        types: Recipe types, in filter order.
        ingredients: Ingredient names with their display spelling, in suggestion order.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    types: list[_Name] = Field(min_length=1)
    ingredients: list[_Name] = Field(min_length=1)

    _type_lookup: dict[str, str] = PrivateAttr(default_factory=dict)
    _ingredient_lookup: dict[str, str] = PrivateAttr(default_factory=dict)

    @field_validator("types")
    @classmethod
    def _check_types(cls, types: list[str]) -> list[str]:
        """Reject duplicate types.

        Args:
            types: The trimmed types.

        Returns:
            The types unchanged.

        Raises:
            ValueError: If a type is listed twice, ignoring case.
        """
        problems = [f'duplicate type "{name}"' for name in _duplicates(types)]
        if problems:
            raise ValueError("; ".join(problems))
        return types

    @field_validator("ingredients")
    @classmethod
    def _check_ingredients(cls, ingredients: list[str]) -> list[str]:
        """Reject duplicate ingredients and names the recipe grammar cannot express.

        Args:
            ingredients: The trimmed ingredient names.

        Returns:
            The ingredients unchanged.

        Raises:
            ValueError: If an ingredient is listed twice or contains ``/`` or parentheses.
        """
        problems = [
            f'ingredient "{name}" must not contain "/" or parentheses'
            for name in ingredients
            if any(character in name for character in "/()")
        ]
        problems += [f'duplicate ingredient "{name}"' for name in _duplicates(ingredients)]
        if problems:
            raise ValueError("; ".join(problems))
        return ingredients

    def model_post_init(self, context: object, /) -> None:
        """Build the case-insensitive lookups.

        Args:
            context: Unused validation context.
        """
        self._type_lookup = {name.casefold(): name for name in self.types}
        self._ingredient_lookup = {name.casefold(): name for name in self.ingredients}

    def canonical_type(self, name: str) -> str | None:
        """Look up a type, ignoring case and surrounding spaces.

        Args:
            name: The type as written.

        Returns:
            The vocabulary spelling, or ``None`` if it is not a type.
        """
        return self._type_lookup.get(name.strip().casefold())

    def canonical_ingredient(self, name: str) -> str | None:
        """Look up an ingredient, ignoring case and surrounding spaces.

        Args:
            name: The ingredient as written.

        Returns:
            The vocabulary spelling, or ``None`` if it is not in the master list.
        """
        return self._ingredient_lookup.get(name.strip().casefold())


# --- Recipes --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RecipeType:
    """A recipe type from the vocabulary.

    Attributes:
        name: Display name, e.g. ``Drink``.
        key: Lower-case form used in query strings, e.g. ``drink``.
    """

    name: str
    key: str = field(init=False)

    def __post_init__(self) -> None:
        """Derive the query-string key from the name."""
        object.__setattr__(self, "key", self.name.casefold())


@dataclass(frozen=True, slots=True)
class IngredientEntry:
    """One line of a recipe's ingredient list.

    Attributes:
        alternatives: Interchangeable ingredients with vocabulary spelling, in the order written.
        amount: Free-text amount, if given.
        optional: Whether the line was marked ``[OPTIONAL]``.
    """

    alternatives: tuple[str, ...]
    amount: str | None
    optional: bool

    @property
    def display_name(self) -> str:
        """The alternatives as prose: "A", "A or B", or "A, B or C"."""
        if len(self.alternatives) == 1:
            return self.alternatives[0]
        return f"{', '.join(self.alternatives[:-1])} or {self.alternatives[-1]}"


@dataclass(frozen=True, slots=True)
class Recipe:
    """A validated recipe.

    Attributes:
        slug: File name without ``.md``; the recipe's address is ``/recipes/{slug}``.
        name: Recipe name from the ``#`` heading.
        type: Recipe type.
        ingredients: Ingredient lines, in the order written.
        method_html: Safe HTML rendered from the method section.
        source: File the recipe was read from.
    """

    slug: str
    name: str
    type: RecipeType
    ingredients: tuple[IngredientEntry, ...]
    method_html: str
    source: Path

    @property
    def ingredient_keys(self) -> frozenset[str]:
        """Lower-case names of every ingredient, including alternatives and optional ones."""
        return frozenset(
            name.casefold() for entry in self.ingredients for name in entry.alternatives
        )

    @property
    def ingredient_summary(self) -> str:
        """The ingredients on one line, for the recipe list."""
        return _SUMMARY_SEPARATOR.join(entry.display_name for entry in self.ingredients)


@dataclass(frozen=True)
class RecipeCollection:
    """Every recipe, with the vocabulary they were checked against.

    Attributes:
        recipes: Recipes sorted by name, ignoring case.
        vocabulary: The vocabulary.
    """

    recipes: tuple[Recipe, ...]
    vocabulary: Vocabulary

    @cached_property
    def by_slug(self) -> Mapping[str, Recipe]:
        """Recipes keyed by slug."""
        return MappingProxyType({recipe.slug: recipe for recipe in self.recipes})

    @cached_property
    def types_in_use(self) -> tuple[RecipeType, ...]:
        """Types with at least one recipe, in vocabulary order."""
        used = {recipe.type.name for recipe in self.recipes}
        return tuple(RecipeType(name) for name in self.vocabulary.types if name in used)

    @property
    def ingredient_names(self) -> tuple[str, ...]:
        """Every vocabulary ingredient, in vocabulary order."""
        return tuple(self.vocabulary.ingredients)


@dataclass(frozen=True, slots=True)
class RecipeProblem:
    """A problem found while loading the collection.

    Attributes:
        source: The offending file.
        message: What is wrong, for the author.
    """

    source: Path
    message: str


class RecipeCollectionError(Exception):
    """The recipe collection is invalid.

    Attributes:
        problems: Every problem found, across all files.
    """

    def __init__(self, problems: Sequence[RecipeProblem]) -> None:
        """Create the error.

        Args:
            problems: Every problem found.
        """
        self.problems: tuple[RecipeProblem, ...] = tuple(problems)
        super().__init__(str(self))

    def __str__(self) -> str:
        """Report every problem, one ``<file>: <message>`` line each, sorted by file name.

        Returns:
            The report.
        """
        count = len(self.problems)
        lines = [f"The recipe collection has {count} problem{'' if count == 1 else 's'}:"]
        lines += [
            f"{problem.source.name}: {problem.message}"
            for problem in sorted(self.problems, key=lambda problem: problem.source.name)
        ]
        return "\n".join(lines)


# --- Loading --------------------------------------------------------------------------------


class RecipePreamble(BaseModel):
    """The YAML block at the top of a recipe file.

    Attributes:
        type: Recipe type as written.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    type: str


def _describe(error: ErrorDetails) -> str:
    """Turn a Pydantic error into an author-facing message.

    Args:
        error: One validation error.

    Returns:
        The message, prefixed with the field location when it helps.
    """
    if error["type"] == "value_error":
        return str(error.get("ctx", {}).get("error", error["msg"]))
    location = ".".join(str(part) for part in error["loc"])
    return f"{location}: {error['msg']}" if location else error["msg"]


def _load_vocabulary(path: Path) -> tuple[Vocabulary | None, list[str]]:
    """Read and validate the vocabulary file.

    Args:
        path: Path to ``vocabulary.yaml``.

    Returns:
        The vocabulary, or ``None`` with the problems found.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None, ["vocabulary file is missing"]
    except UnicodeDecodeError:
        return None, ["file is not valid UTF-8 text"]
    except yaml.YAMLError as error:
        return None, [f"vocabulary is not valid YAML: {error}"]
    if not isinstance(data, dict):
        return None, ['vocabulary must be a mapping with "types" and "ingredients"']
    try:
        return Vocabulary.model_validate(data), []
    except ValidationError as error:
        return None, [_describe(detail) for detail in error.errors()]


@dataclass(slots=True)
class _Section:
    """A ``##`` section of a recipe file.

    Attributes:
        title: Heading text as written.
        tokens: Top-level tokens between this heading and the next.
    """

    title: str
    tokens: list[Token]


def _inline_text(tokens: Sequence[Token], index: int) -> str:
    """Return the text of the heading that opens at ``index``.

    Args:
        tokens: The token stream.
        index: Index of a ``heading_open`` token.

    Returns:
        The trimmed heading text.
    """
    return tokens[index + 1].content.strip()


def _parse_preamble(
    tokens: Sequence[Token], vocabulary: Vocabulary
) -> tuple[str | None, str | None]:
    """Find the recipe type in the preamble.

    Args:
        tokens: The token stream.
        vocabulary: The vocabulary.

    Returns:
        The vocabulary spelling of the type, or a problem message.
    """
    if not tokens or tokens[0].type != "front_matter":
        return None, 'preamble is missing: start the file with "type: ..." between "---" lines'
    try:
        data = yaml.safe_load(tokens[0].content)
    except yaml.YAMLError as error:
        return None, f"preamble is not valid YAML: {error}"
    try:
        preamble = RecipePreamble.model_validate(data)
    except ValidationError:
        return None, 'preamble must contain only "type", as text'
    canonical = vocabulary.canonical_type(preamble.type)
    if canonical is None:
        return None, f'unknown type "{preamble.type}"'
    return canonical, None


def _split_structure(
    tokens: Sequence[Token],
) -> tuple[str | None, list[_Section], list[str]]:
    """Split the token stream into the name heading and the ``##`` sections.

    Args:
        tokens: The token stream, after any preamble.

    Returns:
        The recipe name, the sections in file order, and any problems.
    """
    problems: list[str] = []
    names: list[str] = []
    sections: list[_Section] = []
    stray = False
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.level == 0 and token.type == "heading_open" and token.tag in {"h1", "h2"}:
            text = _inline_text(tokens, index)
            if token.tag == "h1":
                names.append(text)
                if sections:
                    problems.append('the "#" recipe name heading must come before the sections')
            else:
                sections.append(_Section(text, []))
            index += 3
            continue
        if sections:
            sections[-1].tokens.append(token)
        elif token.type != "front_matter":
            stray = True
        index += 1
    if len(names) != 1:
        problems.append(f'expected exactly one "#" recipe name heading, found {len(names)}')
    elif not names[0]:
        problems.append('the "#" recipe name heading is empty')
    if stray:
        problems.append('only the "#" recipe name heading may come before "## Ingredients"')
    return (names[0] if len(names) == 1 and names[0] else None), sections, problems


def _check_sections(sections: Sequence[_Section]) -> list[str]:
    """Check that the sections are exactly Ingredients then Method.

    Args:
        sections: The sections in file order.

    Returns:
        Any problems.
    """
    problems = [
        f'unknown section "{section.title}"'
        for section in sections
        if section.title.casefold() not in {name.casefold() for name in _SECTIONS}
    ]
    if problems:  # A misspelt heading also leaves a section missing; report only the typo.
        return problems
    known = [section.title.casefold() for section in sections]
    missing = [name for name in _SECTIONS if name.casefold() not in known]
    problems += [f'missing section "{name}"' for name in missing]
    if not missing and known != [name.casefold() for name in _SECTIONS]:
        problems.append('sections must be "## Ingredients" then "## Method", each once')
    return problems


def _ingredient_lines(tokens: Sequence[Token]) -> tuple[list[str], str | None]:
    """Extract the item texts of the ingredients' single, flat bulleted list.

    Args:
        tokens: Tokens of the Ingredients section.

    Returns:
        The raw item texts, or a problem message.
    """
    if (
        not tokens
        or tokens[0].type != "bullet_list_open"
        or tokens[-1].type != "bullet_list_close"
        or any(token.level == 0 for token in tokens[1:-1])
    ):
        return [], _FLAT_LIST_MESSAGE
    lines: list[str] = []
    for token in tokens[1:-1]:
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            return [], _FLAT_LIST_MESSAGE
        if token.type == "list_item_open":
            lines.append("")
        elif token.type == "inline":
            if lines[-1]:
                return [], _FLAT_LIST_MESSAGE
            lines[-1] = token.content.strip()
        elif token.type not in {"paragraph_open", "paragraph_close", "list_item_close"}:
            return [], _FLAT_LIST_MESSAGE
    return lines, None


def _parse_ingredient(
    line: str, vocabulary: Vocabulary
) -> tuple[IngredientEntry | None, list[str]]:
    """Parse one ingredient line.

    Args:
        line: The item text, e.g. ``[OPTIONAL] Champagne/Prosecco (100 ml)``.
        vocabulary: The vocabulary.

    Returns:
        The entry, or ``None`` with the problems found.
    """
    if not line:
        return None, ["empty ingredient line"]
    if "\n" in line:
        return None, [f'ingredient line "{line.splitlines()[0]}" must be on one line']
    if line.count("(") != line.count(")"):
        return None, [f'ingredient line "{line}" has unbalanced parentheses']
    if _EMPTY_AMOUNT_PATTERN.search(line):
        return None, [f'ingredient line "{line}" has an empty amount']
    match = _INGREDIENT_PATTERN.fullmatch(line)
    if match is None:
        return None, [
            f'ingredient line "{line}" is not in the form "[OPTIONAL] Name/Alternative (amount)"'
        ]
    written = [name.strip() for name in match["names"].split("/")]
    if not all(written):
        return None, [f'ingredient line "{line}" has an empty alternative']
    problems = [
        f'unknown ingredient "{name}"'
        for name in written
        if vocabulary.canonical_ingredient(name) is None
    ]
    if problems:
        return None, problems
    alternatives = tuple(vocabulary.canonical_ingredient(name) or name for name in written)
    problems = [
        f'ingredient line "{line}" lists "{name}" more than once'
        for name in _duplicates(alternatives)
    ]
    if problems:
        return None, problems
    amount = match["amount"].strip() if match["amount"] is not None else None
    return IngredientEntry(alternatives, amount, optional=match["optional"] is not None), []


def _parse_recipe(path: Path, vocabulary: Vocabulary) -> tuple[Recipe | None, list[str]]:
    """Parse and check one recipe file.

    Args:
        path: The recipe file.
        vocabulary: The vocabulary.

    Returns:
        The recipe, or ``None`` with every problem found in the file.
    """
    problems: list[str] = []
    if not _SLUG_PATTERN.fullmatch(path.stem):
        problems.append("file name must be lower-case words joined by hyphens, e.g. french-75.md")
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, [*problems, "file is not valid UTF-8 text"]
    tokens = _MARKDOWN.parse(text)

    type_name, problem = _parse_preamble(tokens, vocabulary)
    if problem:
        problems.append(problem)
    name, sections, structure_problems = _split_structure(tokens)
    problems += structure_problems
    section_problems = _check_sections(sections)
    problems += section_problems

    entries: list[IngredientEntry] = []
    method_html = ""
    if not section_problems:
        by_title = {section.title.casefold(): section for section in sections}
        lines, problem = _ingredient_lines(by_title["ingredients"].tokens)
        if problem:
            problems.append(problem)
        for line in lines:
            entry, line_problems = _parse_ingredient(line, vocabulary)
            problems += line_problems
            if entry is not None:
                entries.append(entry)
        method_tokens = by_title["method"].tokens
        if method_tokens:
            method_html = _MARKDOWN.renderer.render(method_tokens, _MARKDOWN.options, {})
        else:
            problems.append("method section is empty")

    if problems or type_name is None or name is None:
        return None, problems
    return Recipe(
        slug=path.stem,
        name=name,
        type=RecipeType(type_name),
        ingredients=tuple(entries),
        method_html=method_html,
        source=path,
    ), []


def _duplicate_name_problems(recipes: Sequence[Recipe]) -> list[RecipeProblem]:
    """Report recipes whose names are already used, ignoring case.

    Args:
        recipes: Recipes in file order.

    Returns:
        One problem per repeat, naming the file that used the name first.
    """
    first: dict[str, Recipe] = {}
    problems: list[RecipeProblem] = []
    for recipe in recipes:
        earlier = first.setdefault(recipe.name.casefold(), recipe)
        if earlier is not recipe:
            message = f'recipe name "{recipe.name}" is also used by {earlier.source.name}'
            problems.append(RecipeProblem(recipe.source, message))
    return problems


def load_collection(directory: Path) -> RecipeCollection:
    """Load and check every recipe in a folder.

    Every file is checked before anything is raised, so one run reports every problem.

    Args:
        directory: Folder holding ``vocabulary.yaml`` and the ``*.md`` recipes.

    Returns:
        The collection, sorted by recipe name.

    Raises:
        RecipeCollectionError: If the vocabulary or any recipe is invalid.
    """
    vocabulary_path = directory / VOCABULARY_FILE
    vocabulary, messages = _load_vocabulary(vocabulary_path)
    if vocabulary is None:
        raise RecipeCollectionError([RecipeProblem(vocabulary_path, m) for m in messages])

    problems: list[RecipeProblem] = []
    recipes: list[Recipe] = []
    for path in sorted(directory.glob("*.md")):
        if path.name == README_FILE:
            continue
        recipe, messages = _parse_recipe(path, vocabulary)
        problems += [RecipeProblem(path, message) for message in messages]
        if recipe is not None:
            recipes.append(recipe)
    problems += _duplicate_name_problems(recipes)
    if problems:
        raise RecipeCollectionError(problems)
    recipes.sort(key=lambda recipe: (recipe.name.casefold(), recipe.slug))
    return RecipeCollection(tuple(recipes), vocabulary)


# --- Filtering ------------------------------------------------------------------------------


def _clean_text(value: object) -> str:
    """Trim a free-text filter and cap its length.

    Args:
        value: Raw query value.

    Returns:
        The cleaned text; anything that is not text becomes ``""``.
    """
    if isinstance(value, list | tuple):
        value = value[-1] if value else ""
    return value.strip()[:MAX_QUERY_LENGTH] if isinstance(value, str) else ""


class RecipeQuery(BaseModel):
    """The list page's filters, from the query string.

    Parsing is lenient: odd values become "no filter" rather than an error.

    Attributes:
        type: Lower-case type keys; any one of them matches. Empty means every type.
        name: Text the recipe name must contain, ignoring case.
        ingredient: An ingredient the recipe must use.
    """

    type: list[str] = []
    name: str = ""
    ingredient: str = ""

    @field_validator("type", mode="before")
    @classmethod
    def _clean_types(cls, value: object) -> list[str]:
        """Lower-case and trim the types, dropping anything that is not text.

        Args:
            value: Raw query value or values.

        Returns:
            The cleaned type keys.
        """
        values = value if isinstance(value, list | tuple) else [value]
        return [item.strip().casefold() for item in values if isinstance(item, str)]

    @field_validator("name", "ingredient", mode="before")
    @classmethod
    def _clean(cls, value: object) -> str:
        """Trim and cap the free-text filters.

        Args:
            value: Raw query value.

        Returns:
            The cleaned text.
        """
        return _clean_text(value)


@dataclass(frozen=True, slots=True)
class RecipeSearch:
    """The result of filtering the collection.

    Attributes:
        query: The filters applied, with unknown types removed.
        recipes: Matching recipes, in collection order.
        is_filtered: Whether any filter is active.
        active_filter_count: Ticked types, plus one each for a name and an ingredient.
    """

    query: RecipeQuery
    recipes: tuple[Recipe, ...]
    is_filtered: bool
    active_filter_count: int


def filter_recipes(collection: RecipeCollection, query: RecipeQuery) -> RecipeSearch:
    """Filter the collection.

    Filters combine with AND. Types match any ticked type, names match a case-insensitive
    substring, and an ingredient must be a vocabulary name used by the recipe (alternatives and
    optional ingredients count). An ingredient not in the vocabulary matches nothing.

    Args:
        collection: The recipe collection.
        query: The filters.

    Returns:
        The matching recipes and a summary of the filters.
    """
    type_keys = {recipe_type.key for recipe_type in collection.types_in_use}
    types = list(dict.fromkeys(key for key in query.type if key in type_keys))
    cleaned = query.model_copy(update={"type": types})
    name = cleaned.name.casefold()
    ingredient = cleaned.ingredient.casefold()
    count = len(types) + bool(name) + bool(ingredient)

    recipes: tuple[Recipe, ...] = ()
    if not ingredient or collection.vocabulary.canonical_ingredient(ingredient) is not None:
        recipes = tuple(
            recipe
            for recipe in collection.recipes
            if (not types or recipe.type.key in types)
            and name in recipe.name.casefold()
            and (not ingredient or ingredient in recipe.ingredient_keys)
        )
    return RecipeSearch(cleaned, recipes, is_filtered=count > 0, active_filter_count=count)
