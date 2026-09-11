package net.tjh90.website.core.recipes;

public interface Ingredient {

  String getName();

  boolean isOptional();

  String getQuantity();

  /// Returns true if `name` is the full name of this ingredient or a single whole word of it,
  /// ignoring case.
  boolean matches(String name);
}
