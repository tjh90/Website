package net.tjh90.website.ui.components;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

import net.tjh90.website.core.Point;

/// Unit tests for the [ScrambledCharacter] component.
class ScrambledCharacterTests {

    @Test
    protected void constructorUppercasesLetter() {
        ScrambledCharacter character = new ScrambledCharacter('a', new Point(10.0, 20.0));

        assertEquals("A", character.getElement().getText());
    }

    @Test
    protected void constructorSetsAbsolutePosition() {
        ScrambledCharacter character = new ScrambledCharacter('A', new Point(10.0, 20.0));

        assertEquals("absolute", character.getElement().getStyle().get("position"));
        assertEquals("10.0px", character.getElement().getStyle().get("left"));
        assertEquals("20.0px", character.getElement().getStyle().get("top"));
    }

    @Test
    protected void setDimmedAddsDimmedClass() {
        ScrambledCharacter character = new ScrambledCharacter('A', new Point(0.0, 0.0));

        character.setDimmed(true);

        assertTrue(character.getElement().getClassList().contains("dimmed"));
    }

    @Test
    protected void setDimmedFalseRemovesDimmedClass() {
        ScrambledCharacter character = new ScrambledCharacter('A', new Point(0.0, 0.0));
        character.setDimmed(true);

        assertTrue(character.getElement().getClassList().contains("dimmed"));

        character.setDimmed(false);

        assertFalse(character.getElement().getClassList().contains("dimmed"));
    }
}
