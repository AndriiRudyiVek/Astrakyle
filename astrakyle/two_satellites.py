"""Compare the default experiment with two satellites separated by 180 degrees."""
import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from .access import access_metrics, merge_intervals
from .geometry import CircularOrbit, GroundStation, elevation_deg
from .passes import simulate


def run(step_s=10.0, second_raan_deg=0.0, window_s=86400.0, latitude_deg=50.45):
    """Propagate continuously from the original synthetic epoch to window_s."""
    station = GroundStation(latitude_deg=latitude_deg)
    orbits = [CircularOrbit(), CircularOrbit(initial_angle_deg=180, raan_deg=second_raan_deg)]
    results = [simulate(lambda t, orbit=orbit: elevation_deg(orbit, station, t),
                        duration_s=window_s, step_s=step_s, minimum_deg=10) for orbit in orbits]
    individual = [[(p.start_s, p.end_s) for p in result[2]] for result in results]
    merged = merge_intervals(individual[0] + individual[1])
    metrics = {
        'satellite_1': access_metrics(individual[0], window_s),
        'satellite_2': access_metrics(individual[1], window_s),
        'combined': access_metrics(merged, window_s),
    }
    return orbits, station, results, merged, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step-s', type=float, default=10)
    parser.add_argument('--output', type=Path, default=Path('outputs/two_satellites'))
    args = parser.parse_args()
    try:
        orbits, station, results, merged, metrics = run(args.step_s)
    except ValueError as exc:
        parser.error(str(exc))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    args.output.mkdir(parents=True, exist_ok=True)
    config = dict(orbits=[asdict(o) for o in orbits], station=asdict(station),
                  minimum_deg=10, window_s=86400, step_s=args.step_s, earth_angle_deg=0,
                  model='Circular orbits; rotating spherical Earth; synthetic epoch; surface station')
    (args.output / 'config.json').write_text(json.dumps(config, indent=2) + '\n')
    (args.output / 'access_metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    with (args.output / 'passes.csv').open('w', newline='') as f:
        fields = ['satellite', 'start_s', 'end_s', 'duration_s', 'peak_time_s',
                  'peak_elevation_deg', 'clipped_start', 'clipped_end']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for number, result in enumerate(results, 1):
            writer.writerows(dict(satellite=number, **asdict(p), duration_s=p.duration_s) for p in result[2])
    with (args.output / 'merged_access.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['start_s', 'end_s', 'duration_s', 'clipped_start', 'clipped_end'])
        writer.writerows((start, end, end - start, start == 0, end == 86400) for start, end in merged)
    with (args.output / 'elevation.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['elapsed_s', 'satellite_1_deg', 'satellite_2_deg', 'at_least_one_above_minimum'])
        writer.writerows((t, a, b, max(a, b) >= 10)
                         for t, a, b in zip(results[0][0], results[0][1], results[1][1]))

    fig, (ax, timeline) = plt.subplots(2, 1, figsize=(13, 7), sharex=True,
                                      gridspec_kw={'height_ratios': [4, 1]}, layout='constrained')
    for number, ((times, values, _), color) in enumerate(zip(results, ['#247ba0', '#a457a5']), 1):
        ax.plot([t / 3600 for t in times], values, label=f'Satellite {number}', color=color, linewidth=1)
    ax.axhline(10, color='#dc7135', linestyle='--', label='10° minimum')
    ax.axhline(0, color='#777777', linewidth=0.6)
    for start, end in merged:
        ax.axvspan(start / 3600, end / 3600, color='#2a9d8f', alpha=0.15)
    ax.set(ylabel='Elevation (degrees)', ylim=(-90, 90),
           title='Two satellites in one orbital plane • 180° separation\n500 km altitude • 53° inclination • Kyiv station')
    ax.legend(loc='lower center', ncol=3)
    ax.grid(alpha=0.2)
    for row, intervals, color in [(2, [(p.start_s, p.end_s) for p in results[0][2]], '#247ba0'),
                                  (1, [(p.start_s, p.end_s) for p in results[1][2]], '#a457a5'),
                                  (0, merged, '#2a9d8f')]:
        timeline.broken_barh([(start / 3600, (end - start) / 3600) for start, end in intervals],
                            (row - 0.3, 0.6), facecolors=color)
    timeline.set(yticks=[0, 1, 2], yticklabels=['Combined', 'Satellite 2', 'Satellite 1'],
                 xlabel='Elapsed simulation time (hours)', xlim=(0, 24), xticks=range(0, 25, 2))
    timeline.grid(axis='x', alpha=0.2)
    fig.savefig(args.output / 'elevation.png', dpi=160)
    plt.close(fig)
    print(json.dumps(metrics, indent=2))
    print(f'Outputs: {args.output.resolve()}')


if __name__ == '__main__':
    main()
