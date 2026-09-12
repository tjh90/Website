package net.tjh90.website.core.recipes;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

public class RecipesLoaderTest {

  private static final String TEST_RESOURCE_DIR = "/recipes/";

  private List<Recipe> recipes;

  @BeforeEach
  void loadRecipesFromTheTestClasspath() {
    recipes = RecipesLoader.loadRecipes();
  }

  @Test
  public void loadsExactlyTheRecipesInTheTestResources() {
    assertEquals(Set.of("Mojito", "Spaghetti Carbonara", "Roasted Potatoes"), recipeNames());
  }

  @Test
  public void dropsAnInvalidRecipeFile() {
    assertFalse(recipeNames().contains("Not a Recipe"));
  }

  @Test
  public void parsesTheTypeFromTheYamlFrontMatter() {
    assertEquals(Recipe.Type.DRINK, recipe("Mojito").type());
    assertEquals(Recipe.Type.MEAL, recipe("Spaghetti Carbonara").type());
    assertEquals(Recipe.Type.SIDE, recipe("Roasted Potatoes").type());
  }

  @Test
  public void parsesOptionalFlagsQuantitiesAndChoices() {
    List<Ingredient> ingredients = recipe("Mojito").ingredients();

    assertTrue(find(ingredients, "Fresh mint leaves").isOptional());
    assertEquals("10 leaves", find(ingredients, "Fresh mint leaves").getQuantity());

    assertFalse(find(ingredients, "White rum").isOptional());
    assertEquals("60 ml", find(ingredients, "White rum").getQuantity());

    assertFalse(find(ingredients, "Lime").isOptional());
    assertNull(find(ingredients, "Lime").getQuantity());

    Ingredient sugar = find(ingredients, "Sugar/Simple syrup");
    assertTrue(sugar instanceof IngredientChoice);
    assertEquals("2 teaspoons", sugar.getQuantity());
    assertTrue(sugar.matches("Sugar"));
    assertTrue(sugar.matches("Simple syrup"));
  }

  @Test
  public void contentIsTheRawMarkdownOfTheRecipeFile() {
    assertEquals(readTestResource("TestMojito.md"), recipe("Mojito").content());
    assertEquals(
        readTestResource("TestSpaghettiCarbonara.md"), recipe("Spaghetti Carbonara").content());
    assertEquals(readTestResource("TestRoastedPotatoes.md"), recipe("Roasted Potatoes").content());
  }

  private Set<String> recipeNames() {
    return recipes.stream().map(Recipe::name).collect(Collectors.toSet());
  }

  private Recipe recipe(String name) {
    return recipes.stream()
        .filter(recipe -> name.equals(recipe.name()))
        .findFirst()
        .orElseThrow(
            () -> new AssertionError("No recipe named '" + name + "' in " + recipeNames()));
  }

  private static Ingredient find(List<Ingredient> ingredients, String name) {
    return ingredients.stream()
        .filter(ingredient -> name.equals(ingredient.getName()))
        .findFirst()
        .orElseThrow(
            () -> new AssertionError("No ingredient named " + name + " in " + ingredients));
  }

  private static String readTestResource(String fileName) {
    String path = TEST_RESOURCE_DIR + fileName;
    try (InputStream is = RecipesLoaderTest.class.getResourceAsStream(path)) {
      if (is == null) {
        throw new AssertionError("Missing test resource: " + path);
      }

      try (BufferedReader br =
          new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
        return br.lines().reduce("", (content, line) -> content + line + "\n");
      }
    } catch (IOException e) {
      throw new AssertionError("Failed to read test resource: " + path, e);
    }
  }
}
