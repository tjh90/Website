package net.tjh90.website.core.recipes;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.StringJoiner;
import org.junit.jupiter.api.Test;

public class RecipeParserTest {

  private static final String TEST_RECIPE_NAME = "Tap water";
  private static final Recipe.Type TEST_RECIPE_TYPE = Recipe.Type.DRINK;
  private static final String INGREDIENT_NAME_WATER = "Water";
  private static final String INGREDIENT_WATER = INGREDIENT_NAME_WATER;
  private static final String INGREDIENT_NAME_ICE = "Ice cubes";
  private static final String INGREDIENT_ICE =
      String.format("[OPTIONAL] %s (3)", INGREDIENT_NAME_ICE);
  private static final String INGREDIENT_NAME_STRAW = "Straw";
  private static final String INGREDIENT_STRAW = String.format("%s (2)", INGREDIENT_NAME_STRAW);
  private static final String INGREDIENT_NAME_DRUGS = "Cocaine/Heroin";
  private static final String INGREDIENT_DRUGS =
      String.format("%s (1 tbsp)", INGREDIENT_NAME_DRUGS);
  private static final List<String> TEST_RECIPE_INGREDIENTS =
      List.of(INGREDIENT_WATER, INGREDIENT_ICE, INGREDIENT_STRAW, INGREDIENT_DRUGS);

  private static final String TEST_RECIPE = createTestRecipe();

  private static String createTestRecipe() {
    StringJoiner sj = new StringJoiner("\n");

    sj.add("---");
    sj.add(String.format("type: %s", TEST_RECIPE_TYPE.name().toLowerCase()));
    sj.add("---");

    sj.add(String.format("# %s", TEST_RECIPE_NAME));
    sj.add("");

    sj.add("## Ingredients");
    for (String ingredient : TEST_RECIPE_INGREDIENTS) {
      sj.add(String.format("- %s", ingredient));
    }
    sj.add("");

    sj.add("## Method");
    sj.add("1. Pour water into a glass.");
    sj.add("1. Add ice cubes if desired.");
    sj.add("1. Add the drugs.");
    sj.add("1. Add the straws and stir.");

    return sj.toString();
  }

  @Test
  public void recipeNameComesFromTheTitle() {
    Recipe recipe = parse(TEST_RECIPE);

    assertEquals(TEST_RECIPE_NAME, recipe.name());
  }

  @Test
  public void recipeTypeComesFromTheYamlFrontMatter() {
    Recipe recipe = parse(TEST_RECIPE);

    assertEquals(TEST_RECIPE_TYPE, recipe.type());
  }

  @Test
  public void recipeContentIsTheEntireMarkdown() {
    Recipe recipe = RecipeParser.parse(TEST_RECIPE).orElseThrow();

    assertEquals(TEST_RECIPE, recipe.content());
  }

  @Test
  public void simpleIngredientHasNoOptionalFlagOrAmount() {
    Recipe recipe = parse(TEST_RECIPE);

    Ingredient water = find(recipe.ingredients(), INGREDIENT_NAME_WATER);
    assertFalse(water.isOptional());
    assertNull(water.getQuantity());
  }

  @Test
  public void optionalMarkerIsParsed() {
    Recipe recipe = parse(TEST_RECIPE);

    Ingredient ice = find(recipe.ingredients(), INGREDIENT_NAME_ICE);
    assertTrue(ice.isOptional());
  }

  @Test
  public void quantityIsParsed() {
    Recipe recipe = parse(TEST_RECIPE);

    Ingredient straw = find(recipe.ingredients(), INGREDIENT_NAME_STRAW);
    assertEquals("2", straw.getQuantity());
  }

  @Test
  public void forwardSlashSeparatedNamesBecomeAnIngredientChoice() {
    Recipe recipe = parse(TEST_RECIPE);

    Ingredient drugs = find(recipe.ingredients(), INGREDIENT_NAME_DRUGS);

    assertTrue(drugs instanceof IngredientChoice);
    assertTrue(drugs.matches("Cocaine"));
    assertFalse(drugs.matches(INGREDIENT_NAME_DRUGS));
  }

  private static Recipe parse(String recipeMarkdown) {
    return RecipeParser.parse(recipeMarkdown).orElseThrow();
  }

  private static Ingredient find(List<Ingredient> ingredients, String name) {
    return ingredients.stream()
        .filter(ingredient -> name.equals(ingredient.getName()))
        .findFirst()
        .orElseThrow(
            () -> new AssertionError("No ingredient named " + name + " in " + ingredients));
  }
}
