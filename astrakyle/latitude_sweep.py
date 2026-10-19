"""Compare four station latitudes and four RAAN configurations over seven days."""
import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from .raan_sweep import RAAN_VALUES
from .two_satellites import run

LATITUDES = (0, 30, 50.45, 70)
WINDOW_S = 7 * 86400


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step-s', type=float, default=10)
    parser.add_argument('--output', type=Path, default=Path('outputs/latitude_sweep'))
    args = parser.parse_args()
    rows, details = [], []
    for latitude in LATITUDES:
        for raan in RAAN_VALUES:
            try:
                orbits, station, samples, merged, metrics = run(args.step_s, raan, WINDOW_S, latitude)
                fine = run(args.step_s / 2, raan, WINDOW_S, latitude)
            except ValueError as exc:
                parser.error(str(exc))
            combined, refined = metrics['combined'], fine[4]['combined']
            rows.append(dict(latitude_deg=latitude, second_raan_deg=raan,
                interval_count=len(merged), access_fraction=combined['access_fraction'],
                access_percent=combined['access_percent'], longest_gap_s=combined['longest_gap_s'],
                beginning_gap_s=combined['beginning_gap_s'], ending_gap_s=combined['ending_gap_s'],
                fine_interval_count=refined['interval_count'],
                access_difference_s=abs(combined['total_access_s'] - refined['total_access_s']),
                longest_gap_difference_s=abs(combined['longest_gap_s'] - refined['longest_gap_s'])))
            details.append(dict(latitude_deg=latitude, second_raan_deg=raan,
                orbits=[asdict(o) for o in orbits], station=asdict(station),
                metrics=metrics, fine_metrics=fine[4], merged_intervals_s=merged,
                passes=[[asdict(p) for p in sample[2]] for sample in samples]))
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / 'comparison.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / 'results.json').write_text(json.dumps(dict(window_s=WINDOW_S,
        minimum_deg=10, earth_angle_deg=0, epoch='original synthetic epoch; no daily resets',
        step_s=args.step_s, fine_step_s=args.step_s / 2, configurations=details), indent=2) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout='constrained')
    for ax, key, scale, title in [(axes[0], 'access_percent', 1, 'Union access (% of seven days)'),
                                 (axes[1], 'longest_gap_s', 1 / 3600, 'Longest gap (hours)')]:
        values = np.array([row[key] * scale for row in rows]).reshape(4, 4)
        ax.imshow(values, cmap='Blues', vmin=0)
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f'{values[i,j]:.3f}', ha='center', va='center',
                        color='white' if values[i,j] > values.max() * 0.6 else '#172b3a')
        ax.set(xticks=range(4), xticklabels=[f'{r}°' for r in RAAN_VALUES],
               yticks=range(4), yticklabels=[f'{lat}°' for lat in LATITUDES],
               xlabel='Satellite 2 RAAN', ylabel='Station latitude', title=title)
    fig.suptitle('Latitude comparison • longitude fixed at 30.52° E\n500 km altitude • 53° inclination • elevation ≥ 10° • continuous seven-day window')
    fig.savefig(args.output / 'comparison.png', dpi=160)
    plt.close(fig)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
