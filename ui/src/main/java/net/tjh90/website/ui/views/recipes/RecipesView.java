package net.tjh90.website.ui.views.recipes;

import com.vaadin.flow.component.Component;
import com.vaadin.flow.component.checkbox.Checkbox;
import com.vaadin.flow.component.html.Div;
import com.vaadin.flow.component.html.H3;
import com.vaadin.flow.component.html.H5;
import com.vaadin.flow.component.listbox.ListBox;
import com.vaadin.flow.component.orderedlayout.FlexComponent;
import com.vaadin.flow.component.orderedlayout.HorizontalLayout;
import com.vaadin.flow.component.orderedlayout.VerticalLayout;
import com.vaadin.flow.component.textfield.TextField;
import com.vaadin.flow.data.value.ValueChangeMode;
import com.vaadin.flow.router.Route;
import java.util.List;
import net.tjh90.website.core.recipes.Recipe;
import net.tjh90.website.ui.HasTitle;
import net.tjh90.website.ui.views.CssClassNames;

/// Defines the view for exploring and displaying recipes. UI logic is handled in
/// [RecipesViewModel].
@Route(RecipesView.ROUTE)
public class RecipesView extends VerticalLayout implements HasTitle {

  public static final String ROUTE = "recipes";

  public static final String TITLE = "Recipes";
  public static final String NAV_LABEL = TITLE;

  static final String NO_RECIPES_TEXT = "No recipes found.";

  private static final String TYPE_FILTER_LABEL = "Types";
  private static final String NAME_FILTER_LABEL = "Search by name";
  private static final String INGREDIENT_FILTER_LABEL = "Search by ingredient";

  private static final String RECIPE_LIST_WIDTH = "16em";

  private final ListBox<Recipe> recipeList = new ListBox<>();
  private final Div recipeContainer = new Div();

  private final Checkbox drinkFilter = new Checkbox("Drink", true);
  private final Checkbox mealFilter = new Checkbox("Meal", true);
  private final Checkbox sideFilter = new Checkbox("Side", true);
  private final TextField nameFilter = new TextField();
  private final TextField ingredientFilter = new TextField();

  @SuppressWarnings("unused")
  private final RecipesViewModel viewModel;

  public RecipesView() {
    setSizeFull();

    add(createContent());

    viewModel = new RecipesViewModel(this);
  }

  private Component createContent() {
    VerticalLayout filterPanel = createFilterPanel();

    H3 recipeListLabel = new H3(TITLE);

    VerticalLayout recipeListPanel = new VerticalLayout(filterPanel, recipeListLabel, recipeList);
    recipeListPanel.setClassName(CssClassNames.RECIPE_LIST_PANEL);
    recipeListPanel.setPadding(false);
    recipeListPanel.setSpacing(false);
    recipeListPanel.setWidth(RECIPE_LIST_WIDTH);
    recipeListPanel.setHeightFull();

    recipeList.setClassName(CssClassNames.RECIPE_LIST);
    recipeList.setWidthFull();
    recipeList.setItemLabelGenerator(RecipesView::recipeLabel);

    recipeContainer.setWidthFull();
    recipeContainer.setHeightFull();

    HorizontalLayout layout = new HorizontalLayout();
    layout.setWidthFull();
    layout.setHeightFull();
    layout.setClassName(CssClassNames.RECIPE_LAYOUT);
    layout.add(recipeListPanel, recipeContainer);
    layout.setFlexShrink(0, recipeListPanel);
    layout.expand(recipeContainer);

    return layout;
  }

  private VerticalLayout createFilterPanel() {
    HorizontalLayout typeFilters = new HorizontalLayout(drinkFilter, mealFilter, sideFilter);
    typeFilters.setClassName(CssClassNames.RECIPE_TYPE_FILTERS);
    typeFilters.setSpacing(true);
    typeFilters.setPadding(false);

    nameFilter.setClassName(CssClassNames.RECIPE_FILTER_FIELD);
    nameFilter.setWidthFull();
    nameFilter.setValueChangeMode(ValueChangeMode.EAGER);

    ingredientFilter.setClassName(CssClassNames.RECIPE_FILTER_FIELD);
    ingredientFilter.setWidthFull();
    ingredientFilter.setValueChangeMode(ValueChangeMode.EAGER);

    Div typeFilterGroup = createFilterGroup(TYPE_FILTER_LABEL, typeFilters);
    Div nameFilterGroup = createFilterGroup(NAME_FILTER_LABEL, nameFilter);
    Div ingredientFilterGroup = createFilterGroup(INGREDIENT_FILTER_LABEL, ingredientFilter);

    VerticalLayout filterPanel =
        new VerticalLayout(typeFilterGroup, nameFilterGroup, ingredientFilterGroup);
    filterPanel.setClassName(CssClassNames.RECIPE_FILTERS);
    filterPanel.setPadding(true);
    filterPanel.setSpacing(true);
    filterPanel.setAlignItems(FlexComponent.Alignment.START);

    return filterPanel;
  }

  private static Div createFilterGroup(String labelText, Component field) {
    H5 label = new H5(labelText);
    Div group = new Div(label, field);
    group.setClassName(CssClassNames.RECIPE_FILTER_GROUP);

    return group;
  }

  /// Populates the recipe list and shows the details of the first recipe.
  ///
  /// @param recipes the recipes to display.
  void setRecipes(List<Recipe> recipes) {
    recipeList.setItems(recipes);
    if (recipes.isEmpty()) {
      setRecipeContent(NO_RECIPES_TEXT);
    } else if (recipeList.getValue() == null) {
      recipeList.setValue(recipes.get(0));
    }
  }

  /// Displays the given recipe in the detail panel.
  ///
  /// @param recipe the recipe to display.
  void showRecipe(Recipe recipe) {
    setRecipeContent(recipe.toHtml());
  }

  private void setRecipeContent(String html) {
    recipeContainer.getElement().setProperty("innerHTML", html);
  }

  private static String recipeLabel(Recipe recipe) {
    return recipe.name();
  }

  ListBox<Recipe> getRecipeList() {
    return recipeList;
  }

  Div getRecipeContainer() {
    return recipeContainer;
  }

  Checkbox getDrinkFilter() {
    return drinkFilter;
  }

  Checkbox getMealFilter() {
    return mealFilter;
  }

  Checkbox getSideFilter() {
    return sideFilter;
  }

  TextField getNameFilter() {
    return nameFilter;
  }

  TextField getIngredientFilter() {
    return ingredientFilter;
  }

  @Override
  public String getTitle() {
    return TITLE;
  }
}
