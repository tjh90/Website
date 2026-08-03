package net.tjh90.website.ui.views.anascramble;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/// The backing data model for the [AnascrambleView].
public class AnascrambleModel {

    private String letters = "";
    private List<Character> knownLetters = List.of();

    public String getLetters() {
        return letters;
    }

    public void setLetters(final String letters) {
        this.letters = letters;
        clearKnownLetters();
    }

    public List<Character> getKnownLetters() {
        return knownLetters;
    }

    public void setKnownLetter(int position, char letter) {
        if (position >= 0 && position < knownLetters.size()) {
            knownLetters.set(position, letter);
        }
    }

    public void clearKnownLetters() {
        this.knownLetters = List.of();
    }

    public void initKnownLetters(int wordLength) {
        this.knownLetters = new ArrayList<>(Collections.nCopies(wordLength, null));
    }

    /// @return true if the given letter (case-insensitive) has not already been assigned to a known position.
    public boolean isLetterAvailable(char letter) {
        List<Boolean> claimed = computeClaimedMap();
        char upperLetter = Character.toUpperCase(letter);
        for (int i = 0; i < letters.length(); i++) {
            if (!claimed.get(i) && Character.toUpperCase(letters.charAt(i)) == upperLetter) {
                return true;
            }
        }
        return false;
    }

    /// @return a list parallel to [letters], where each element is true if the corresponding letter has already been
    ///         assigned to a known position.
    public List<Boolean> computeClaimedMap() {
        List<Boolean> claimed = new ArrayList<>(Collections.nCopies(letters.length(), false));
        for (Character knownLetter : knownLetters) {
            if (knownLetter != null) {
                char upperLetter = Character.toUpperCase(knownLetter.charValue());
                for (int i = 0; i < letters.length(); i++) {
                    if (!claimed.get(i) && Character.toUpperCase(letters.charAt(i)) == upperLetter) {
                        claimed.set(i, true);
                        break;
                    }
                }
            }
        }
        return claimed;
    }
}
