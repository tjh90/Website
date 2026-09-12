package net.tjh90.website.core.anascramble;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import net.tjh90.website.core.Point;

/// Handles random scrambling of constituent characters in a [String].
///
/// Uses an offset length from a centre position combined with a randomly generated direction to
/// iteratively determine the scrambled position of each character in a given `String`. If no
/// position can be found that does not overlap with a previously allocated location, then the
/// length of the offset is increased. This keeps letters roughly congregated around the centre
/// point regardless of the length of the supplied `String`.
public class CharacterScrambler {

  private static final double BUFFER_ZONE = 50.0;
  private static final double BUFFER_ZONE_SQUARED = BUFFER_ZONE * BUFFER_ZONE;

  private static final double DEFAULT_INITIAL_OFFSET = 50.0;
  private static final double DEFAULT_OFFSET_INCR = 5.0;

  private final Random random;
  private final double initialOffset;
  private final double offsetIncr;

  private List<Point> letterLocations = new ArrayList<>();

  /// Default constructor.
  public CharacterScrambler() {
    this(0L, DEFAULT_INITIAL_OFFSET, DEFAULT_OFFSET_INCR);
  }

  /// Constructor.
  ///
  /// @param seed the seed to use for the random number generator.
  public CharacterScrambler(long seed) {
    this(seed, DEFAULT_INITIAL_OFFSET, DEFAULT_OFFSET_INCR);
  }

  /// Constructor.
  ///
  /// @param seed the seed to use for the random number generator.
  /// @param initialOffset the initial length of the vector used to offset letters from the centre.
  /// @param offsetIncr the amount to increment the length of the vector by when characters need to
  ///                   be placed further from the centre to avoid overlaps.
  public CharacterScrambler(long seed, double initialOffset, double offsetIncr) {
    random = new Random(seed);
    this.initialOffset = initialOffset > 0 ? initialOffset : DEFAULT_INITIAL_OFFSET;
    this.offsetIncr = offsetIncr > 0 ? offsetIncr : DEFAULT_OFFSET_INCR;
  }

  /// Take a [String] of letters, and compute a scrambled location for each one.
  ///
  /// @param lettersToScramble the `String` containing letters to scramble.
  ///
  /// @return a list of characters and their assigned scrambled location.
  public List<CharacterData> scramble(final String lettersToScramble) {
    letterLocations.clear();

    List<CharacterData> letters = new ArrayList<>();
    Double offset = initialOffset;
    for (char ch : lettersToScramble.toCharArray()) {
      Point p = getLetterPosition(offset);
      letterLocations.add(p);

      letters.add(new CharacterData(ch, p));
    }

    return letters;
  }

  private Point getLetterPosition(Double offset) {
    double theta = Math.TAU * random.nextDouble();
    Point p = new Point(offset * Math.sin(theta), offset * Math.cos(theta));

    int tries = 0;
    while (overlaps(p, letterLocations)) {
      theta = Math.TAU * random.nextDouble();
      p = new Point(offset * Math.sin(theta), offset * Math.cos(theta));

      tries++;
      if (tries % 10 == 0) {
        offset += offsetIncr;
      }
    }

    return p;
  }

  public boolean overlaps(final Point point, final List<Point> others) {
    return !others.isEmpty()
        && others.stream().anyMatch(p -> Point.distanceSquared(point, p) < BUFFER_ZONE_SQUARED);
  }
}
