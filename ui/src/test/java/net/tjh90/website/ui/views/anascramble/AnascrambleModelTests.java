package net.tjh90.website.ui.views.anascramble;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

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

    @Test
    protected void isLetterAvailableForLetterPresentInLetters() {
        AnascrambleModel model = new AnascrambleModel();
        model.setLetters("Echoes");

        assertTrue(model.isLetterAvailable('E'));
        assertTrue(model.isLetterAvailable('e'));
    }

    @Test
    protected void isLetterAvailableForLetterNotInLetters() {
        AnascrambleModel model = new AnascrambleModel();
        model.setLetters("Echoes");

        assertFalse(model.isLetterAvailable('Z'));
    }

    @Test
    protected void isLetterAvailableIsCaseInsensitive() {
        AnascrambleModel model = new AnascrambleModel();
        model.setLetters("Echoes");

        assertTrue(model.isLetterAvailable('c'));
        assertTrue(model.isLetterAvailable('C'));
    }

    @Test
    protected void assigningKnownLetterConsumesOneOccurrence() {
        AnascrambleModel model = new AnascrambleModel();
        model.setLetters("Echoes");
        model.initKnownLetters(6);
        model.setKnownLetter(0, 'E');

        assertTrue(model.isLetterAvailable('E'));
        assertEquals(List.of(true, false, false, false, false, false), model.computeClaimedMap());

        model.setKnownLetter(1, 'E');

        assertFalse(model.isLetterAvailable('E'));
    }

    @Test
    protected void computeClaimedMapMarksCorrectPositionsWithDuplicates() {
        AnascrambleModel model = new AnascrambleModel();
        model.setLetters("Echoes");
        model.initKnownLetters(6);
        model.setKnownLetter(0, 'E');
        model.setKnownLetter(2, 'H');

        assertEquals(List.of(true, false, true, false, false, false), model.computeClaimedMap());
    }

    @Test
    protected void computeClaimedMapIgnoresNullKnownLetters() {
        AnascrambleModel model = new AnascrambleModel();
        model.setLetters("Echoes");
        model.initKnownLetters(6);

        assertTrue(model.computeClaimedMap().stream().noneMatch(claimed -> claimed));
    }

    @Test
    protected void computeClaimedMapMatchesCaseInsensitively() {
        AnascrambleModel model = new AnascrambleModel();
        model.setLetters("Echoes");
        model.initKnownLetters(6);
        model.setKnownLetter(0, 'e');

        assertEquals(List.of(true, false, false, false, false, false), model.computeClaimedMap());
    }
}
