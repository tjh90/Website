# Feature Specification: Anascramble Page

**Feature Branch**: `rewrite` (spec-kit feature id `003-anascramble-page`)

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "Can we create a new Anascramble page implemented like the one currently on main?"

## Reference Implementation

The Anascramble page on the `main` branch is the behavioural reference. It is a solving aid for
anagram puzzles (e.g. crossword anagram clues). Relevant behaviour:

- The page is listed as "Anascramble" in the navigation drawer, directly after Home, and has its
  own address (`/anascramble`). Its header and tab title are "Anascramble".
- From top to bottom the page shows: a square scramble area, a "Solution:" row (hidden until enough
  letters are entered), a "Letters to scramble" text field and a primary "Scramble!" button, all
  centred.
- The text field accepts only letters and digits, at most 30 characters. "Scramble!" is disabled
  until at least 3 characters have been entered.
- Choosing "Scramble!" shows each entered character, in upper case and a handwritten-style font,
  at a random position around the centre of the scramble area. Characters never overlap; with more
  characters they spread further out from the centre. Each press gives a new arrangement.
- Once 3 or more characters are entered, the "Solution:" row shows one single-letter box per
  character. Typing a letter into a box is accepted only if that letter is still unused among the
  entered characters (case-insensitive, respecting repeats); otherwise the box is cleared. An
  accepted letter "uses up" one matching scrambled character, which is dimmed in the scramble area;
  clearing the box undims it.
- Keyboard conveniences in the solution row: an accepted letter moves focus to the next box;
  Backspace in an empty box moves focus to the previous box; Space clears the current box and moves
  to the next.
- Changing the letters to scramble clears the scramble area and resets the solution row.
- Nothing is stored; leaving or reloading the page discards the puzzle.

Known shortcomings of the reference, corrected here:

- The scramble area is a fixed 400 px square, so it overflows narrow (phone) screens. Here it MUST
  fit the screen width (FR-007).
- Long inputs can place characters outside the scramble area. Here every character MUST stay
  visible inside it (FR-006).
- The handwritten font is loaded from a third-party font service. Here it MUST be self-hosted and
  credited (FR-021), as the constitution requires.

Deliberate changes from the reference:

- The letters field accepts letters only; digits are no longer allowed (see Clarifications).
- The solution row is one text field drawn as a row of letter cells instead of one box per letter.
  Space enters a blank (unknown letter) and Backspace deletes the previous character, as in any
  text field (see Clarifications).

## Clarifications

### Session 2026-11-14

- Q: The constitution forbids hand-written JavaScript, but the solution row's focus movements need
  more than HTML. Keep, reduce or drop them? → A: Keep all three (auto-advance, Backspace back,
  Space skip), driven by the server: the server's response decides where focus goes. No hand-written
  scripts; a short round-trip delay before focus moves is acceptable.
- Q: Main accepts digits in the letters field but not in the solution boxes. How should digits be
  handled? → A: Letters only, everywhere: the letters field no longer accepts digits.
- Q: How should dimmed (already used) scrambled letters meet the accessibility contrast rule? → A:
  Treat dimmed letters as inactive and exempt them from the contrast requirement; keep the
  reference's faded look (about 25% opacity).
- Q: In what order should a screen reader read out the scrambled letters? → A: In a freshly
  shuffled order on each scramble, provided this stays trivial (no dedicated assistive-technology
  code); otherwise it is not required.
- Q: (Raised in planning.) Server-driven focus cannot detect Backspace in an empty box under the
  site's Content Security Policy, and focus moves made by server round trips lose or misplace fast
  keystrokes. How should the solution row work? → A: As a single text field styled as a row of
  letter cells (the usual one-time-passcode pattern). The browser's own editing gives auto-advance,
  Backspace and Space (a blank = unknown letter), so no focus management is needed. This supersedes
  the "server decides focus" answer above.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scramble letters (Priority: P1)

