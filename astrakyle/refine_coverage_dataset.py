"""Copy a dataset and refine unresolved labels without changing its inputs."""
import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .coverage_dataset import evaluate, provenance


def refine(source, output, attempts=4):
    manifest = json.loads((source / 'manifest.json').read_text())
    original = (source / 'dataset.csv').read_bytes()
    if manifest.get('status') not in ('complete', 'needs_review'):
        raise ValueError('Source generation must have finished')
    if hashlib.sha256(original).hexdigest() != manifest['dataset_sha256']:
        raise ValueError('Source hash mismatch')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory must be empty')
    with (source / 'dataset.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    history = []
    for i, row in enumerate(rows):
        if row['quality_status'] == 'checked':
            continue
        config = {k: float(row[k]) for k in ('second_raan_deg', 'second_initial_angle_deg', 'latitude_deg')}
        accumulated_s = float(row['simulation_wall_s'])
        for _ in range(attempts):
            previous = row
            row = evaluate(config, float(row['step_s']) / 2, manifest['tolerance_s'])
            accumulated_s += row['simulation_wall_s']
            history.append(dict(configuration_id=row['configuration_id'],
                old_step_s=float(previous['step_s']), new_step_s=row['step_s'],
                quality_status=row['quality_status']))
            if row['quality_status'] == 'checked':
                break
        row['simulation_wall_s'] = accumulated_s
        rows[i] = row
        print(f"Refined {i + 1}: {row['quality_status']} at {row['fine_step_s']} s", flush=True)
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'dataset.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    checked = sum(row['quality_status'] == 'checked' for row in rows)
    manifest.update(parent_dataset_sha256=manifest['dataset_sha256'], refinement_history=history,
        refinement_provenance=provenance(), refined_at=datetime.now(timezone.utc).isoformat(),
        status='complete' if checked == len(rows) else 'needs_review', checked_count=checked,
        unresolved_count=len(rows) - checked, label_resolution='per-row fine_step_s',
        dataset_sha256=hashlib.sha256((output / 'dataset.csv').read_bytes()).hexdigest())
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        refine(args.dataset, args.output)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
