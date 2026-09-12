package net.tjh90.website.ui.components;

import com.vaadin.flow.component.Component;
import com.vaadin.flow.component.Tag;
import com.vaadin.flow.dom.Element;

/// HTML element containing a [Font Awesome](https://fontawesome.com/) icon tag.
@Tag("i")
class Icon extends Component {

  private static final String ATTR_CLASS = "class";

  /// Constructor
  ///
  /// @param cssClassName the Font Awesome class name for the icon.
  public Icon(final String cssClassName) {
    Element element = getElement();
    if (element != null) {
      element.setAttribute(ATTR_CLASS, cssClassName);
    }
  }
}
