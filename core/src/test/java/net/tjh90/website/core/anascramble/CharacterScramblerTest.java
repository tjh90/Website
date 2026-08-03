package net.tjh90.website.core.anascramble;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;

import net.tjh90.website.core.Point;
import net.tjh90.website.core.anascramble.CharacterData;
import net.tjh90.website.core.anascramble.CharacterScrambler;

public class CharacterScramblerTest {

    private static final String TEST_LETTERS = "TestLetters";

    private static final double BUFFER_ZONE = 50.0;
    private static final double BUFFER_ZONE_SQUARED = BUFFER_ZONE * BUFFER_ZONE;

    /// Test that the letters returned from the scrambler are the same letters as those that appear in the test string.
    @Test
    public void letterScramblerTest() {
        CharacterScrambler characterScrambler = new CharacterScrambler();
        List<CharacterData> scrambledLetters = characterScrambler.scramble(TEST_LETTERS);

        assertEquals(TEST_LETTERS.length(), scrambledLetters.size());

        // Check that all letters in the original test string are present in the scrambled letter list.
        List<Character> testLetters = new ArrayList<>(TEST_LETTERS.chars().mapToObj(c -> (char) c).toList());
        for (CharacterData letter : scrambledLetters) {
            char ch = letter.letter();

            int chInd = testLetters.indexOf(ch);
            assertTrue(chInd >= 0);

            testLetters.remove(chInd);
        }
    }

    /// Test that the positions of the letters returned from the scrambler are adequately spaced.
    @Test
    public void letterPositionTest() {
        CharacterScrambler letterScrambler = new CharacterScrambler();
        List<CharacterData> scrambledLetters = letterScrambler.scramble(TEST_LETTERS);

        List<Point> points = scrambledLetters.stream().map(l -> l.point()).toList();
        int pointsCount = points.size();
        for (int i = 0; i < pointsCount; i++) {
            Point p0 = points.get(i);
            for (int j = i + 1; j < pointsCount; j++) {
                Point p1 = points.get(j);
                assertTrue(Point.distanceSquared(p0, p1) >= BUFFER_ZONE_SQUARED);
            }
        }
    }

    /// Test that a scrambler with the same seed produces the same scrambled result.
    @Test
    public void scrambledResultIsDeterministicForSeed() {
        CharacterScrambler first = new CharacterScrambler(42L);
        CharacterScrambler second = new CharacterScrambler(42L);

        List<CharacterData> firstResult = first.scramble(TEST_LETTERS);
        List<CharacterData> secondResult = second.scramble(TEST_LETTERS);

        assertEquals(firstResult, secondResult);
    }

    /// Test that scrambling an empty string produces an empty list.
    @Test
    public void scrambleEmptyStringReturnsEmptyList() {
        CharacterScrambler scrambler = new CharacterScrambler();

        assertTrue(scrambler.scramble("").isEmpty());
    }

    /// Test that a single character is scrambled to a single location.
    @Test
    public void scrambleSingleCharacterReturnsSingleLetter() {
        CharacterScrambler scrambler = new CharacterScrambler();
        List<CharacterData> result = scrambler.scramble("A");

        assertEquals(1, result.size());
        assertEquals('A', result.get(0).letter());
    }

    /// Test that points closer than the buffer zone are reported as overlapping.
    @Test
    public void overlapsReturnsTrueForClosePoints() {
        CharacterScrambler scrambler = new CharacterScrambler();

        List<Point> others = List.of(new Point(0.0, 0.0));
        assertTrue(scrambler.overlaps(new Point(BUFFER_ZONE / 2, 0.0), others));
    }

    /// Test that points further apart than the buffer zone are not reported as overlapping.
    @Test
    public void overlapsReturnsFalseForDistantPoints() {
        CharacterScrambler scrambler = new CharacterScrambler();

        List<Point> others = List.of(new Point(0.0, 0.0));
        assertFalse(scrambler.overlaps(new Point(BUFFER_ZONE * 2, 0.0), others));
    }

    /// Test that a point never overlaps an empty set of points.
    @Test
    public void overlapsReturnsFalseForEmptyList() {
        CharacterScrambler scrambler = new CharacterScrambler();

        assertFalse(scrambler.overlaps(new Point(0.0, 0.0), List.of()));
    }
}
