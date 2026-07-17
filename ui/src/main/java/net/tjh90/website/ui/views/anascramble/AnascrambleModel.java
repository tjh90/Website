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
}
