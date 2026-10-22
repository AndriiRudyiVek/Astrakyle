import unittest
try:
    import numpy as np
    from astrakyle.train_coverage import features, split_indices, errors
except ImportError:
    raise unittest.SkipTest('Install the ml extra to run model tests')


class TrainingTests(unittest.TestCase):
    def test_periodic_angles_and_signed_latitude(self):
        x = features([[0, 90, -30], [360, 450, -30]])
        np.testing.assert_allclose(x[0], x[1], atol=1e-12)
        self.assertEqual(x[0, -1], -30)
        with self.assertRaises(ValueError):
            features([[0, 0, 80]])

    def test_split_is_disjoint_complete_reproducible(self):
        splits = split_indices(1000, 42)
        self.assertEqual([len(s) for s in splits], [700, 150, 150])
        self.assertEqual(len(set(np.concatenate(splits))), 1000)
        for a, b in zip(splits, split_indices(1000, 42)):
            np.testing.assert_array_equal(a, b)

    def test_errors_use_absolute_physical_units(self):
        result = errors(np.array([0, .05]), np.array([.01, .03]), 100)
        self.assertAlmostEqual(result['mae'], 1.5)
        self.assertEqual(errors(np.array([]), np.array([]), 1), {'count': 0})

    def test_dataset_rejects_hash_mismatch_and_duplicate_angles(self):
        import csv
        import hashlib
        import json
        import tempfile
        from pathlib import Path
        from astrakyle.train_coverage import load_dataset
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            data = directory / 'dataset.csv'
            fields = ['configuration_id', 'second_raan_deg', 'second_initial_angle_deg',
                      'latitude_deg', 'access_fraction', 'longest_gap_s', 'quality_status']
            with data.open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(fields)
                for i in range(100):
                    writer.writerow([str(i), 360 * i, 0, 0, .05, 100, 'checked'])
            manifest = dict(status='complete', dataset_sha256='wrong')
            path = directory / 'manifest.json'
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'hash'):
                load_dataset(directory)
            manifest['dataset_sha256'] = hashlib.sha256(data.read_bytes()).hexdigest()
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'equivalent'):
                load_dataset(directory)
