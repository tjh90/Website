package net.tjh90.website.core.recipes;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

public class RecipesLoaderTest {

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
  public void contentIsParsedFromEachRecipeFile() {
    assertTrue(recipe("Mojito").toHtml().contains("<h1>Mojito</h1>"));
    assertTrue(recipe("Spaghetti Carbonara").toHtml().contains("<h1>Spaghetti Carbonara</h1>"));
    assertTrue(recipe("Roasted Potatoes").toHtml().contains("<h1>Roasted Potatoes</h1>"));
    assertFalse(recipe("Mojito").toHtml().contains("---"));
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
}
