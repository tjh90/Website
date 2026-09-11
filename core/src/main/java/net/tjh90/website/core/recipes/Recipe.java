package net.tjh90.website.core.recipes;

import java.util.List;

public record Recipe(String name, Type type, List<Ingredient> ingredients, String content) {

  public enum Type {
    MEAL,
    SIDE,
    DRINK
  }
}
