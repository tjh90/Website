package net.tjh90.website.ui.views.recipes;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.options.LoadState;
import net.tjh90.website.ui.PlaywrightTests;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

/// End-to-end tests for the Recipes page.
class RecipesViewTests extends PlaywrightTests {

  private static final String RECIPE_LIST_SELECTOR = "vaadin-list-box.recipeList";
  private static final String RECIPE_ITEM_SELECTOR = RECIPE_LIST_SELECTOR + " vaadin-item";
  private static final String RECIPE_CONTENT_SELECTOR = "div.recipeContainer";
  private static final String RECIPE_CONTENT_H1_SELECTOR = RECIPE_CONTENT_SELECTOR + " h1";
  private static final String TYPE_CHECKBOX_SELECTOR = "vaadin-checkbox";
  private static final String NAME_FILTER_INPUT_SELECTOR =
      "vaadin-text-field.recipeFilterField input[placeholder='Search by name']";
  private static final String INGREDIENT_FILTER_INPUT_SELECTOR =
      "vaadin-text-field.recipeFilterField input[placeholder='Search by ingredient']";

  private static final String FRENCH_75_NAME = "French 75";
  private static final String WHISKY_NAME = "Whisky";

  private Page page = null;

  @BeforeEach
  void setup() {
    page = browser.newPage();
    page.navigate(baseUrl() + "/recipes");
    page.waitForLoadState(LoadState.DOMCONTENTLOADED);
    page.locator(RECIPE_ITEM_SELECTOR)
        .first()
        .waitFor(new Locator.WaitForOptions().setTimeout(120_000));
  }

  @Test
  protected void listsAllBundledRecipes() {
    assertTrue(page.getByText(FRENCH_75_NAME).first().isVisible());
    assertTrue(page.getByText(WHISKY_NAME).first().isVisible());
  }

  @Test
  protected void autoSelectsTheFirstRecipe() {
    assertEquals(FRENCH_75_NAME, page.locator(RECIPE_CONTENT_H1_SELECTOR).innerText());
  }

  @Test
  protected void clickingRecipeSwapsTheDisplayedContent() {
    getRecipeItem(WHISKY_NAME).click();

    String func =
        String.format(
            "() => document.querySelector('%s').innerText === '%s'",
            RECIPE_CONTENT_H1_SELECTOR, WHISKY_NAME);
    page.waitForFunction(func);

    assertEquals(WHISKY_NAME, page.locator(RECIPE_CONTENT_H1_SELECTOR).innerText());
  }

  @Test
  protected void nameFilterLimitsTheRecipeList() {
    page.locator(NAME_FILTER_INPUT_SELECTOR).fill("french");

    waitForRecipeCount(1);
    assertTrue(getRecipeItem(FRENCH_75_NAME).isVisible());
    assertEquals(0, getRecipeItem(WHISKY_NAME).count());
    assertEquals(FRENCH_75_NAME, page.locator(RECIPE_CONTENT_H1_SELECTOR).innerText());
  }

  @Test
  protected void ingredientFilterLimitsTheRecipeList() {
    page.locator(INGREDIENT_FILTER_INPUT_SELECTOR).fill("lime");

    waitForRecipeCount(1);
    assertTrue(getRecipeItem(FRENCH_75_NAME).isVisible());
    assertEquals(0, getRecipeItem(WHISKY_NAME).count());
  }

  @Test
  protected void ingredientFilterMatchesMultiWordIngredients() {
    page.locator(INGREDIENT_FILTER_INPUT_SELECTOR).fill("ice cubes");

    waitForRecipeCount(1);
    assertTrue(getRecipeItem(FRENCH_75_NAME).isVisible());
    assertEquals(0, getRecipeItem(WHISKY_NAME).count());
  }

  @Test
  protected void ingredientFilterMatchesWholeWordsOnly() {
    page.locator(INGREDIENT_FILTER_INPUT_SELECTOR).fill("hampagne");

    waitForRecipeCount(0);
    assertFalse(page.locator(RECIPE_CONTENT_SELECTOR).innerText().isEmpty());
    assertEquals(RecipesView.NO_RECIPES_TEXT, page.locator(RECIPE_CONTENT_SELECTOR).innerText());
  }

  @Test
  protected void uncheckingATypeFiltersOutThatType() {
    getTypeCheckbox("Drink").click();

    waitForRecipeCount(0);
    assertEquals(RecipesView.NO_RECIPES_TEXT, page.locator(RECIPE_CONTENT_SELECTOR).innerText());
  }

  @Test
  protected void filtersCombineWithAnd() {
    page.locator(NAME_FILTER_INPUT_SELECTOR).fill("french");
    page.locator(INGREDIENT_FILTER_INPUT_SELECTOR).fill("whisky");

    waitForRecipeCount(0);
    assertEquals(RecipesView.NO_RECIPES_TEXT, page.locator(RECIPE_CONTENT_SELECTOR).innerText());
  }

  private void waitForRecipeCount(int count) {
    page.waitForFunction(
        "() => document.querySelectorAll('%s').length === %d"
            .formatted(RECIPE_ITEM_SELECTOR, count));
  }

  private Locator getRecipeItem(String recipeName) {
    return page.locator(RECIPE_ITEM_SELECTOR)
        .filter(new Locator.FilterOptions().setHasText(recipeName));
  }

  private Locator getTypeCheckbox(String label) {
    return page.locator(TYPE_CHECKBOX_SELECTOR)
        .filter(new Locator.FilterOptions().setHasText(label));
  }
}
