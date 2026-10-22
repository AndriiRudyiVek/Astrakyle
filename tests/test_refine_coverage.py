import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from astrakyle.refine_coverage_dataset import refine


class RefinementTests(unittest.TestCase):
    def test_refinement_preserves_source_and_records_cost_and_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / 'source', Path(tmp) / 'refined'
            source.mkdir()
            row = dict(configuration_id='a', second_raan_deg=0., second_initial_angle_deg=90.,
                       latitude_deg=30., step_s=10., fine_step_s=5., simulation_wall_s=1.,
                       quality_status='unresolved')
            with (source / 'dataset.csv').open('w', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            original = (source / 'dataset.csv').read_bytes()
            digest = hashlib.sha256(original).hexdigest()
            (source / 'manifest.json').write_text(json.dumps(dict(status='needs_review',
                dataset_sha256=digest, tolerance_s=.1)))
            corrected = dict(row, step_s=5., fine_step_s=2.5, simulation_wall_s=2., quality_status='checked')
            with patch('astrakyle.refine_coverage_dataset.evaluate', return_value=corrected) as evaluate:
                refine(source, output)
            self.assertEqual(evaluate.call_args.args[1], 5.)
            self.assertEqual((source / 'dataset.csv').read_bytes(), original)
            report = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(report['status'], 'complete')
            self.assertEqual(report['parent_dataset_sha256'], digest)
            with (output / 'dataset.csv').open() as stream:
                saved = next(csv.DictReader(stream))
            self.assertEqual(float(saved['simulation_wall_s']), 3.)
            self.assertEqual(float(saved['fine_step_s']), 2.5)
