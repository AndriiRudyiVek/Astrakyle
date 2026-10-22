# First ML project: predicting constellation access metrics

Status: dataset generation implemented, 2026-10-22. The configurable phase and
resolution-checked pilot/random generator are available. Baseline regression training, random-split evaluation, prediction, and runtime
comparison are implemented. Latitude-band holdout and application-specific
acceptance thresholds remain future work. The repository README describes
current capabilities.

## Question and scope

Can a supervised regression model approximate Astrakyle's seven-day geometric
access calculations accurately enough to make repeated configuration evaluation
faster? This connects orbital geometry studies with practical ML: generating
labels, choosing features, separating evaluation data, analyzing errors, and
measuring runtime.

| Part | Specification |
| --- | --- |
| Variable inputs | Satellite 2 RAAN, satellite 2 initial orbital angle, station latitude |
| Orbits | Two circular satellites, each at 500 km altitude and 53° inclination |
| Satellite 1 | RAAN 0°, initial orbital angle 0° |
| Station | Surface station, longitude 30.52° E |
| Clock | Existing synthetic epoch, initial Earth angle 0°, continuous 604,800 s window |
| Access rule | At least one satellite has elevation ≥ 10° |
| Targets | Union access fraction in [0, 1]; longest gap in seconds in [0, 604,800] |
| Label source | Current simulator, with sampling-resolution checks |

“Coverage” here means geometric access at one station. It does not measure
global coverage, bandwidth, communications reliability, or demand satisfaction.
Labels are simulator outputs, not observations of real satellites.

## Reuse the existing simulator

`astrakyle.two_satellites.run` already accepts satellite 2 RAAN, window length,
and station latitude. It now exposes satellite 2's initial orbital angle through
`second_initial_angle_deg`, defaulting to 180° while preserving positional calls. Reuse `CircularOrbit`, pass detection, interval union,
and `access_metrics`; do not implement a separate label calculation.

Access fraction is merged access duration divided by the full window.
Longest gap is the largest interval in the complement of that union, including
window boundaries. Never restart daily or join the beginning and ending gaps.
Zero access produces fraction 0 and one 604,800 s gap.

This experiment needs no external datasets, new orbit provider abstraction,
reinforcement learning environment, or radio-link model. The broader
[dataset interface proposal](dataset-interfaces.md) remains a later-stage plan.

## Stage 1: a small, checked dataset

Start with a pilot grid: RAAN and initial angle each in {0°, 90°, 180°, 270°},
and latitude in {0°, 30°, 50.45°, 70°}, giving 64 configurations. Use it to
check generation, units, zero-access cases, and runtime, not to claim model
generalization. Include existing RAAN/latitude experiment configurations as
separate regression checks.

Run the pilot at 10 s and 5 s sampling. Record interval counts, absolute total
access differences, and longest-gap differences. Investigate disagreements at
finer resolution before accepting labels; bisection accuracy alone does not
guarantee that sample-based detection finds every grazing interval. Choose and
record label tolerances before scaling up, below the desired prediction error.

For a first training dataset, propose 1,000 seeded configurations sampled
uniformly in each angle over [0°, 360°) and latitude over [-70°, 70°].
Uniform latitude is an experimental design, not an area-weighted Earth sample.
Confirm the runtime budget using the pilot before generating this dataset.
Keep targeted cases near the access boundary and angle wraparound in a separate
diagnostic set; do not silently mix them into uniform-distribution scores.

Store one row per configuration with a stable ID, the three inputs, both
targets, sampling settings, resolution-check results, and label quality status.
Keep a manifest containing fixed settings, units, seed, configuration list,
simulator revision and any local modifications, generation time, and dataset hash.
Keep generated data under ignored `outputs/`; commit generation recipes.
Represent failed or unresolved calculations explicitly, never as zero access.

## Stage 2: learn and compare

Assign unique configurations to fixed 70% training, 15% validation, and 15%
test splits before fitting. Keep equivalent angles and both sampling resolutions
of a configuration in the same split; fine-resolution calculations are checks,
not additional independent examples.

Encode each variable angle as sine and cosine after converting to radians.
Combine those four features with station latitude. Fit any scaling only on
training data. Start with a training-mean predictor for each target, then linear
regression and a modest tree-based regressor. Select settings on validation
data and evaluate the untouched test set once the comparison is fixed.
Separate regressors for the two targets are a simple starting point.

Report access-fraction MAE in percentage points and longest-gap MAE in minutes,
plus 95th-percentile and maximum absolute errors. Compare each target against
its own baseline. Avoid percentage-relative errors near zero. Report errors
separately for zero-access and positive-access cases and by latitude band so
easy unreachable stations cannot hide poor predictions where access occurs.
Show predicted-versus-calculated plots and inspect the worst configurations.

Use a separate experiment withholding complete latitude bands to assess
generalization to unsampled latitude ranges. Label this result separately from
random-split interpolation. Do not claim validity beyond the declared domain or
under changes to altitude, inclination, longitude, epoch, or observation window.

Check predictions for physical bounds. If clipping is used, declare it and
report how frequently it changes predictions alongside raw prediction errors.
Do not assume a regressor will learn exact zero access.

## Stage 3: measure practical value

Benchmark the existing simulator and model on the same configurations and
hardware. Exclude plotting and file export from simulator compute timing.
Include feature construction in prediction timing; report model-loading cost,
single-configuration latency, and batch throughput separately.

Report dataset generation and training costs as well as prediction speed.
If simulation time per configuration is S and prediction time is P, a rough
break-even query count is upfront generation/training cost divided by (S - P),
when S > P. State caching and repeated-run conditions.

Before final testing, choose acceptable errors for each target based on the
intended use. A useful outcome requires both acceptable held-out errors and
measured runtime improvement; a weak model is still informative if its failures
are explained. Any candidate configuration selected using the model must be
rechecked with the simulator.

## Learning sequence and first deliverable

1. Connect RAAN, orbital phase, latitude, and merged access to existing aerospace
   studies; predict qualitative trends before generating labels.
2. Expose satellite 2's initial angle and generate the checked pilot dataset.
3. Learn feature encoding, regression, splits, and baseline comparisons using
   the larger reproducible dataset.
4. Analyze errors and runtime, then write a short experiment report.

The first implementation deliverable is the parameter extension plus a
reproducible, resolution-checked dataset generator. Verify that the default
180° case preserves existing results and that nondefault angles reach the
underlying orbit calculation. Training follows once labels pass the checks.
