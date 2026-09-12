package net.tjh90.website.core.recipes;

public class RecipeLoadException extends RuntimeException {

  public RecipeLoadException(String message) {
    super(message);
  }

  public RecipeLoadException(String message, Throwable cause) {
    super(message, cause);
  }
}
