import math
import unittest
from dataclasses import asdict

from astrakyle.raan_sweep import RAAN_VALUES
from astrakyle.two_satellites import run


class RaanTests(unittest.TestCase):
    def test_only_second_raan_changes_and_union_converges(self):
        baseline = run()
        for raan in RAAN_VALUES:
            orbits, station, samples, merged, metrics = run(10, raan)
            fine = run(5, raan)
            self.assertEqual(orbits[0], baseline[0][0])
            self.assertEqual(station, baseline[1])
            expected = asdict(baseline[0][1])
            expected['raan_deg'] = raan
            self.assertEqual(asdict(orbits[1]), expected)
            self.assertEqual(samples[0][2], baseline[2][0][2])
            self.assertEqual(len(merged), len(fine[3]))
            for a, b in zip(merged, fine[3]):
                for x, y in zip(a, b):
                    self.assertAlmostEqual(x, y, delta=0.002)
            combined = metrics['combined']
            self.assertAlmostEqual(combined['total_access_s'] + sum(g['duration_s'] for g in combined['gaps']), 86400)
            self.assertAlmostEqual(combined['total_access_s'], fine[4]['combined']['total_access_s'], delta=0.02)
            self.assertAlmostEqual(combined['longest_gap_s'], fine[4]['combined']['longest_gap_s'], delta=0.002)
            theta = math.radians(raan)
            for t in (0, 1234, 86400):
                x, y, z = baseline[0][1].position_eci(t)
                rotated = (math.cos(theta)*x-math.sin(theta)*y,
                           math.sin(theta)*x+math.cos(theta)*y, z)
                actual = orbits[1].position_eci(t)
                for a, b in zip(actual, rotated):
                    self.assertAlmostEqual(a, b, delta=1e-9)
