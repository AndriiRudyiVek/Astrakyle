"""Controlled exploratory RAAN sweep; all other parameters match two_satellites."""
import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from .two_satellites import run

RAAN_VALUES = (0, 60, 120, 180)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step-s', type=float, default=10)
    parser.add_argument('--output', type=Path, default=Path('outputs/raan_sweep'))
    args = parser.parse_args()
    try:
        runs = [(raan, run(args.step_s, raan)) for raan in RAAN_VALUES]
        fine = [(raan, run(args.step_s / 2, raan)) for raan in RAAN_VALUES]
    except ValueError as exc:
        parser.error(str(exc))
    args.output.mkdir(parents=True, exist_ok=True)
    rows, details = [], []
    for (raan, result), (_, refined) in zip(runs, fine):
        orbits, station, samples, merged, metrics = result
        combined = metrics['combined']
        finer = refined[4]['combined']
        row = dict(second_raan_deg=raan, interval_count=len(merged),
                   total_access_s=combined['total_access_s'],
                   access_fraction=combined['access_fraction'], access_percent=combined['access_percent'],
                   longest_gap_s=combined['longest_gap_s'],
                   beginning_gap_s=combined['beginning_gap_s'], ending_gap_s=combined['ending_gap_s'],
                   fine_interval_count=finer['interval_count'],
                   total_access_difference_s=abs(combined['total_access_s'] - finer['total_access_s']),
                   longest_gap_difference_s=abs(combined['longest_gap_s'] - finer['longest_gap_s']))
        rows.append(row)
        details.append(dict(second_raan_deg=raan, orbits=[asdict(o) for o in orbits],
                            station=asdict(station), metrics=metrics,
                            fine_metrics=refined[4],
                            merged_intervals_s=merged,
                            passes=[[asdict(p) for p in sample[2]] for sample in samples]))
    with (args.output / 'comparison.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / 'results.json').write_text(json.dumps(dict(
        window_s=86400, minimum_deg=10, earth_angle_deg=0, step_s=args.step_s,
        fine_step_s=args.step_s / 2, epoch='synthetic', configurations=details), indent=2) + '\n')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    fig, axes = plt.subplots(4, 1, figsize=(13, 8), sharex=True, layout='constrained')
    for ax, (raan, result) in zip(axes, runs):
        _, _, samples, merged, metrics = result
        for level, intervals, color in [(2, [(p.start_s, p.end_s) for p in samples[0][2]], '#247ba0'),
                                        (1, [(p.start_s, p.end_s) for p in samples[1][2]], '#a457a5'),
                                        (0, merged, '#2a9d8f')]:
            ax.broken_barh([(s / 3600, (e - s) / 3600) for s, e in intervals],
                          (level - 0.3, 0.6), facecolors=color)
        gap = max(metrics['combined']['gaps'], key=lambda g: g['duration_s'])
        ax.axvspan(gap['start_s'] / 3600, gap['end_s'] / 3600, color='#f6b756', alpha=0.18)
        ax.set(yticks=[0, 1, 2], yticklabels=['Union', 'Satellite 2', 'Satellite 1'],
               xlim=(0, 24), xticks=range(0, 25, 2),
               title=f"Satellite 2 RAAN = {raan}°   |   Access {metrics['combined']['access_percent']:.3f}%   |   Longest gap {gap['duration_s']/3600:.3f} h")
        ax.grid(axis='x', alpha=0.2)
    axes[0].legend(handles=[Patch(facecolor='#f6b756', alpha=0.3, label='Longest gap within window')],
                   loc='upper right', fontsize=8)
    axes[-1].set_xlabel('Elapsed simulation time (hours)')
    fig.suptitle('Orbital-plane diversity: only satellite 2 RAAN changes\n500 km • 53° inclination • initial angles 0° / 180° • Kyiv • elevation ≥ 10°')
    fig.savefig(args.output / 'access_timeline.png', dpi=160)
    plt.close(fig)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
