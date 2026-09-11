package net.tjh90.website.core.recipes;

import java.util.List;

public class IngredientChoice implements Ingredient {

  private final List<String> names;
  private final boolean isOptional;
  private final String quantity;

  public IngredientChoice(List<String> names, boolean isOptional, String quantity) {
    this.names = names.stream().distinct().toList();
    this.isOptional = isOptional;
    this.quantity = quantity;
  }

  @Override
  public String getName() {
    return String.join("/", names);
  }

  @Override
  public boolean isOptional() {
    return isOptional;
  }

  @Override
  public String getQuantity() {
    return quantity;
  }

  @Override
  public boolean matches(String name) {
    if (name == null || names == null) {
      return false;
    }

    return names.contains(name);
  }
}
