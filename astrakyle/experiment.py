"""Run with python -m astrakyle.experiment; outputs use elapsed simulation time."""
import argparse
import csv
import json
from dataclasses import asdict
from math import isfinite
from pathlib import Path

from .geometry import CircularOrbit, GroundStation, elevation_deg
from .passes import simulate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default, help_text in [
        ('altitude-km', 500, 'Circular orbit altitude in km'),
        ('inclination-deg', 53, 'Inclination in degrees'),
        ('raan-deg', 0, 'RAAN in degrees'),
        ('initial-angle-deg', 0, 'Initial argument of latitude in degrees'),
        ('latitude-deg', 50.45, 'Station spherical latitude in degrees'),
        ('longitude-deg', 30.52, 'Station east-positive longitude in degrees'),
        ('earth-angle-deg', 0, 'Earth rotation angle at the synthetic epoch'),
        ('hours', 24, 'Simulation duration in hours'),
        ('step-s', 10, 'Sample spacing in seconds; shorter passes may be missed'),
        ('minimum-deg', 10, 'Minimum elevation in degrees, from 0 to 90'),
    ]:
        parser.add_argument('--' + name, type=float, default=default, help=help_text)
    parser.add_argument('--output', type=Path, default=Path('outputs/single_station'))
    args = parser.parse_args()
    try:
        if not isfinite(args.earth_angle_deg):
            raise ValueError('Earth angle must be finite')
        orbit = CircularOrbit(args.altitude_km, args.inclination_deg, args.raan_deg, args.initial_angle_deg)
        station = GroundStation(args.latitude_deg, args.longitude_deg)
        elevation = lambda t: elevation_deg(orbit, station, t, args.earth_angle_deg)
        times, values, passes = simulate(elevation, args.hours * 3600, args.step_s, args.minimum_deg)
    except ValueError as exc:
        parser.error(str(exc))

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / 'elevation.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['elapsed_s', 'elevation_deg', 'above_minimum'])
        writer.writerows((t, e, e >= args.minimum_deg) for t, e in zip(times, values))
    rows = [dict(asdict(p), duration_s=p.duration_s) for p in passes]
    with (args.output / 'passes.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['start_s', 'end_s', 'peak_time_s', 'peak_elevation_deg',
                                             'clipped_start', 'clipped_end', 'duration_s'])
        writer.writeheader()
        writer.writerows(rows)
    config = {k: v for k, v in vars(args).items() if k != 'output'}
    config['model'] = 'Circular two-body orbit; rotating spherical Earth; synthetic epoch; surface station'
    (args.output / 'config.json').write_text(json.dumps(config, indent=2) + '\n')

    fig, ax = plt.subplots(figsize=(12, 5), layout='constrained')
    ax.plot([t / 3600 for t in times], values, color='#247ba0', linewidth=1.2)
    ax.axhline(0, color='#555555', linewidth=0.7)
    ax.axhline(args.minimum_deg, color='#dc7135', linestyle='--', label=f'Minimum elevation: {args.minimum_deg:g}°')
    for number, p in enumerate(passes):
        ax.axvspan(p.start_s / 3600, p.end_s / 3600, color='#2a9d8f', alpha=0.22,
                   label='Access interval' if number == 0 else None)
        ax.plot(p.peak_time_s / 3600, p.peak_elevation_deg, '.', color='#176c60')
    ax.set(xlabel='Elapsed simulation time (hours)', ylabel='Elevation (degrees)',
           xlim=(0, args.hours), ylim=(-90, 90),
           title=f'Synthetic satellite • {args.altitude_km:g} km, {args.inclination_deg:g}° inclination\n'
                 f'Station: {args.latitude_deg:g}° latitude, {args.longitude_deg:g}° longitude • {len(passes)} access intervals')
    ax.grid(alpha=0.2)
    ax.legend(loc='lower right')
    fig.savefig(args.output / 'elevation.png', dpi=160)
    plt.close(fig)
    print(f'Orbital period: {orbit.period_s / 60:.2f} min; {len(passes)} access intervals')
    print(' Start (h)   End (h)   Duration (min)   Peak (deg)   Window clipped')
    for p in passes:
        clipped = ', '.join(label for flag, label in [(p.clipped_start, 'start'), (p.clipped_end, 'end')] if flag) or 'no'
        print(f'{p.start_s / 3600:10.4f} {p.end_s / 3600:9.4f} {p.duration_s / 60:16.2f} {p.peak_elevation_deg:12.2f}   {clipped}')
    print(f'Outputs: {args.output.resolve()}')
    print('Detection is sampled; reduce --step-s to check for short or grazing passes.')


if __name__ == '__main__':
    main()
