package net.tjh90.website.core.recipes;

import java.util.List;
import org.commonmark.node.Node;
import org.commonmark.renderer.html.HtmlRenderer;

public record Recipe(String name, Type type, List<Ingredient> ingredients, Node content) {

  private static final HtmlRenderer HTML_RENDERER = HtmlRenderer.builder().build();

  /// Renders the recipe [content] to HTML.
  ///
  /// The YAML front matter is omitted from the rendered output.
  ///
  /// @return the recipe content rendered as HTML.
  public String toHtml() {
    return HTML_RENDERER.render(content);
  }

  public enum Type {
    MEAL,
    SIDE,
    DRINK
  }
}
