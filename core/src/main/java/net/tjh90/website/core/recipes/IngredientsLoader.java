package net.tjh90.website.core.recipes;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.stream.Collectors;

public class IngredientsLoader {

  private static final String INGREDIENTS_FILE = "/recipes/ingredients.txt";

  private IngredientsLoader() {
    // Private constructor to prevent instantiation.
  }

  public static Set<String> loadIngredients() {
    try (InputStream is = IngredientsLoader.class.getResourceAsStream(INGREDIENTS_FILE)) {
      if (is == null) {
        throw new RecipeException("Ingredients allowlist not found: " + INGREDIENTS_FILE);
      }

      try (BufferedReader br =
          new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
        return br.lines()
            .map(String::trim)
            .filter(line -> !line.isEmpty())
            .collect(Collectors.toSet());
      }
    } catch (IOException e) {
      throw new RecipeException("Failed to read ingredients allowlist: " + INGREDIENTS_FILE, e);
    }
  }
}
