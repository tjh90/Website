package net.tjh90.website.ui.views.anascramble;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import com.microsoft.playwright.Locator;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.options.AriaRole;
import com.microsoft.playwright.options.LoadState;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import net.tjh90.website.ui.PlaywrightTests;

/// End-to-end tests for the Anascramble page.
class AnascrambleViewTests extends PlaywrightTests {

    private static final String SCRAMBLE_CONTAINER_SELECTOR = "div.scrambleContainer";
    private static final String SCRAMBLED_CHARACTER_SELECTOR = SCRAMBLE_CONTAINER_SELECTOR + " > i";
    private static final String DIMMED_CHARACTER_SELECTOR = SCRAMBLED_CHARACTER_SELECTOR + ".dimmed";

    private static final String TEST_LETTERS = "TestLetters";

    private static final String POSITION_FIELD_SELECTOR = "vaadin-text-field.knownPositionField input";
    private static final String POSITION_FIELD_INPUTS_JS = "'vaadin-text-field.knownPositionField input'";

    private Page page = null;

    @BeforeEach
    void setup() {
        page = browser.newPage();
        page.navigate(baseUrl() + "/anascramble");
        page.waitForLoadState(LoadState.DOMCONTENTLOADED);
        page.getByLabel(AnascrambleView.SCRAMBLE_FLD_LBL).waitFor();
    }

    @Test
    protected void pageLoadsWithExpectedComponents() {
        assertTrue(page.getByLabel(AnascrambleView.SCRAMBLE_FLD_LBL).isVisible());
        assertTrue(page.locator(SCRAMBLE_CONTAINER_SELECTOR).isVisible());
        assertTrue(getScrambleButton().isVisible());
    }

    @Test
    protected void scrambleButtonDisabledUntilMinLettersEntered() {
        assertTrue(getScrambleButton().isDisabled());

        enterLetters("Te");
        assertTrue(getScrambleButton().isDisabled());

        enterLetters(TEST_LETTERS);
        page.waitForFunction("() => !document.querySelector('vaadin-button').hasAttribute('disabled')");
        assertTrue(getScrambleButton().isEnabled());
    }

    @Test
    protected void positionFieldsMatchEnteredWordLength() {
        enterLetters(TEST_LETTERS);
        page.waitForFunction("n => document.querySelectorAll(" + POSITION_FIELD_INPUTS_JS + ").length === n",
            TEST_LETTERS.length());

        Locator inputs = getPositionInputs();
        assertEquals(TEST_LETTERS.length(), inputs.count());
    }

    @Test
    protected void scramblePopulatesContainerWithExpectedLetters() {
        enterLetters(TEST_LETTERS);
        scramble();

        Locator scrambled = page.locator(SCRAMBLED_CHARACTER_SELECTOR);
        assertEquals(TEST_LETTERS.length(), scrambled.count());

        List<String> expected = TEST_LETTERS.chars()
            .mapToObj(c -> Character.toString(Character.toUpperCase((char) c)))
            .sorted()
            .toList();
        List<String> actual = scrambled.allInnerTexts().stream().map(String::trim).sorted().toList();
        assertEquals(expected, actual);
    }

    @Test
    protected void enteringKnownLetterDimsScrambledCharacter() {
        enterLetters(TEST_LETTERS);
        scramble();

        assertEquals(0, page.locator(DIMMED_CHARACTER_SELECTOR).count());

        getPositionInputs().first().fill("T");
        page.waitForFunction("() => document.querySelectorAll('" + DIMMED_CHARACTER_SELECTOR + "').length === 1");

        assertEquals(1, page.locator(DIMMED_CHARACTER_SELECTOR).count());
    }

    @Test
    protected void unavailableLetterIsClearedFromPositionField() {
        enterLetters(TEST_LETTERS);
        scramble();

        Locator firstInput = getPositionInputs().first();
        firstInput.fill("Z");
        page.waitForFunction("() => document.querySelectorAll(" + POSITION_FIELD_INPUTS_JS + ")[0].value === ''");

        assertEquals("", firstInput.inputValue());
        assertEquals(0, page.locator(DIMMED_CHARACTER_SELECTOR).count());
    }

    @Test
    protected void duplicateLettersDimDistinctCharactersUntilExhausted() {
        String word = "Echoes";
        enterLetters(word);
        scramble(word);

        Locator inputs = getPositionInputs();
        inputs.first().fill("E");
        page.waitForFunction("() => document.querySelectorAll('" + DIMMED_CHARACTER_SELECTOR + "').length === 1");
        assertEquals(1, page.locator(DIMMED_CHARACTER_SELECTOR).count());

        inputs.nth(1).fill("E");
        page.waitForFunction("() => document.querySelectorAll('" + DIMMED_CHARACTER_SELECTOR + "').length === 2");
        assertEquals(2, page.locator(DIMMED_CHARACTER_SELECTOR).count());

        inputs.nth(2).fill("E");
        page.waitForFunction("() => document.querySelectorAll(" + POSITION_FIELD_INPUTS_JS + ")[2].value === ''");
        assertEquals("", inputs.nth(2).inputValue());
        assertEquals(2, page.locator(DIMMED_CHARACTER_SELECTOR).count());
    }

    @Test
    protected void changingLettersClearsScrambledDisplay() {
        enterLetters(TEST_LETTERS);
        scramble();
        assertEquals(TEST_LETTERS.length(), page.locator(SCRAMBLED_CHARACTER_SELECTOR).count());

        enterLetters("NewWord");
        page.waitForFunction("() => document.querySelectorAll('" + SCRAMBLED_CHARACTER_SELECTOR + "').length === 0");

        assertEquals(0, page.locator(SCRAMBLED_CHARACTER_SELECTOR).count());
        assertEquals("NewWord".length(), getPositionInputs().count());
    }

    @Test
    protected void pressingSpaceAdvancesToNextPositionField() {
        enterLetters(TEST_LETTERS);
        scramble();

        Locator inputs = getPositionInputs();
        inputs.first().focus();
        inputs.first().press(" ");
        page.waitForTimeout(300);

        assertTrue(Boolean.TRUE.equals(inputs.nth(1).evaluate("el => document.activeElement === el")),
            "Focus should move to the second position field after pressing space");
    }

    @Test
    protected void pressingBackspaceOnEmptyFieldMovesToPrevious() {
        enterLetters(TEST_LETTERS);
        scramble();

        Locator inputs = getPositionInputs();
        inputs.nth(1).focus();
        inputs.nth(1).press("Backspace");
        page.waitForTimeout(300);

        assertTrue(Boolean.TRUE.equals(inputs.first().evaluate("el => document.activeElement === el")),
            "Focus should move to the first position field after pressing backspace");
    }

    private Locator getPositionInputs() {
        return page.locator(POSITION_FIELD_SELECTOR);
    }

    private Locator getScrambleButton() {
        return page.getByRole(AriaRole.BUTTON, new Page.GetByRoleOptions().setName(AnascrambleView.SCRAMBLE_BTN_TEXT));
    }

    private void enterLetters(String letters) {
        page.getByLabel(AnascrambleView.SCRAMBLE_FLD_LBL).fill(letters);
    }

    private void scramble() {
        scramble(TEST_LETTERS);
    }

    private void scramble(String letters) {
        getScrambleButton().click();
        page.waitForFunction("() => document.querySelectorAll('" + SCRAMBLED_CHARACTER_SELECTOR + "').length === "
            + letters.length());
    }
}
