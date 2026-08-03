package net.tjh90.website.core;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

public class PointTest {

    private static final double TOLERANCE = 1E-9;

    @Test
    public void distanceSquaredOfIdenticalPointsIsZero() {
        Point p = new Point(3.0, -4.0);

        assertEquals(0.0, Point.distanceSquared(p, p), TOLERANCE);
    }

    @Test
    public void distanceSquaredIsSymmetric() {
        Point p0 = new Point(1.0, 2.0);
        Point p1 = new Point(-3.0, 5.0);

        assertEquals(Point.distanceSquared(p0, p1), Point.distanceSquared(p1, p0), TOLERANCE);
    }

    @Test
    public void distanceSquaredCalculatesPythagoreanValue() {
        Point p0 = new Point(0.0, 0.0);
        Point p1 = new Point(3.0, 4.0);

        assertEquals(25.0, Point.distanceSquared(p0, p1), TOLERANCE);
    }

    @Test
    public void distanceSquaredHandlesNegativeCoordinates() {
        Point p0 = new Point(-1.0, -1.0);
        Point p1 = new Point(2.0, 3.0);

        assertEquals(25.0, Point.distanceSquared(p0, p1), TOLERANCE);
    }
}
