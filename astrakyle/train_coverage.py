"""Train and evaluate coverage surrogates on checked simulator labels."""
import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .coverage_dataset import WINDOW_S, provenance
from .two_satellites import run

INPUTS = ('second_raan_deg', 'second_initial_angle_deg', 'latitude_deg')
TARGETS = ('access_fraction', 'longest_gap_s')


def features(configs):
    """Periodic angular features and signed latitude; accepts N x 3 arrays."""
    x = np.asarray(configs, dtype=float)
    if x.ndim != 2 or x.shape[1] != 3 or not np.isfinite(x).all():
        raise ValueError('Expected finite N x 3 configurations')
    if np.any(np.abs(x[:, 2]) > 70):
        raise ValueError('Training domain is latitude [-70, 70] degrees')
    angles = np.deg2rad(x[:, :2] % 360)
    return np.column_stack((np.sin(angles), np.cos(angles), x[:, 2]))


def load_dataset(directory):
    data = (directory / 'dataset.csv').read_bytes()
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest.get('status') != 'complete':
        raise ValueError('Dataset must be complete with all labels checked')
    if hashlib.sha256(data).hexdigest() != manifest['dataset_sha256']:
        raise ValueError('Dataset hash does not match manifest')
    with (directory / 'dataset.csv').open() as f:
        rows = list(csv.DictReader(f))
    if len(rows) < 100 or any(r['quality_status'] != 'checked' for r in rows):
        raise ValueError('Need at least 100 checked configurations; pilot is diagnostic only')
    x = np.array([[float(r[k]) for k in INPUTS] for r in rows])
    y = np.array([[float(r[k]) for k in TARGETS] for r in rows])
    features(x)
    canonical = [(round(r % 360, 10), round(a % 360, 10), round(lat, 10)) for r, a, lat in x]
    if len(set(canonical)) != len(rows) or len({r['configuration_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate or equivalent configurations would leak between splits')
    if not np.isfinite(y).all() or np.any(y < 0) or np.any(y > [1, WINDOW_S]):
        raise ValueError('Invalid target values')
    expected = dict(window_s=WINDOW_S, altitude_km=500, inclination_deg=53,
                    first_raan_deg=0, first_initial_angle_deg=0,
                    longitude_deg=30.52, minimum_deg=10, earth_angle_deg=0)
    if any(manifest['fixed'].get(k) != v for k, v in expected.items()):
        raise ValueError('Dataset fixed settings do not match the coverage experiment')
    if len(rows) != len(manifest['configurations']):
        raise ValueError('Dataset row count does not match configuration manifest')
    if any(tuple(config[k] for k in INPUTS) != tuple(actual)
           for config, actual in zip(manifest['configurations'], x)):
        raise ValueError('Dataset inputs do not match configuration manifest')
    return rows, x, y, manifest


def split_indices(count, seed):
    indices = np.random.default_rng(seed).permutation(count)
    return np.split(indices, [int(.7 * count), int(.85 * count)])


def errors(truth, prediction, scale):
    if len(truth) == 0:
        return dict(count=0)
    e = np.abs(truth - prediction) * scale
    return dict(count=len(e), mae=float(e.mean()), p95=float(np.percentile(e, 95)),
                maximum=float(e.max()))


def train(directory, output, seed=42):
    rows, x, y, manifest = load_dataset(directory)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output directory must be empty')
    output.mkdir(parents=True, exist_ok=True)
    train_idx, val_idx, test_idx = split_indices(len(rows), seed)
    f = features(x)
    report = dict(dataset_sha256=manifest['dataset_sha256'], seed=seed,
                  provenance=provenance(), versions=dict(python=platform.python_version(),
                  numpy=np.__version__, sklearn=sklearn.__version__), hardware=platform.platform(),
                  selection='Lowest validation MAE per target; no refit after selection',
                  clipping='None; errors and physical-bound violations use raw predictions',
                  scope='Random-split interpolation only; latitude-band holdout not evaluated',
                  targets={}, splits={name: [rows[i]['configuration_id'] for i in idx]
                  for name, idx in [('train', train_idx), ('validation', val_idx), ('test', test_idx)]})
    models = {}
    predictions = []
    start = time.perf_counter()
    for column, target in enumerate(TARGETS):
        scale = 100 if column == 0 else 1 / 60
        candidates = {'mean': DummyRegressor(),
                      'linear': make_pipeline(StandardScaler(), LinearRegression()),
                      'forest_leaf1': RandomForestRegressor(n_estimators=200, min_samples_leaf=1,
                                                           random_state=seed, n_jobs=1),
                      'forest_leaf3': RandomForestRegressor(n_estimators=200, min_samples_leaf=3,
                                                           random_state=seed, n_jobs=1)}
        validation = {}
        for name, model in candidates.items():
            model.fit(f[train_idx], y[train_idx, column])
            validation[name] = errors(y[val_idx, column], model.predict(f[val_idx]), scale)
        selected = min(validation, key=lambda name: validation[name]['mae'])
        model = candidates[selected]
        models[target] = model
        pred = model.predict(f[test_idx])
        predictions.append(pred)
        truth = y[test_idx, column]
        groups = {'zero_access': y[test_idx, 0] == 0, 'positive_access': y[test_idx, 0] > 0}
        for lo, hi in [(-70, -30), (-30, 0), (0, 30), (30, 70)]:
            groups[f'latitude_{lo}_{hi}'] = ((x[test_idx, 2] >= lo) &
                (x[test_idx, 2] <= hi if hi == 70 else x[test_idx, 2] < hi))
        report['targets'][target] = dict(selected=selected, validation=validation,
            test=errors(truth, pred, scale), units='percentage_points' if column == 0 else 'minutes',
            mean_baseline_test=errors(truth, candidates['mean'].predict(f[test_idx]), scale),
            out_of_bounds_count=int(np.sum((pred < 0) | (pred > (1 if column == 0 else WINDOW_S)))),
            groups={name: errors(truth[mask], pred[mask], scale) for name, mask in groups.items()})
    report['training_wall_s'] = time.perf_counter() - start
    bundle = dict(models=models, fixed=manifest['fixed'], inputs=INPUTS, targets=TARGETS,
                  feature_order=['sin_raan', 'sin_angle', 'cos_raan', 'cos_angle', 'latitude'],
                  versions=report['versions'], dataset_sha256=manifest['dataset_sha256'])
    joblib.dump(bundle, output / 'models.joblib')
    start = time.perf_counter()
    joblib.load(output / 'models.joblib')
    load_s = time.perf_counter() - start
    def predict(configs):
        ff = features(configs)
        return np.column_stack([m.predict(ff) for m in models.values()])
    predict(x[test_idx[:1]])  # warm-up
    single_times, simulation_times = [], []
    # Same first ten held-out configurations, no plotting or export.
    for idx in test_idx[:10]:
        start = time.perf_counter()
        predict(x[idx:idx + 1])
        single_times.append(time.perf_counter() - start)
        start = time.perf_counter()
        run(step_s=float(rows[idx]['fine_step_s']), window_s=WINDOW_S, **dict(zip(INPUTS, x[idx])))
        simulation_times.append(time.perf_counter() - start)
    batch_times = []
    for _ in range(5):
        start = time.perf_counter()
        predict(x[test_idx])
        batch_times.append(time.perf_counter() - start)
    s, p = float(np.median(simulation_times)), float(np.median(single_times))
    generation_s = sum(float(r['simulation_wall_s']) for r in rows)
    report['timing'] = dict(model_load_s=load_s, benchmark_count=len(single_times),
        simulator_median_s=s, prediction_median_s=p, single_speedup=s / p,
        batch_size=len(test_idx), batch_median_s=float(np.median(batch_times)),
        generation_simulation_s=generation_s,
        break_even_queries=(generation_s + report['training_wall_s'] + load_s) / (s - p) if s > p else None,
        note='Warm inference includes features and both targets; simulator is uncached fine-resolution compute.')
    pred_matrix = np.column_stack(predictions)
    with (output / 'test_predictions.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['configuration_id', *INPUTS, *TARGETS, 'predicted_access_fraction', 'predicted_longest_gap_s'])
        for i, pred in zip(test_idx, pred_matrix):
            writer.writerow([rows[i]['configuration_id'], *x[i], *y[i], *pred])
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
    for j, ax in enumerate(axes):
        scale = 100 if j == 0 else 1 / 60
        truth, pred = y[test_idx, j] * scale, pred_matrix[:, j] * scale
        ax.scatter(truth, pred, s=12, alpha=.65)
        low, high = min(truth.min(), pred.min()), max(truth.max(), pred.max())
        ax.plot([low, high], [low, high], color='gray', linestyle='--')
        unit = 'access (%)' if j == 0 else 'longest gap (min)'
        ax.set(xlabel=f'Simulator {unit}', ylabel=f'Predicted {unit}', title=report['targets'][TARGETS[j]]['selected'])
    fig.savefig(output / 'predictions.png', dpi=150)
    plt.close(fig)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k in ('targets', 'timing')}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path('outputs/coverage_random_42'))
    parser.add_argument('--output', type=Path, default=Path('outputs/coverage_model_42'))
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    try:
        train(args.dataset, args.output, args.seed)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