A puzzle solver stuck on an anagram clue opens Anascramble, types the clue's letters and presses
"Scramble!". The letters appear jumbled around a central point, helping them see new word shapes.
They press again for a fresh arrangement.

**Why this priority**: This is the core purpose of the page; it delivers value on its own.

**Independent Test**: Open the page, enter letters of varying lengths, press "Scramble!" repeatedly
and check every character appears once, upper case, non-overlapping, inside the area, in a new
arrangement each time.

**Acceptance Scenarios**:

1. **Given** the page is open with an empty field, **When** the visitor views it, **Then**
   "Scramble!" is disabled and the scramble area is empty.
2. **Given** the visitor has typed fewer than 3 characters, **When** they view the button, **Then**
   it is disabled; **When** they type a third character, **Then** it becomes enabled.
3. **Given** the visitor types a character other than a letter (e.g. a digit), or a 31st character,
   **When** they type it, **Then** it is not entered.
4. **Given** 3–30 valid characters are entered, **When** the visitor presses "Scramble!", **Then**
   each character appears exactly once in upper case in the scramble area, none overlap, and all are
   fully inside the area.
5. **Given** letters have been scrambled, **When** the visitor presses "Scramble!" again, **Then**
   the same characters are shown in a different arrangement.
6. **Given** letters have been scrambled, **When** the visitor edits the field, **Then** the
   scramble area is cleared.
7. **Given** the visitor presses Enter in the field with 3 or more characters entered, **When** the
   form is submitted, **Then** it behaves the same as pressing "Scramble!".

---

### User Story 2 - Build the solution (Priority: P2)

Having spotted a likely word, the solver types letters into the "Solution:" field, one cell per
letter. Each letter they place is dimmed in the scramble so they can see which letters remain.
Letters they don't have are refused.

**Why this priority**: Valuable for longer anagrams but only useful once scrambling works.

**Independent Test**: Enter letters with repeats (e.g. "LETTER"), scramble, type available,
repeated and unavailable letters into the solution field, delete some, and check acceptance and
dimming.

**Acceptance Scenarios**:

1. **Given** fewer than 3 characters are entered, **When** the visitor views the page, **Then** no
   solution row is shown.
2. **Given** N (≥ 3) characters are entered, **When** the visitor views the page, **Then** a
   "Solution:" field drawn as N empty letter cells is shown, before scrambling.
3. **Given** "LETTER" is entered and scrambled, **When** the visitor types "t" in the solution
   field, **Then** it is shown as "T" and one scrambled "T" is dimmed; **When** they type a second
   "T", **Then** the second "T" is dimmed; **When** they type a third "T", **Then** it is refused
   and removed.
4. **Given** a letter not among the entered characters, **When** the visitor types it in the
   solution field, **Then** it is refused and removed.
5. **Given** the solution holds an accepted letter, **When** the visitor deletes it, **Then** the
   corresponding scrambled character is no longer dimmed and the letter becomes available again.
6. **Given** the solution has letters, **When** the visitor presses "Scramble!" again, **Then** the
   solution keeps its letters and the matching characters in the new arrangement are dimmed.
7. **Given** the solution has letters, **When** the visitor edits the letters to scramble, **Then**
   the solution is reset to empty cells matching the new length.
8. **Given** letters are typed or deleted in the solution, **When** the visitor has not scrambled
   yet, **Then** letters are still accepted or refused as above (there is simply nothing to dim).

---

### User Story 3 - Fast keyboard entry in the solution row (Priority: P3)

The solver types a candidate answer straight through without reaching for the mouse: each letter
lands in the next cell, Space leaves a cell blank (unknown) and moves on, and Backspace steps back.

**Why this priority**: Convenience that matches the reference; it comes from the browser's normal
text editing, so it needs no extra behaviour.

**Independent Test**: With a keyboard only, type a word into the solution field using Space for
unknown letters and Backspace to correct, and check which cell each letter appears in.

**Acceptance Scenarios**:

1. **Given** the caret is in the solution field, **When** the visitor types an accepted letter,
   **Then** it appears in the current cell and the caret moves to the next cell.
