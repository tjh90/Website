package net.tjh90.website.ui.components;

import com.vaadin.flow.component.Component;
import com.vaadin.flow.component.Tag;
import com.vaadin.flow.dom.ClassList;
import com.vaadin.flow.dom.Element;
import com.vaadin.flow.dom.Style;
import com.vaadin.flow.dom.Style.Position;

import net.tjh90.website.core.Point;

/// HTML element for a single scrambled character.
@Tag(value = "i")
public class ScrambledCharacter extends Component {

    private static final String UNITS = "px";
    private static final String DIMMED_CLASS = "dimmed";

    /// Constructor.
    ///
    /// @param ch the character to render.
    /// @param p  the location at which the character should be rendered.
    public ScrambledCharacter(char ch, Point p) {
        Element element = getElement();
        if (element != null) {
            element.setText(Character.toString(ch).toUpperCase());

            Style style = element.getStyle();
            if (style != null) {
                style.setPosition(Position.ABSOLUTE);
                style.set("left", toPosition(p.x()));
                style.set("top", toPosition(p.y()));
            }
        }
    }

    /// Toggle the dimmed appearance of this character.
    ///
    /// @param dimmed true to dim, false to undim.
    public void setDimmed(boolean dimmed) {
        Element element = getElement();
        ClassList classList = element != null ? element.getClassList() : null;
        if (classList == null) {
            return;
        }

        if (dimmed) {
            classList.add(DIMMED_CLASS);
        } else {
            classList.remove(DIMMED_CLASS);
        }
    }

    private static String toPosition(final double dimension) {
        return Double.toString(dimension) + UNITS;
    }
}
