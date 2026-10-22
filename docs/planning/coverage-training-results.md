# First coverage-model training run

Run date: 2026-10-22. This is an exploratory result, not an accuracy acceptance
or a claim of generalization beyond the fixed simulator settings.

## Data and model selection

Generated 1,000 configurations with seed 42, uniform RAAN and initial angle in
[0°, 360°), and uniform latitude in [-70°, 70°]. Both satellites remain at
500 km altitude and 53° inclination; longitude is 30.52° E, the elevation mask
is 10°, and the synthetic epoch advances continuously for seven days.

Five cases failed the initial 10 s / 5 s resolution comparison. All five passed
when repeated at 5 s / 2.5 s. The original dataset is preserved; refinement
history and hashes are saved in the checked dataset manifest. Resolution
agreement does not prove every grazing interval was detected.

The split is 700 training, 150 validation, and 150 test configurations. Models
use sine/cosine features for both angles and signed latitude. Validation MAE
selects each target independently from a mean predictor, standardized linear
regression, and two 200-tree random forests. No test-driven tuning or refitting
was performed. Access fraction selected minimum leaf size 3; longest gap
selected minimum leaf size 1. Predictions are raw, without clipping.

## Held-out test results

| Target | Mean baseline MAE | Selected model MAE | 95th-percentile error | Maximum error |
| --- | ---: | ---: | ---: | ---: |
| Access fraction | 1.092 percentage points | 0.0784 percentage points | 0.2674 percentage points | 1.0714 percentage points |
| Longest gap | 910.4 min | 31.0 min | 81.8 min | 157.6 min |

There were 143 positive-access and seven zero-access test configurations.
Positive-access MAE was 0.0815 percentage points and 31.2 minutes, respectively.
Neither selected model produced out-of-bounds predictions on the test set.

A serious failure appeared in validation: RAAN 150.3698°, initial angle
41.4624°, latitude -67.0801° had no simulated access and a 168-hour gap, but
its predicted gap was only 79.4746 hours, an 88.5254-hour error. This is near
the geometric reach boundary. The large miss shows why the smaller test-set
maximum is not a guarantee. Investigate boundary sampling and an explicit
geometry-based reach check in a future experiment; do not reuse this test set
as an untouched benchmark after using these results to redesign the model.

## Runtime and scope

On this machine, median warm prediction for both targets, including features,
was 6.44 ms versus 269.25 ms for fine-resolution simulator computation on the
same ten test configurations: about 41.8× faster. Model loading took 30 ms;
a batch of 150 predictions took 9.19 ms. Dataset generation and refinement
used about 415 s of simulation time. Including training and loading, the rough
single-query break-even estimate is 1,583 queries. Timings are local measurements,
not portable performance guarantees; no simulator caching was used.

The models approximate the fixed synthetic geometry. Latitude-band holdout,
other epochs or orbit settings, and application-specific error thresholds
have not been evaluated. Continue simulator verification of candidate designs.

## Reproduction and artifacts

Use the commands in the repository README. The following artifacts from this
training run are committed explicitly; other generated outputs remain ignored:

- `outputs/coverage_random_42/`: original dataset and manifest.
- `outputs/coverage_random_42_checked/`: refined dataset and manifest.
- `outputs/coverage_model_42/models.joblib`: the two selected trained regressors.
- `outputs/coverage_model_42/report.json`: split IDs, validation/test scores,
  subgroup errors, software versions, provenance, and timings.
- `outputs/coverage_model_42/test_predictions.csv`: per-configuration test predictions.
- `outputs/coverage_model_42/predictions.png`: predicted-versus-simulated values.

These saved models were smoke-tested through the prediction command. The complete
26-test suite covers simulation behavior, generation, refinement, periodic
features, split separation, error units, and input integrity.

The saved model environment is recorded in
`outputs/coverage_model_42/requirements.txt`. Install those versions and then
install this repository with `python -m pip install -e . --no-deps` to recreate
the environment. Platform-specific wheel availability can vary. The original
manifests retain the Git revision and source hashes recorded during generation;
their dirty-worktree status reflects that the run preceded this commit.
