import math
import unittest

from astrakyle.access import access_metrics, merge_intervals
from astrakyle.two_satellites import run


class AccessTests(unittest.TestCase):
    def test_union_with_overlap_nesting_touching_and_disjoint_intervals(self):
        intervals = [(8, 12), (2, 5), (3, 4), (4, 8), (15, 17), (2, 5)]
        self.assertEqual(merge_intervals(intervals), [(2, 12), (15, 17)])
        metrics = access_metrics(intervals, 20)
        self.assertEqual(metrics['total_access_s'], 12)
        self.assertEqual(metrics['access_fraction'], 0.6)
        self.assertEqual(metrics['longest_gap_s'], 3)
        self.assertEqual(metrics['beginning_gap_s'], 2)
        self.assertEqual(metrics['ending_gap_s'], 3)

    def test_empty_and_full_window(self):
        empty = access_metrics([], 20)
        self.assertEqual(empty['total_access_s'], 0)
        self.assertEqual(empty['longest_gap_s'], 20)
        self.assertEqual(len(empty['gaps']), 1)
        full = access_metrics([(0, 20)], 20)
        self.assertEqual(full['access_fraction'], 1)
        self.assertEqual(full['longest_gap_s'], 0)
        self.assertEqual(full['gaps'], [])

    def test_two_satellite_geometry_convergence_and_accounting(self):
        orbits, _, _, merged, metrics = run(10)
        _, _, _, fine, fine_metrics = run(5)
        for t in (0, 1234, 86400):
            a, b = (o.position_eci(t) for o in orbits)
            self.assertLess(math.hypot(*(x + y for x, y in zip(a, b))), 1e-8)
        self.assertEqual(len(merged), len(fine))
        for coarse_interval, fine_interval in zip(merged, fine):
            for a, b in zip(coarse_interval, fine_interval):
                self.assertAlmostEqual(a, b, delta=0.002)
        combined = metrics['combined']
        self.assertGreaterEqual(combined['total_access_s'], metrics['satellite_1']['total_access_s'])
        self.assertLessEqual(combined['total_access_s'], sum(metrics[k]['total_access_s'] for k in ['satellite_1', 'satellite_2']))
        self.assertAlmostEqual(combined['total_access_s'] + sum(g['duration_s'] for g in combined['gaps']), 86400)
        self.assertAlmostEqual(combined['total_access_s'], fine_metrics['combined']['total_access_s'], delta=0.01)
        self.assertAlmostEqual(combined['longest_gap_s'], fine_metrics['combined']['longest_gap_s'], delta=0.002)