2. **Given** the caret is after a character, **When** the visitor presses Backspace, **Then** that
   character is removed and the caret moves back one cell.
3. **Given** the caret is in the solution field, **When** the visitor presses Space, **Then** the
   current cell is left blank (unknown) and the caret moves to the next cell.
4. **Given** a refused letter, **When** the visitor types it, **Then** it is removed and the caret
   stays in the same cell.
5. **Given** the visitor types quickly, **When** feedback arrives, **Then** no accepted keystroke is
   lost or lands in the wrong cell.
6. **Given** all N cells are filled (letters or blanks), **When** the visitor types another
   character, **Then** it is not entered.

---

### Edge Cases

- **Digits and other characters**: only letters can be entered in the letters field, and only
  letters and spaces (blanks) in the solution field; digits and punctuation are removed.
- **Trailing blanks**: cells after the last typed character count as unknown, the same as blanks.
- **Long words on narrow screens**: the solution cells shrink to fit; if they would become too
  small to read, the solution row may scroll sideways within itself (never the whole page).
- **Lower case input**: the letters field and solution field accept lower case; scrambled characters
  and solution letters are shown in upper case, and matching is case-insensitive.
- **Exactly 30 characters**: all fit inside the scramble area without overlap on every supported
  screen width.
- **Pasting text**: pasted characters that are not letters are discarded, and the result
  is cut to 30 characters.
- **Clearing the field**: the scramble area is emptied, the solution row is hidden and "Scramble!"
  is disabled.
- **JavaScript disabled**: the page still works by full form submission: entering letters and
  pressing "Scramble!" shows the scramble and a solution row; typing a solution and submitting
  (which also re-scrambles) refuses unavailable letters and updates the dimming. Instant
  (as-you-type) updates are not required.
- **Theme switching**: scrambled characters and the solution field are readable, and dimmed
  characters clearly distinguishable from undimmed ones, in both light and dark themes; switching
  theme does not lose the current puzzle.
- **In-place navigation**: arriving at the page from the drawer behaves as a full page load would;
  leaving discards the puzzle.
- **Reduced motion**: no animation is required; if any is added, it is suppressed for visitors who
  prefer reduced motion.

## Requirements *(mandatory)*

### Functional Requirements

#### Page and navigation

- **FR-001**: The site MUST provide an Anascramble page at `/anascramble` with header and tab title
  "Anascramble", following the site's existing title format.
- **FR-002**: The navigation drawer MUST list "Anascramble" directly after Home, with the current
  page indicator working as for other pages.
- **FR-003**: The page MUST show, centred and in this order: the scramble area, the solution row,
  the "Letters to scramble" field and the "Scramble!" button.

#### Letters and scrambling

- **FR-004**: The "Letters to scramble" field MUST accept only letters A–Z (either case), at most 30
  characters. "Scramble!" MUST be enabled only when 3–30 valid characters are
  entered.
- **FR-005**: Pressing "Scramble!" (or submitting the field with Enter) MUST display every entered
  character exactly once, in upper case and the site's handwritten display font, at a randomly
  chosen position clustered around the centre of the scramble area.
- **FR-006**: Scrambled characters MUST NOT overlap one another and MUST lie entirely inside the
  scramble area for any valid input length.
- **FR-007**: The scramble area MUST be square, about 400 px wide on larger screens, and MUST shrink
  to fit narrower screens without horizontal scrolling while keeping FR-006 true.
- **FR-008**: Each press of "Scramble!" MUST produce a new random arrangement. Arrangements MUST be
  reproducible from a given seed for testing.
- **FR-009**: Any change to the letters to scramble MUST clear the scramble area.

#### Solution row

- **FR-010**: When 3–30 characters are entered, a "Solution:" row MUST show a single text field,
  labelled "Solution", drawn as one cell per entered character and accepting at most that many
  characters; otherwise it MUST be hidden. Each character position MUST line up with its cell.
