import math
import unittest

from astrakyle.geometry import (CircularOrbit, GroundStation, EARTH_RADIUS_KM,
                               EARTH_ROTATION_RAD_S, eci_to_ecef, elevation_deg)
from astrakyle.passes import simulate


class GeometryTests(unittest.TestCase):
    def test_orbit_radius_period_and_quarter_orbit(self):
        orbit = CircularOrbit(inclination_deg=90)
        for t in (0, 100, 1500, orbit.period_s):
            self.assertAlmostEqual(math.hypot(*orbit.position_eci(t)), 6878)
        self.assertAlmostEqual(orbit.position_eci(orbit.period_s / 4)[2], 6878)
        self.assertAlmostEqual(orbit.position_eci(orbit.period_s)[0], 6878)

    def test_rotation_sign(self):
        result = eci_to_ecef((1, 0, 0), math.pi / (2 * EARTH_ROTATION_RAD_S))
        self.assertAlmostEqual(result[0], 0)
        self.assertAlmostEqual(result[1], -1)

    def test_overhead_and_opposite(self):
        station = GroundStation(0, 0)
        self.assertAlmostEqual(elevation_deg(CircularOrbit(inclination_deg=0), station, 0), 90)
        self.assertAlmostEqual(elevation_deg(CircularOrbit(initial_angle_deg=180), station, 0), -90)

    def test_equatorial_pass_matches_analytic_crossing(self):
        orbit, station = CircularOrbit(inclination_deg=0, initial_angle_deg=-30), GroundStation(0, 0)
        threshold = 10
        e = math.radians(threshold)
        angle = math.acos(EARTH_RADIUS_KM / 6878 * math.cos(e)) - e
        speed = orbit.angular_speed - EARTH_ROTATION_RAD_S
        expected_start = (math.radians(30) - angle) / speed
        expected_end = (math.radians(30) + angle) / speed
        _, _, passes = simulate(lambda t: elevation_deg(orbit, station, t), 1200, 10, threshold)
        self.assertEqual(len(passes), 1)
        self.assertAlmostEqual(passes[0].start_s, expected_start, delta=0.001)
        self.assertAlmostEqual(passes[0].end_s, expected_end, delta=0.001)
        self.assertAlmostEqual(passes[0].peak_elevation_deg, 90, places=5)

    def test_empty_full_and_clipped_windows(self):
        self.assertEqual(simulate(lambda t: -5, 25, 10)[2], [])
        times, _, passes = simulate(lambda t: 20, 25, 10)
        self.assertEqual(times, [0, 10, 20, 25])
        self.assertEqual(passes[0].duration_s, 25)
        self.assertTrue(passes[0].clipped_start and passes[0].clipped_end)
        self.assertTrue(simulate(lambda t: 20 - t, 30, 3)[2][0].clipped_start)
        self.assertTrue(simulate(lambda t: t, 30, 3)[2][0].clipped_end)

    def test_full_day_radius_and_rotation_length(self):
        orbit = CircularOrbit()
        expected = EARTH_RADIUS_KM + orbit.altitude_km
        for t in range(0, 86401, 5):
            inertial = orbit.position_eci(t)
            fixed = eci_to_ecef(inertial, t)
            self.assertAlmostEqual(math.hypot(*inertial), expected, delta=1e-9)
            self.assertAlmostEqual(math.hypot(*fixed), math.hypot(*inertial), delta=1e-9)

    def test_half_step_convergence_and_final_pass(self):
        orbit, station = CircularOrbit(), GroundStation()
        elevation = lambda t: elevation_deg(orbit, station, t)
        coarse = simulate(elevation, step_s=10)[2]
        fine = simulate(elevation, step_s=5)[2]
        self.assertEqual(len(coarse), 6)
        self.assertEqual(len(coarse), len(fine))
        for a, b in zip(coarse, fine):
            self.assertAlmostEqual(a.start_s, b.start_s, delta=0.002)
            self.assertAlmostEqual(a.end_s, b.end_s, delta=0.002)
            self.assertAlmostEqual(a.duration_s, b.duration_s, delta=0.002)
            self.assertAlmostEqual(a.peak_elevation_deg, b.peak_elevation_deg, delta=1e-6)
        self.assertLess(fine[-1].end_s, 86400)
        self.assertFalse(fine[-1].clipped_end)
        # Move the cutoff inside a real pass to verify partial-window labeling.
        cutoff = (fine[-1].start_s + fine[-1].end_s) / 2
        partial = simulate(elevation, duration_s=cutoff, step_s=5)[2][-1]
        self.assertTrue(partial.clipped_end)
        self.assertEqual(partial.end_s, cutoff)
        self.assertLess(partial.duration_s, fine[-1].duration_s)

    def test_invalid_inputs(self):
        for kwargs in ({'step_s': 0}, {'duration_s': -1}, {'minimum_deg': 91}, {'step_s': float('nan')}):
            with self.assertRaises(ValueError):
                simulate(lambda t: 0, **kwargs)
        with self.assertRaises(ValueError):
            GroundStation(91, 0)
        with self.assertRaises(ValueError):
            CircularOrbit(altitude_km=-1)


if __name__ == '__main__':
    unittest.main()
