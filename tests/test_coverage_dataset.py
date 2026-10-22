import unittest
from unittest.mock import patch

from astrakyle.coverage_dataset import configurations, evaluate
from astrakyle.two_satellites import run


class CoverageDatasetTests(unittest.TestCase):
    def test_design_is_reproducible_and_unique(self):
        pilot = configurations()
        self.assertEqual(len(pilot), 64)
        self.assertEqual(len({tuple(c.values()) for c in pilot}), 64)
        self.assertEqual(configurations(10, 7), configurations(10, 7))
        self.assertNotEqual(configurations(10, 7), configurations(10, 8))
        for c in configurations(100):
            self.assertTrue(0 <= c['second_raan_deg'] < 360)
            self.assertTrue(0 <= c['second_initial_angle_deg'] < 360)
            self.assertTrue(-70 <= c['latitude_deg'] <= 70)

    def test_phase_preserves_default_and_coincident_satellites(self):
        default = run(window_s=86400)
        explicit = run(window_s=86400, second_initial_angle_deg=180)
        self.assertEqual(default, explicit)
        coincident = run(window_s=86400, second_initial_angle_deg=0)
        self.assertEqual(coincident[2][0], coincident[2][1])
        self.assertEqual(coincident[4]['combined'], coincident[4]['satellite_1'])
        self.assertNotEqual(default[4]['combined'], coincident[4]['combined'])

    def test_unreachable_station_label(self):
        config = dict(second_raan_deg=90., second_initial_angle_deg=270., latitude_deg=70.)
        row = evaluate(config)
        self.assertEqual(row['quality_status'], 'checked')
        self.assertEqual(row['access_fraction'], 0)
        self.assertEqual(row['longest_gap_s'], 604800)

    def test_disagreement_is_not_accepted_as_training_truth(self):
        coarse = dict(total_access_s=100, longest_gap_s=1000, interval_count=2,
                      access_fraction=100 / 604800)
        fine = dict(total_access_s=110, longest_gap_s=990, interval_count=3,
                    access_fraction=110 / 604800)
        result = lambda metrics: (None, None, None, None, {'combined': metrics})
        with patch('astrakyle.coverage_dataset.run', side_effect=[result(coarse), result(fine)]):
            row = evaluate(configurations()[0])
        self.assertEqual(row['quality_status'], 'unresolved')
        self.assertEqual(row['access_fraction'], fine['access_fraction'])
        self.assertEqual(row['access_difference_s'], 10)

    def test_invalid_generation_settings(self):
        for step in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                evaluate(configurations()[0], step_s=step)
        with self.assertRaises(ValueError):
            configurations(0)
