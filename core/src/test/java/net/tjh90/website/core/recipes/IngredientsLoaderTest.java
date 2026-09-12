package net.tjh90.website.core.recipes;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Set;
import org.junit.jupiter.api.Test;

public class IngredientsLoaderTest {

  private static final Set<String> EXPECTED_INGREDIENTS =
      Set.of(
          "Eggs",
          "Fresh mint leaves",
          "Guanciale",
          "Lime",
          "Olive oil",
          "Parmigiano",
          "Pecorino",
          "Potatoes",
          "Rosemary",
          "Simple syrup",
          "Soda water",
          "Spaghetti",
          "Sugar",
          "White rum");

  @Test
  public void loadsEveryAllowlistedIngredient() {
    assertEquals(EXPECTED_INGREDIENTS, IngredientsLoader.loadIngredients());
  }
}
