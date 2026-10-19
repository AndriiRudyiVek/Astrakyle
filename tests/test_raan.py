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

    def test_seven_days_continue_original_epoch_and_preserve_cross_day_gaps(self):
        from astrakyle.access import access_metrics
        from astrakyle.geometry import elevation_deg
        for raan in RAAN_VALUES:
            day = run(10, raan)
            week = run(10, raan, 7 * 86400)
            fine = run(5, raan, 7 * 86400)
            for index in (0, 1):
                times, values, _ = week[2][index]
                self.assertEqual(times[:8641], day[2][index][0])
                self.assertEqual(values[:8641], day[2][index][1])
                for t in (86410, 345600, 604800):
                    self.assertAlmostEqual(values[int(t / 10)],
                        elevation_deg(week[0][index], week[1], t), places=12)
            metrics = week[4]['combined']
            self.assertEqual(metrics['window_s'], 604800)
            self.assertEqual(len(week[3]), len(fine[3]))
            for a, b in zip(week[3], fine[3]):
                for x, y in zip(a, b):
                    self.assertAlmostEqual(x, y, delta=0.002)
            self.assertAlmostEqual(metrics['total_access_s'] + sum(g['duration_s'] for g in metrics['gaps']), 604800)
            self.assertAlmostEqual(metrics['longest_gap_s'], fine[4]['combined']['longest_gap_s'], delta=0.002)
            first_day = [(s, min(e, 86400)) for s, e in week[3] if s < 86400]
            self.assertEqual(access_metrics(first_day, 86400), day[4]['combined'])
        # A gap spanning a daily reporting boundary must remain one full gap.
        metrics = access_metrics([(0, 80000), (100000, 172800)], 172800)
        self.assertEqual(metrics['longest_gap_s'], 20000)