- **FR-011**: The solution field MUST accept letters and spaces only. A space is a blank (unknown
  letter). A letter MUST be accepted only if it (case-insensitive) is among the entered characters
  and not already used earlier in the solution, counting repeats; refused letters and other
  characters MUST be removed. Accepted letters MUST be shown in upper case.
- **FR-012**: For each accepted solution letter, exactly one matching scrambled character MUST be
  shown dimmed (faded to about 25% opacity, as in the reference); deleting the letter MUST undim it.
  Dimmed characters count as inactive and are exempt from the contrast requirement in FR-019.
  Dimming MUST follow the solution letters across re-scrambles.
- **FR-013**: Any change to the letters to scramble MUST reset the solution field to empty cells
  matching the new length.
- **FR-014**: Acceptance, refusal and dimming MUST update as the visitor types, without a page
  reload, when JavaScript is available.
- **FR-015**: Keyboard entry in the solution field MUST behave as in User Story 3 using the
  browser's own text editing; the page MUST NOT move focus itself. Feedback from the server MUST NOT
  move the caret, or lose or misplace accepted characters typed while it was pending.

#### Robustness, privacy and accessibility

- **FR-016**: All scrambling and letter-availability rules MUST be decided by the server, which MUST
  validate all submitted input and respond safely to invalid or tampered input (e.g. over-long or
  disallowed characters) without error pages.
- **FR-017**: The page MUST work without JavaScript through standard form submission, as described
  in Edge Cases.
- **FR-018**: The page MUST NOT store anything in the visitor's browser or on the server; the
  puzzle lasts only while the page is open.
- **FR-019**: The page MUST meet WCAG 2.2 AA in both themes, including contrast of undimmed
  scrambled characters (dimmed ones are exempt, see FR-012), labelled controls, keyboard
  operability and the site's touch-target size.
  Assistive technology MUST encounter the scrambled characters in a random order that changes on
  each scramble (not the typed order). This SHOULD come for free from the order in which the
  characters are placed on the page; no dedicated assistive-technology handling is required.
- **FR-020**: Automated accessibility scans MUST report no serious or critical violations on the
  page in either theme, before and after scrambling and with some characters dimmed. Dimmed
  characters MUST be marked as inactive so that the exemption is recognised, not suppressed by
  disabling the contrast check for the whole page.
- **FR-021**: The handwritten display font MUST be self-hosted, have an AGPL-compatible licence, and
  be credited on the About page if its licence requires it.

### Key Entities

- **Letters to scramble**: the visitor's 3–30 letters; the puzzle's source characters.
- **Scrambled character**: one source character with a position in the scramble area and a dimmed
  flag.
- **Solution**: an ordered list, one slot per source character, each empty or holding a letter;
  determines which scrambled characters are dimmed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A visitor can go from opening the page to seeing their letters scrambled in under 10
  seconds.
- **SC-002**: Scrambled letters appear within 1 second of pressing "Scramble!", and solution
  feedback (accept/refuse/dim) within 0.5 seconds of typing, on a typical connection.
- **SC-003**: Across 1,000 scrambles of random 3–30 letter inputs, 100% show every character
  exactly once, with no overlaps and none outside the area, at both phone (360 px) and desktop
  widths.
- **SC-004**: 100% of the reference behaviours listed under Reference Implementation (other than the
  corrected shortcomings and any clarified changes) are verifiably reproduced.
- **SC-005**: The page has no horizontal scrolling at 320 px width and above.
- **SC-006**: Zero serious or critical accessibility violations in automated scans in both themes.

## Assumptions

- "Implemented like the one on main" means the same visitor-facing behaviour, rebuilt with this
  branch's technology stack and conventions, not a port of main's code.
- The handwritten font is the one used on main (a freely licensed Google Font), self-hosted.
- Character spacing and spread may differ slightly from the reference as long as letters cluster
  around the centre and FR-006 holds.
- No answer checking, dictionary lookup or solving help is in scope; the page is a visual aid only.
