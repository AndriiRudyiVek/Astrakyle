"""Generate reproducible, resolution-checked seven-day coverage labels."""
import argparse
import csv
import hashlib
import itertools
import json
import math
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .two_satellites import run

WINDOW_S = 604800


def configurations(count=None, seed=42):
    """The default is the 64-case pilot; count selects seeded random samples."""
    if count is None:
        values = itertools.product((0, 90, 180, 270), (0, 90, 180, 270), (0, 30, 50.45, 70))
    else:
        if count <= 0:
            raise ValueError('count must be positive')
        rng = random.Random(seed)
        values = ((rng.uniform(0, 360), rng.uniform(0, 360), rng.uniform(-70, 70))
                  for _ in range(count))
    return [dict(second_raan_deg=float(r), second_initial_angle_deg=float(a),
                 latitude_deg=float(lat)) for r, a, lat in values]


def evaluate(config, step_s=10.0, tolerance_s=0.1):
    """Use finer labels; retain unresolved rows with an explicit quality flag."""
    if not math.isfinite(step_s) or step_s <= 0:
        raise ValueError('step_s must be finite and positive')
    if not math.isfinite(tolerance_s) or tolerance_s < 0:
        raise ValueError('tolerance_s must be finite and nonnegative')
    identity = json.dumps(config, sort_keys=True, separators=(',', ':'))
    row = dict(configuration_id=hashlib.sha256(identity.encode()).hexdigest(), **config,
               step_s=step_s, fine_step_s=step_s / 2)
    start = time.perf_counter()
    coarse = run(step_s=step_s, window_s=WINDOW_S, **config)[4]['combined']
    fine = run(step_s=step_s / 2, window_s=WINDOW_S, **config)[4]['combined']
    access_diff = abs(coarse['total_access_s'] - fine['total_access_s'])
    gap_diff = abs(coarse['longest_gap_s'] - fine['longest_gap_s'])
    checked = (coarse['interval_count'] == fine['interval_count']
               and access_diff <= tolerance_s and gap_diff <= tolerance_s)
    row.update(access_fraction=fine['access_fraction'], longest_gap_s=fine['longest_gap_s'],
               interval_count=coarse['interval_count'], fine_interval_count=fine['interval_count'],
               access_difference_s=access_diff, longest_gap_difference_s=gap_diff,
               quality_status='checked' if checked else 'unresolved',
               simulation_wall_s=time.perf_counter() - start)
    return row


def provenance():
    root = Path(__file__).resolve().parent.parent
    def git(*args):
        try:
            return subprocess.check_output(['git', '-C', str(root), *args], text=True,
                                           stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    # Hash actual sources, including uncommitted files, rather than only HEAD.
    hashes = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((root / 'astrakyle').glob('*.py'))}
    return dict(git_revision=git('rev-parse', 'HEAD'),
                git_status=git('status', '--short'), source_sha256=hashes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count', type=int, help='Generate this many random cases instead of the pilot')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--step-s', type=float, default=10)
    parser.add_argument('--tolerance-s', type=float, default=0.1,
                        help='Maximum discrepancy in total access and longest gap (seconds)')
    parser.add_argument('--output', type=Path, default=Path('outputs/coverage_pilot'))
    args = parser.parse_args()
    if not math.isfinite(args.step_s) or args.step_s <= 0:
        parser.error('--step-s must be finite and positive')
    if not math.isfinite(args.tolerance_s) or args.tolerance_s < 0:
        parser.error('--tolerance-s must be finite and nonnegative')
    try:
        configs = configurations(args.count, args.seed)
    except ValueError as exc:
        parser.error(str(exc))
    # Never silently overwrite a previous dataset or its provenance.
    if args.output.exists() and any(args.output.iterdir()):
        parser.error('output directory must be empty; choose a new --output')
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = dict(schema_version=1, status='generating',
                    created_at=datetime.now(timezone.utc).isoformat(),
                    design='pilot_grid' if args.count is None else 'uniform_random',
                    seed=args.seed, configurations=configs, provenance=provenance(),
                    fixed=dict(window_s=WINDOW_S, altitude_km=500, inclination_deg=53,
                               first_raan_deg=0, first_initial_angle_deg=0,
                               longitude_deg=30.52, minimum_deg=10, earth_angle_deg=0,
                               epoch='synthetic; continuous, no daily resets'),
                    step_s=args.step_s, fine_step_s=args.step_s / 2,
                    tolerance_s=args.tolerance_s, label_resolution='fine_step_s',
                    units=dict(angles='degrees', access_fraction='dimensionless', longest_gap_s='seconds'),
                    limitation='Agreement between resolutions does not prove grazing-pass completeness.')
    manifest_path = args.output / 'manifest.json'
    def save_manifest():
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    save_manifest()
    dataset_path = args.output / 'dataset.csv'
    checked = 0
    try:
        with dataset_path.open('w', newline='') as stream:
            writer = None
            for index, config in enumerate(configs, 1):
                row = evaluate(config, args.step_s, args.tolerance_s)
                if writer is None:
                    writer = csv.DictWriter(stream, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row)
                stream.flush()
                checked += row['quality_status'] == 'checked'
                print(f"{index}/{len(configs)}: {row['quality_status']}", flush=True)
    except BaseException as exc:
        manifest.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        save_manifest()
        raise
    manifest.update(status='complete' if checked == len(configs) else 'needs_review',
                    checked_count=checked, unresolved_count=len(configs) - checked,
                    dataset_sha256=hashlib.sha256(dataset_path.read_bytes()).hexdigest())
    save_manifest()
    print(f"Saved {len(configs)} configurations to {dataset_path}; {checked} checked.")


if __name__ == '__main__':
    main()
