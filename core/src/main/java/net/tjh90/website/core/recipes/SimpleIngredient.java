package net.tjh90.website.core.recipes;

public class SimpleIngredient implements Ingredient {

  private final String name;
  private final boolean isOptional;
  private final String quantity;

  public SimpleIngredient(String name, boolean isOptional, String quantity) {
    this.name = name;
    this.isOptional = isOptional;
    this.quantity = quantity;
  }

  @Override
  public String getName() {
    return name;
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
    if (name == null) {
      return false;
    }

    return name.equals(this.name);
  }
}
