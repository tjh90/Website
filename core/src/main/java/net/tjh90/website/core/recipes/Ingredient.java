package net.tjh90.website.core.recipes;

public interface Ingredient {

  String getName();

  boolean isOptional();

  String getQuantity();

  boolean matches(String name);
}
