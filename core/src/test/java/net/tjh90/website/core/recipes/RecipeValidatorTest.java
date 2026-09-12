package net.tjh90.website.core.recipes;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

public class RecipeValidatorTest {

  private static final Set<String> ALLOWED_INGREDIENTS =
      Set.of("Water", "Ice cubes", "Lime", "Sugar", "Simple syrup");

  private static final Recipe SIMPLE_RECIPE =
      new Recipe("Tap water", Recipe.Type.DRINK, List.of(ingredient("Water")), "");

  private final RecipeValidator validator = new RecipeValidator(ALLOWED_INGREDIENTS);

  @Test
  public void validatesRecipesWhoseIngredientsAreAllAllowlisted() {
    Recipe recipe =
        new Recipe(
            "Mojito",
            Recipe.Type.DRINK,
            List.of(ingredient("Water"), ingredient("Ice cubes"), ingredient("Lime")),
            "");

    assertDoesNotThrow(() -> validator.validate(List.of(SIMPLE_RECIPE, recipe)));
  }

  @Test
  public void throwsWhenAnIngredientIsNotInTheAllowlist() {
    Recipe recipe =
        new Recipe(
            "Suspicious Drink",
            Recipe.Type.DRINK,
            List.of(ingredient("Water"), ingredient("Cocaine")),
            "");

    RecipeException exception =
        assertThrows(RecipeException.class, () -> validator.validate(List.of(recipe)));
    assertTrue(exception.getMessage().contains("Suspicious Drink"));
    assertTrue(exception.getMessage().contains("Cocaine"));
  }

  @Test
  public void choiceIngredientIsValidWhenAnyAlternativeIsAllowlisted() {
    Recipe recipe =
        new Recipe("Mojito", Recipe.Type.DRINK, List.of(choice("Water", "Cocaine")), "");

    assertDoesNotThrow(() -> validator.validate(List.of(recipe)));
  }

  @Test
  public void choiceIngredientIsInvalidWhenNoAlternativeIsAllowlisted() {
    Recipe recipe =
        new Recipe("Suspicious Drink", Recipe.Type.DRINK, List.of(choice("Cocaine", "Heroin")), "");

    RecipeException exception =
        assertThrows(RecipeException.class, () -> validator.validate(List.of(recipe)));
    assertTrue(exception.getMessage().contains("Cocaine/Heroin"));
  }

  @Test
  public void reportsEveryRecipeWithAnOffendingIngredient() {
    Recipe badDrink =
        new Recipe("Suspicious Drink", Recipe.Type.DRINK, List.of(ingredient("Cocaine")), "");
    Recipe badSide =
        new Recipe("Suspicious Side", Recipe.Type.SIDE, List.of(ingredient("Heroin")), "");

    RecipeException exception =
        assertThrows(RecipeException.class, () -> validator.validate(List.of(badDrink, badSide)));

    assertTrue(exception.getMessage().contains("Suspicious Drink"));
    assertTrue(exception.getMessage().contains("Cocaine"));
    assertTrue(exception.getMessage().contains("Suspicious Side"));
    assertTrue(exception.getMessage().contains("Heroin"));
  }

  @Test
  public void matchingIsCaseSensitive() {
    Recipe recipe =
        new Recipe("Water Mislabeled", Recipe.Type.DRINK, List.of(ingredient("water")), "");

    RecipeException exception =
        assertThrows(RecipeException.class, () -> validator.validate(List.of(recipe)));
    assertEquals(1, exception.getMessage().split("\n").length);
  }

  private static SimpleIngredient ingredient(String name) {
    return new SimpleIngredient(name, false, null);
  }

  private static IngredientChoice choice(String... names) {
    return new IngredientChoice(List.of(names), false, null);
  }
}
