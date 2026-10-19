import math
import unittest

from astrakyle.geometry import CircularOrbit, GroundStation, elevation_deg, EARTH_RADIUS_KM
from astrakyle.two_satellites import run


class LatitudeTests(unittest.TestCase):
    def test_equatorial_180_raan_elevations_coincide(self):
        station = GroundStation(0, 30.52)
        a = CircularOrbit()
        b = CircularOrbit(raan_deg=180, initial_angle_deg=180)
        for t in range(0, 604801, 300):
            self.assertAlmostEqual(elevation_deg(a, station, t), elevation_deg(b, station, t), delta=1e-9)

    def test_high_latitude_outside_elevation_footprint(self):
        minimum = math.radians(10)
        reach = math.degrees(math.acos(EARTH_RADIUS_KM / (EARTH_RADIUS_KM + 500)
                                      * math.cos(minimum)) - minimum)
        self.assertLess(53 + reach, 70)

    def test_latitude_is_only_changed_input_and_no_access_is_one_gap(self):
        baseline = run(10, 120, 604800)
        changed = run(10, 120, 604800, 70)
        self.assertEqual(baseline[0], changed[0])
        self.assertEqual(baseline[1].longitude_deg, changed[1].longitude_deg)
        self.assertEqual(changed[1].latitude_deg, 70)
        metrics = changed[4]['combined']
        self.assertEqual(metrics['access_fraction'], 0)
        self.assertEqual(metrics['longest_gap_s'], 604800)
        self.assertEqual(len(metrics['gaps']), 1)
        self.assertEqual(metrics['gaps'][0], dict(start_s=0.0, end_s=604800, duration_s=604800))
