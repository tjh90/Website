package net.tjh90.website.ui.views.anascramble;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/// Unit tests for the [AnascrambleModel].
class AnascrambleModelTests {

    @Test
    protected void lettersDefaultToEmpty() {
        AnascrambleModel model = new AnascrambleModel();

        assertTrue(model.getLetters().isEmpty());
    }

    @Test
    protected void settingLettersClearsKnownLetters() {
        AnascrambleModel model = new AnascrambleModel();
        model.initKnownLetters(4);
        assertEquals(4, model.getKnownLetters().size());

        model.setLetters("abc");

        assertEquals(0, model.getKnownLetters().size());
    }

    @Test
    protected void initKnownLettersCreatesNullFilledList() {
        AnascrambleModel model = new AnascrambleModel();
        model.initKnownLetters(3);

        assertEquals(3, model.getKnownLetters().size());
        assertTrue(model.getKnownLetters().stream().allMatch(letter -> letter == null));
    }

    @Test
    protected void setKnownLetterUpdatesWithinBounds() {
        AnascrambleModel model = new AnascrambleModel();
        int knownLettersSize = 3;
        model.initKnownLetters(knownLettersSize);

        model.setKnownLetter(1, 'A');
        assertEquals('A', model.getKnownLetters().get(1));

        model.setKnownLetter(knownLettersSize, 'B');
        assertNull(model.getKnownLetters().get(knownLettersSize - 1));
    }

    @Test
    protected void clearKnownLettersEmptiesList() {
        AnascrambleModel model = new AnascrambleModel();
        model.initKnownLetters(2);

        model.clearKnownLetters();

        assertEquals(0, model.getKnownLetters().size());
    }
}
