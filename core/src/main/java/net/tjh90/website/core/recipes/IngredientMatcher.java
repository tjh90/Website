package net.tjh90.website.core.recipes;

import java.util.Arrays;

/// Matches ingredient names for filtering and validation.
class IngredientMatcher {

  private IngredientMatcher() {
    // Private constructor to prevent instantiation.
  }

  /// Returns true if `query` matches `name` ignoring case, either as the full `name` or as a
  /// single whole word of it.
  static boolean matches(String name, String query) {
    if (name == null || query == null) {
      return false;
    }

    String trimmed = query.trim();
    if (name.equalsIgnoreCase(trimmed)) {
      return true;
    }

    return Arrays.stream(name.split("\\s+")).anyMatch(word -> word.equalsIgnoreCase(trimmed));
  }
}
