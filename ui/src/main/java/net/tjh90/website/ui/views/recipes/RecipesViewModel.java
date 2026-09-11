package net.tjh90.website.ui.views.recipes;

import com.vaadin.flow.component.AbstractField;
import com.vaadin.flow.component.listbox.ListBox;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import net.tjh90.website.core.recipes.IngredientsLoader;
import net.tjh90.website.core.recipes.Recipe;
import net.tjh90.website.core.recipes.RecipeValidator;
import net.tjh90.website.core.recipes.RecipesLoader;

/// Defines UI logic for the [RecipesView].
public class RecipesViewModel {

  private final RecipesView view;
  private final List<Recipe> allRecipes;

  /// Constructor.
  ///
  /// @param view the [RecipesView] instance to bind to.
  public RecipesViewModel(final RecipesView view) {
    this.view = view;

    ListBox<Recipe> recipeList = view.getRecipeList();
    recipeList.addValueChangeListener(
        event -> {
          if (event.getValue() != null) {
            view.showRecipe(event.getValue());
          }
        });

    allRecipes = loadAndValidateRecipes();

    List<AbstractField> filterFields =
        List.of(
            view.getDrinkFilter(),
            view.getMealFilter(),
            view.getSideFilter(),
            view.getNameFilter(),
            view.getIngredientFilter());
    filterFields.forEach(field -> field.addValueChangeListener(event -> applyFilters()));

    applyFilters();
  }

  private void applyFilters() {
    Set<Recipe.Type> selectedTypes = selectedTypes();

    String nameQuery = view.getNameFilter().getValue().trim().toLowerCase(Locale.ROOT);
    String ingredientQuery = view.getIngredientFilter().getValue().trim();

    List<Recipe> filtered =
        allRecipes.stream()
            .filter(recipe -> selectedTypes.contains(recipe.type()))
            .filter(recipe -> matchesName(recipe, nameQuery))
            .filter(recipe -> matchesIngredient(recipe, ingredientQuery))
            .toList();

    view.setRecipes(filtered);
  }

  private Set<Recipe.Type> selectedTypes() {
    Set<Recipe.Type> types = new HashSet<>();
    if (view.getDrinkFilter().getValue()) {
      types.add(Recipe.Type.DRINK);
    }
    if (view.getMealFilter().getValue()) {
      types.add(Recipe.Type.MEAL);
    }
    if (view.getSideFilter().getValue()) {
      types.add(Recipe.Type.SIDE);
    }

    return types;
  }

  private static boolean matchesName(Recipe recipe, String nameQuery) {
    return nameQuery.isEmpty() || recipe.name().toLowerCase(Locale.ROOT).contains(nameQuery);
  }

  private static boolean matchesIngredient(Recipe recipe, String ingredientQuery) {
    return ingredientQuery.isEmpty()
        || recipe.ingredients().stream()
            .anyMatch(ingredient -> ingredient.matches(ingredientQuery));
  }

  private static List<Recipe> loadAndValidateRecipes() {
    List<Recipe> recipes = RecipesLoader.loadRecipes();

    if (!recipes.isEmpty()) {
      Set<String> allowedIngredients = IngredientsLoader.loadIngredients();
      new RecipeValidator(allowedIngredients).validate(recipes);
    }

    return recipes.stream().sorted(Comparator.comparing(Recipe::name)).toList();
  }
}
