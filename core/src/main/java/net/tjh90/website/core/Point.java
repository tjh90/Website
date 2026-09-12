package net.tjh90.website.core;

/// A point in 2D space.
public record Point(double x, double y) {

  /// @return the squared distance between the two points, `p0` and `p1`.
  public static double distanceSquared(final Point p0, final Point p1) {
    double xDiff = p0.x() - p1.x();
    double yDiff = p0.y() - p1.y();

    return xDiff * xDiff + yDiff * yDiff;
  }
}
