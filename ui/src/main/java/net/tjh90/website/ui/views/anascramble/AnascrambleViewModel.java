package net.tjh90.website.ui.views.anascramble;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import com.vaadin.flow.component.AbstractField.ComponentValueChangeEvent;
import com.vaadin.flow.component.Component;
import com.vaadin.flow.component.Key;
import com.vaadin.flow.component.button.Button;
import com.vaadin.flow.component.textfield.TextField;
import com.vaadin.flow.data.value.ValueChangeMode;

import net.tjh90.website.core.Point;
import net.tjh90.website.core.anascramble.CharacterData;
import net.tjh90.website.core.anascramble.CharacterScrambler;
import net.tjh90.website.ui.components.ScrambledCharacter;
import net.tjh90.website.ui.views.CssClassNames;

/// Defines UI logic for the [AnascrambleView]. Uses [AnascrambleModel] as the data model.
public class AnascrambleViewModel {

    private static final String ALPHANUMERIC_PATTERN = "[a-zA-Z0-9]";
    private static final String POSITION_PATTERN = "[a-zA-Z]";

    private static final int MIN_LETTERS_LENGTH = 3;

    private final AnascrambleView view;
    private final AnascrambleModel model;

    private List<TextField> positionFields = List.of();
    private List<ScrambledCharacter> scrambledComponents = List.of();
    private boolean isUpdatingPositionField = false;

    /// Constructor.
    ///
    /// @param view  the [AnascrambleView] instance to bind to.
    /// @param model the data model instance.
    public AnascrambleViewModel(final AnascrambleView view, final AnascrambleModel model) {
        this.view = view;
        this.model = model;

        TextField scrambleFld = view != null ? view.getLettersFld() : null;
        if (scrambleFld != null) {
            scrambleFld.setMinLength(MIN_LETTERS_LENGTH);
            scrambleFld.setMaxLength(30);
            scrambleFld.setAllowedCharPattern(ALPHANUMERIC_PATTERN);

            scrambleFld.setValueChangeMode(ValueChangeMode.EAGER);
            scrambleFld.addValueChangeListener(this::onValueChangedLettersFld);
        }

        Button scrambleBtn = view != null ? view.getScrambleBtn() : null;
        if (scrambleBtn != null) {
            scrambleBtn.addClickListener(_ -> onClickScrambleBtn());
        }

        onValueChangedLettersFld(null);
    }

    private void onValueChangedLettersFld(final ComponentValueChangeEvent<TextField, String> event) {
        String letters = event != null ? event.getValue() : "";

        boolean isScrambleBtnEnabled = letters != null && letters.length() >= MIN_LETTERS_LENGTH;
        Button scrambleBtn = view != null ? view.getScrambleBtn() : null;
        if (scrambleBtn != null) {
            scrambleBtn.setEnabled(isScrambleBtnEnabled);
        }

        if (model != null) {
            model.setLetters(letters);
        }

        // Clear scrambled display and components.
        if (view != null) {
            view.clearScrambledLetters();
            scrambledComponents = List.of();

            // Remove position fields if present.
            view.clearPositionFields();
            positionFields = List.of();
        }

        // Create new position fields if valid length.
        if (letters != null && letters.length() >= MIN_LETTERS_LENGTH) {
            createPositionFields(letters.length());
        }
    }

    private void onClickScrambleBtn() {
        CharacterScrambler letterScrambler = new CharacterScrambler(Instant.now().toEpochMilli());
        List<CharacterData> letterData = letterScrambler.scramble(model.getLetters());

        float containerOffset = 0.5f * view.getScrambleContainerSize();
        letterData = letterData.stream().map(l -> addOffset(l, containerOffset)).toList();

        scrambledComponents = letterData.stream()
                .map(l -> new ScrambledCharacter(l.letter(), l.point()))
                .toList();

        view.setScrambledLetters(new ArrayList<>(scrambledComponents));

        refreshDimming();
    }

    private void createPositionFields(int wordLength) {
        positionFields = new ArrayList<>(wordLength);

        for (int i = 0; i < wordLength; i++) {
            TextField field = new TextField();
            field.setMaxLength(1);
            field.setWidth("2.5em");
            field.setAllowedCharPattern(POSITION_PATTERN);
            field.setValueChangeMode(ValueChangeMode.EAGER);
            field.addClassName(CssClassNames.KNOWN_POSITION_FIELD);

            int pos = i;
            field.addValueChangeListener(e -> onPositionFieldChanged(pos, e.getValue()));

            field.addKeyDownListener(Key.BACKSPACE, e -> {
                if (pos > 0 && (field.getValue() == null || field.getValue().isEmpty())) {
                    focusPositionField(pos - 1);
                }
            });

            field.addKeyDownListener(Key.SPACE, e -> {
                field.clear();
                focusPositionField(pos + 1);
            });

            positionFields.add(field);
        }

        view.setPositionFields(positionFields);
        model.initKnownLetters(wordLength);
    }

    private void onPositionFieldChanged(int position, String value) {
        if (isUpdatingPositionField || model == null) {
            return;
        }
        isUpdatingPositionField = true;

        try {
            if (value != null && value.length() == 1) {
                char c = value.charAt(0);
                if (Character.isLetter(c)) {
                    char upper = Character.toUpperCase(c);
                    if (isLetterAvailable(upper)) {
                        model.setKnownLetter(position, upper);
                        refreshDimming();
                        focusPositionField(position + 1);
                    } else {
                        positionFields.get(position).clear();
                    }
                }
            } else if (value == null || value.isEmpty()) {
                model.setKnownLetter(position, '\0');
                refreshDimming();
            }
        } finally {
            isUpdatingPositionField = false;
        }
    }

    private boolean isLetterAvailable(char letter) {
        List<Boolean> claimed = computeClaimedMap();
        String letters = model != null ? model.getLetters() : "";
        for (int i = 0; i < letters.length(); i++) {
            if (!claimed.get(i) && Character.toUpperCase(letters.charAt(i)) == letter) {
                return true;
            }
        }
        return false;
    }

    private List<Boolean> computeClaimedMap() {
        String letters = model != null ? model.getLetters() : "";
        List<Boolean> claimed = new ArrayList<>(Collections.nCopies(letters.length(), false));
        List<Character> known = model != null ? model.getKnownLetters() : List.of();
        for (Character knownLetter : known) {
            if (knownLetter != null) {
                for (int i = 0; i < letters.length(); i++) {
                    if (!claimed.get(i) && Character.toUpperCase(letters.charAt(i)) == knownLetter.charValue()) {
                        claimed.set(i, true);
                        break;
                    }
                }
            }
        }
        return claimed;
    }

    private void refreshDimming() {
        for (ScrambledCharacter sc : scrambledComponents) {
            sc.setDimmed(false);
        }

        List<Boolean> claimed = computeClaimedMap();
        for (int i = 0; i < claimed.size() && i < scrambledComponents.size(); i++) {
            if (claimed.get(i)) {
                scrambledComponents.get(i).setDimmed(true);
            }
        }
    }

    private void focusPositionField(int position) {
        if (position >= 0 && position < positionFields.size()) {
            positionFields.get(position).focus();
        }
    }

    private static CharacterData addOffset(final CharacterData letterData, final float containerOffset) {
        Point point = new Point(containerOffset + letterData.point().x(), containerOffset + letterData.point().y());
        return new CharacterData(letterData.letter(), point);
    }
}
