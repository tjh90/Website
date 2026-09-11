package net.tjh90.website.core.recipes;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.commonmark.ext.front.matter.YamlFrontMatterBlock;
import org.commonmark.ext.front.matter.YamlFrontMatterExtension;
import org.commonmark.ext.front.matter.YamlFrontMatterNode;
import org.commonmark.node.AbstractVisitor;
import org.commonmark.node.BulletList;
import org.commonmark.node.Heading;
import org.commonmark.node.ListItem;
import org.commonmark.node.Node;
import org.commonmark.node.Text;
import org.commonmark.parser.Parser;

public class RecipeParser {

  private static final String TYPE_KEY = "type";
  private static final String INGREDIENTS_HEADING = "Ingredients";
  private static final String OPTIONAL_PREFIX = "[OPTIONAL]";

  private static final Parser PARSER =
      Parser.builder().extensions(List.of(YamlFrontMatterExtension.create())).build();

  private RecipeParser() {
    // Private constructor to prevent instantiation.
  }

  public static Optional<Recipe> parse(String markdown) {
    Node document = PARSER.parse(markdown);

    String name = parseName(document);
    Recipe.Type type = parseType(document);
    List<Ingredient> ingredients = parseIngredients(document);

    if (name == null || type == null || ingredients == null) {
      return Optional.empty();
    }

    return Optional.of(new Recipe(name, type, ingredients, document));
  }

  private static String parseName(Node document) {
    for (Node child = document.getFirstChild(); child != null; child = child.getNext()) {
      if (child instanceof Heading heading && heading.getLevel() == 1) {
        return textOf(heading);
      }
    }

    return null;
  }

  private static Recipe.Type parseType(Node document) {
    for (Node child = document.getFirstChild(); child != null; child = child.getNext()) {
      if (child instanceof YamlFrontMatterBlock) {
        for (Node node = child.getFirstChild(); node != null; node = node.getNext()) {
          if (node instanceof YamlFrontMatterNode frontMatter
              && TYPE_KEY.equals(frontMatter.getKey())
              && !frontMatter.getValues().isEmpty()) {
            return Recipe.Type.valueOf(frontMatter.getValues().get(0).toUpperCase());
          }
        }
      }
    }

    return null;
  }

  private static List<Ingredient> parseIngredients(Node document) {
    for (Node child = document.getFirstChild(); child != null; child = child.getNext()) {
      if (child instanceof Heading heading
          && heading.getLevel() == 2
          && INGREDIENTS_HEADING.equals(textOf(heading))) {
        return collectIngredientsFromList(child.getNext());
      }
    }

    return null;
  }

  private static List<Ingredient> collectIngredientsFromList(Node node) {
    List<Ingredient> ingredients = new ArrayList<>();
    while (node != null) {
      if (node instanceof BulletList list) {
        for (Node item = list.getFirstChild(); item != null; item = item.getNext()) {
          if (item instanceof ListItem listItem) {
            ingredients.add(parseIngredient(textOf(listItem)));
          }
        }
      }
      node = node.getNext();
    }

    return ingredients;
  }

  private static Ingredient parseIngredient(String raw) {
    String text = raw.trim();
    boolean optional = false;

    if (text.regionMatches(true, 0, OPTIONAL_PREFIX, 0, OPTIONAL_PREFIX.length())) {
      optional = true;
      text = text.substring(OPTIONAL_PREFIX.length()).trim();
    }

    String amount = null;
    if (text.endsWith(")")) {
      int open = text.lastIndexOf('(');
      if (open > 0) {
        amount = text.substring(open + 1, text.length() - 1).trim();
        text = text.substring(0, open).trim();
      }
    }

    if (text.contains("/")) {
      List<String> names = Arrays.stream(text.split("/")).map(String::trim).toList();
      return new IngredientChoice(names, optional, amount);
    }

    return new SimpleIngredient(text, optional, amount);
  }

  private static String textOf(Node node) {
    StringBuilder builder = new StringBuilder();
    node.accept(
        new AbstractVisitor() {
          @Override
          public void visit(Text text) {
            builder.append(text.getLiteral());
          }
        });
    return builder.toString();
  }
}
