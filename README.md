![A satellite drifts above Earth’s curved horizon and becomes transparent to reveal active neural connections, in GitHub’s dark-theme color palette](docs/figures/astrakyle-neural-satellite.gif)

Astrakyle is a learning and research project exploring adaptive satellite communications constellations at the intersection of aerospace engineering and AI.

The planned simulation starts with circular low Earth orbits, a rotating spherical Earth, and ground locations with synthetic communication demand. Initial work will focus on satellite visibility and elevation angles, followed by satellite selection and allocation of limited communication capacity. Later stages will explore classical optimization and AI methods, including reinforcement learning, to adapt service to satellite failures, new satellites, and regional demand changes.

The first executable experiment tracks a single synthetic satellite over one ground station and identifies geometric access intervals. Its primary goal is to build a deep understanding of orbital mechanics, coverage, and resource allocation through incremental implementation. This README will evolve as development progresses.

## Single-satellite experiment

Requires Python 3.10 or newer. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m astrakyle.experiment
```

The default experiment uses a **500 km circular orbit**, **53° inclination**, a surface station at **50.45° N, 30.52° E** (approximately Kyiv), and a **10° minimum elevation**. It samples **24 hours at 10-second intervals**. RAAN, initial orbital angle, and initial Earth rotation angle are zero. The epoch is synthetic: the ECI and ECEF axes coincide at elapsed time zero. Outputs are not real-world satellite predictions.

Open `outputs/single_station/elevation.png` to see elevation versus elapsed hours. The dashed line is the minimum elevation; green bands mark access intervals; dots mark their maximum elevations. Negative elevation places the satellite below the local horizon.

The same directory contains:

- `elevation.csv`: elapsed seconds, elevation in degrees, and whether the minimum is met.
- `passes.csv`: access start/end, duration, peak time/elevation, and flags for intervals clipped by the observation window. All times and durations are seconds.
- `config.json`: the parameters used to reproduce the run.

Try a stricter elevation requirement, or a finer sampling interval:

```sh
python -m astrakyle.experiment --minimum-deg 20 --output outputs/minimum_20
python -m astrakyle.experiment --step-s 1 --output outputs/fine
python -m astrakyle.experiment --help
```

Latitude, longitude, altitude, inclination, RAAN, initial orbital angle, Earth angle, and duration are also configurable. Generated outputs and the virtual environment are excluded from Git.

### Calculation and accuracy

The experiment computes satellite ECI position analytically, rotates it into ECEF, subtracts the station position, and projects the relative vector into local East–North–Up coordinates. Elevation is `atan2(up, horizontal distance)`. An access interval satisfies **elevation ≥ minimum elevation**.

Sampling detects intervals; bisection refines their threshold crossings to within 1 millisecond of the numerical model, and a local search refines their peaks. Intervals entirely between samples can be missed, especially near grazing contact or with a high elevation mask. Reduce `--step-s` and compare results before relying on completeness. Numerical refinement does not imply physical prediction accuracy. Peaks and durations for clipped intervals describe only the observed window.

This model ignores eccentricity, orbital perturbations, terrain, atmospheric refraction, antenna limits, and radio-link performance. Geometric access alone does not establish a usable communications link.

Run the geometry and pass-detection checks:

```sh
python -m unittest discover -s tests -v
```

## Two satellites in the same plane

Run the second experiment with the same physical inputs and 24-hour window:

```sh
python -m astrakyle.two_satellites
python -m astrakyle.two_satellites --step-s 5 --output outputs/two_satellites_fine
```

Satellite 1 starts at orbital angle 0° and satellite 2 at 180°. Both have altitude 500 km, inclination 53°, and RAAN 0°. The station, initial Earth angle, and 10° elevation minimum are unchanged. Equal angular speeds preserve their 180° separation.

Access means **at least one satellite meets the elevation minimum**. Each satellite's refined intervals are sorted and overlapping or touching intervals are merged before computing metrics. The complement of this union gives the gaps within the window; beginning and ending gaps are kept separate, without assuming daily repetition.

Outputs in `outputs/two_satellites/` include individual passes (`passes.csv`), the union (`merged_access.csv`), both elevation series (`elevation.csv`), a comparison plot (`elevation.png`), parameters (`config.json`), and single-satellite versus combined metrics (`access_metrics.json`). Clipping flags indicate partial intervals at either boundary.

For the default run, satellite 1 has six passes and satellite 2 has five. There are no overlaps, giving eleven combined intervals:

| Metric | Satellite 1 alone | Combined |
| --- | ---: | ---: |
| Total access | 2,347.57 s | 4,466.86 s |
| Access fraction | 2.7171% | 5.1700% |
| Longest gap within 24 h | 61,174.36 s | 58,292.44 s |

The combined beginning gap is 756.86 s and the ending gap is 248.02 s. A second satellite improves access during the available part of the day, but the shared orbital plane still leaves a long gap. Tests compare 10-second and 5-second sampling, verify opposite satellite position vectors, check overlapping-interval union, and confirm that access plus gaps equals the window length. The same sampled-detection limitations apply.

## Exploratory RAAN comparison

```sh
python -m astrakyle.raan_sweep
```

Only satellite 2's RAAN changes: 0°, 60°, 120°, and 180°. Satellite 1 remains at RAAN 0° and initial angle 0°. Satellite 2 retains its initial angle of 180°. Both retain the 500 km altitude and 53° inclination; the station, synthetic epoch, 10° elevation minimum, and 24-hour window are unchanged.

The experiment merges access intervals before measuring the union and includes beginning and ending gaps separately. It automatically repeats each configuration with half the sampling interval. Outputs in `outputs/raan_sweep/` are `comparison.csv`, detailed `results.json` (including individual passes, merged intervals, gaps, parameters, and both resolutions), and `access_timeline.png`.

| Satellite 2 RAAN | Union access fraction | Longest gap |
| --- | ---: | ---: |
| 0° | 5.1700% | 16.1923 h |
| 60° | 5.1552% | 13.0519 h |
| 120° | 5.1850% | 8.3082 h |
| 180° | 5.1306% | 5.1700 h |

For this station and window, rotating the second plane distributes access more evenly by the longest-gap measure, with little change in total access. The 180° case has the shortest longest gap among these four exploratory configurations; the 120° case has the highest access fraction. This is not an optimization or a claim of daily repetition. Counts, refined total access, and longest gaps agree between 10-second and 5-second sampling. As before, sample-based detection cannot rule out every grazing interval.

See [Orbital-plane diversity and RAAN](docs/research/004-orbital-plane-diversity-and-raan.md) for the distinction between plane orientation and orbital phase.

## Knowledge base

The [project knowledge base](docs/README.md) provides standalone technical articles with definitions, equations, worked examples, and references.

- [Satellite service conditions: visibility and elevation](docs/research/001-satellite-service-conditions.md) — explains illustrated geometry, service requirements, and access intervals.
- [Reference frames and Earth’s rotation](docs/research/002-reference-frames-and-earth-rotation.md) — ECI/ECEF transformations, local ENU coordinates, and antenna-pointing angles.
- [Circular orbital motion](docs/research/003-circular-orbital-motion.md) — orbital speed and period, plane orientation, and satellite ECI position over time.
