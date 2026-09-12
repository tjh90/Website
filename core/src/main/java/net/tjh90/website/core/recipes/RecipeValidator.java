package net.tjh90.website.core.recipes;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class RecipeValidator {

  private final Set<String> allowedIngredients;

  public RecipeValidator(Set<String> allowedIngredients) {
    this.allowedIngredients = allowedIngredients;
  }

  public void validate(List<Recipe> recipes) {
    List<String> violations = new ArrayList<>();

    for (Recipe recipe : recipes) {
      for (Ingredient ingredient : recipe.ingredients()) {
        boolean isAllowed = allowedIngredients.stream().anyMatch(ingredient::matches);
        if (!isAllowed) {
          String msg =
              String.format(
                  "Recipe %s: ingredient %s is not in the ingredients allowlist",
                  recipe.name(), ingredient.getName());
          violations.add(msg);
        }
      }
    }

    if (!violations.isEmpty()) {
      throw new RecipeException(String.join("\n", violations));
    }
  }
}
