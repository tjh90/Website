package net.tjh90.website.core.recipes;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class IngredientMatchingTest {

  private final Ingredient whiteRum = new SimpleIngredient("White rum", false, null);
  private final Ingredient lime = new SimpleIngredient("Lime", false, null);
  private final Ingredient sugar =
      new IngredientChoice(List.of("Sugar", "Simple syrup"), false, null);

  @Test
  void simpleIngredientMatchesFullNameIgnoringCase() {
    assertTrue(whiteRum.matches("White rum"));
    assertTrue(whiteRum.matches("white rum"));
    assertTrue(whiteRum.matches("WHITE RUM"));
    assertTrue(lime.matches("Lime"));
    assertTrue(lime.matches("lime"));
  }

  @Test
  void simpleIngredientMatchesSingleWholeWordIgnoringCase() {
    assertTrue(whiteRum.matches("rum"));
    assertTrue(whiteRum.matches("Rum"));
    assertTrue(whiteRum.matches("white"));
    assertTrue(whiteRum.matches("WHITE"));
  }

  @Test
  void simpleIngredientRejectsPartialWords() {
    assertFalse(whiteRum.matches("ru"));
    assertFalse(whiteRum.matches("crumb"));
    assertFalse(whiteRum.matches("rum punch"));
  }

  @Test
  void simpleIngredientRejectsNull() {
    assertFalse(whiteRum.matches(null));
    assertFalse(lime.matches(null));
  }

  @Test
  void choiceIngredientMatchesAnyAlternativeFullName() {
    assertTrue(sugar.matches("Sugar"));
    assertTrue(sugar.matches("Simple syrup"));
    assertTrue(sugar.matches("sugar"));
    assertTrue(sugar.matches("simple syrup"));
  }

  @Test
  void choiceIngredientMatchesWholeWordOfAnyAlternative() {
    assertTrue(sugar.matches("syrup"));
    assertTrue(sugar.matches("Syrup"));
    assertTrue(sugar.matches("Simple"));
  }

  @Test
  void choiceIngredientRejectsPartialWords() {
    assertFalse(sugar.matches("imple"));
    assertFalse(sugar.matches("syru"));
    assertFalse(sugar.matches("simple syrup extra"));
  }
}
