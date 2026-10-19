# Dataset interfaces and final evaluation plan

Status: proposed design, saved 2026-10-19. No interfaces below are implemented by
this document. The README remains authoritative for executable capabilities.

## Purpose

Develop Astrakyle incrementally from synthetic orbital visibility experiments
into a reproducible platform for adaptive LEO communications resource allocation.
The candidate final research question is whether adaptive selection and allocation
reduce unmet demand and interruptions under unfamiliar geography, weather, demand
changes, and failures. A reusable benchmark with strong baselines is a potential
research contribution; dataset size alone does not establish significance.

## Architecture boundary

Separate acquisition from simulation:

`source files -> source adapters -> validated canonical records -> scenario -> simulation -> evaluation`

Download and preprocess explicitly, outside simulation steps. Runs use pinned
local inputs and need no live network connection. Preserve original source files
and provenance; adapters handle source formats, units, missingness, and quality.
Simulation and policy code consume canonical records, not provider-specific fields.
Begin with small Python records/functions; introduce protocols only when multiple
implementations need them. The signatures below describe behavior, not a frozen API.

## Shared conventions

- Keep geometry in km, seconds, and degrees, consistent with current code.
  Express communication rates in bit/s, delays in seconds, and power/attenuation
  in explicitly named units such as W and dB. Never infer units from values.
- A scenario declares a synthetic or UTC-anchored clock. Keep elapsed simulation
  seconds separate from timezone-aware UTC timestamps. Synthetic experiments must
  not acquire an invented real epoch. Declare handling of time scales and leap
  seconds when introducing real orbit propagation.
- Each position declares its frame and Earth model. Synthetic ECEF and real ITRF
  positions must not be silently mixed. Real locations use WGS84 geodetic latitude,
  longitude, and ellipsoidal height, with explicit conversion to Cartesian positions.
- Use stable string IDs for satellites, cells, terminals, and gateways; retain
  source identifiers. Never use record order as identity.
- Intervals use `[start, end)` for aggregation; geometric threshold crossings
  retain the current elevation >= minimum rule. State sampling and aggregation.
- Missing measurements are not zero capacity or zero demand. Return explicit
  missing/invalid status and quality flags; declare interpolation, maximum gap,
  and out-of-range policy. No silent extrapolation.
- Tag values as observed, estimated, or synthetic. Record source, spatial support,
  temporal support, and when information would have become available to a policy.

## Proposed interfaces

### 1. OrbitProvider

`states(satellite_ids, times, frame) -> OrbitState records`

Each record includes satellite ID, time, position_km, frame, Earth model,
source element epoch where applicable, quality/status, and optional velocity_km_s.
Return invalid propagation results explicitly.

First implementation: wrap `CircularOrbit` and the existing synthetic rotation
without changing numerical behavior. Later: CelesTrak GP/OMM or TLE records with
SGP4 and a validated TEME-to-terrestrial transformation. Do not feed SGP4 TEME
coordinates through the existing idealized ECI rotation. Scenario configuration
declares element selection and maximum permitted element age. Causal experiments
cannot select elements published after the decision time; retrospective geometry
reconstruction must be labelled separately.

### 2. DemandProvider

`demand(cell_ids, interval) -> DemandRecord records`

Records include cell ID, interval, offered_rate_bps, traffic class, provenance,
and optional active user count. Define rate as an interval average; offered bits
equal rate times duration. Queue evolution belongs to the simulator.

Start with uniform and hotspot generators with fixed seeds. Later aggregate
WorldPop population to a declared grid and apply explicit adoption, per-user load,
and local-time activity assumptions. Population counts must be conserved during
aggregation. Optional Ookla inputs inform scenario priorities; they do not directly
become demand. Priority weighting is a declared experiment choice.

### 3. EnvironmentProvider

`conditions(locations, interval, available_at) -> EnvironmentRecord records`

Records include location/cell, time support, precipitation with explicit units and
accumulation interval, optional temperature/humidity, quality, and provenance.
Start with constant clear-sky conditions. Later support WetLinks local weather and
ERA5 regional fields. Explicitly document resampling and accumulation-to-rate
conversion. Hourly weather cannot imply observed second-scale rain fluctuations.
Reanalysis can drive retrospective scenario truth; it must not masquerade as a
forecast available to an online policy.

### 4. LinkModel and resource constraints

`evaluate(geometry, environment, terminal, satellite, radio_config) -> LinkEstimate`

Return geometric visibility, link feasibility, modeled maximum rate, propagation
delay, optional attenuation/link margin, and a reason for infeasibility. Begin
with an explicitly synthetic fixed-capacity model behind the elevation mask.
Later introduce a documented radio budget and appropriate propagation methods.

Keep per-link achievable rates separate from shared satellite/beam/gateway limits.
The allocator enforces shared budgets; it must not assign full satellite capacity
independently to every visible terminal. Distinguish propagation delay from measured
end-to-end RTT, which also includes queues, routing, and terrestrial segments.

### 5. MeasurementStore

`query(site_ids, interval, metrics) -> MeasurementRecord records`

Normalize LENS and WetLinks observations to site, timestamp/interval, metric,
value, unit, measurement method, endpoint/direction, and quality metadata. Metrics
can include RTT, throughput, packet loss, and dish telemetry where available.
Retain geography and aggregation support; do not invent serving-satellite IDs.

Use traces for calibration and held-out validation of service distributions and
temporal behavior. Replaying an observed trace under another policy does not
establish that policy's counterfactual performance: actions need an interactive
model. Fit model parameters using training data only.

### 6. Scenario and policy boundary

`build(manifest) -> Scenario`
`act(observation, resource_limits) -> AllocationAction`
`step(action) -> next observation, outcomes`

A scenario binds the clock, locations, orbit/demand/environment providers, radio
and shared-resource configuration, event schedule, seed, and evaluation split.
An action identifies satellite-terminal assignments and allocated rates. Validate
visibility, nonnegative rates, per-link limits, and shared budgets; log invalid
actions rather than silently repairing them unless repair is an explicit policy.

Events identify target, type, start/end, and parameters: satellite loss/addition,
capacity reduction, gateway outage, or demand surge. Synthetic failures must be
labelled synthetic. Specify event order, handover cost, queue/drop rules, and
whether offered traffic persists between steps. Expose only information available
at decision time; keep hidden failures and future demand in environment state.

### 7. Evaluator

`evaluate(outcomes, scenario_manifest) -> MetricsReport`

Report offered/served/dropped bits, service fraction, per-cell/user fairness,
outage durations, handover count, recovery time after disruptions, and policy
runtime. Define service thresholds, percentile population, and clipping rules.
Preserve current access and gap metrics as geometry diagnostics. Include seeds,
run configuration, confidence intervals across independent runs, and input hashes.

## Reproducible dataset manifest

Each input reference records dataset ID/version, original URL or DOI, retrieval
time, covered dates/region, local artifact path and SHA-256, source schema, license
and attribution, redistribution status, preprocessing version/configuration,
quality filters, and known limitations. Preserve upstream revision metadata.

Each scenario manifest records schema version, provider/model versions, input
references, clock, units/frames, grid, time step, seeds, event schedule, policy
parameters, and train/validation/test assignment. Pin transformations as well as
raw files. Store large archives outside Git; commit small permitted fixtures and
retrieval recipes. Check each source's actual terms before redistributing data.

## Candidate sources and order

1. [CelesTrak GP](https://celestrak.org/NORAD/documentation/gp-data-formats.php):
   real geometry; no bandwidth, beam schedule, or service-state ground truth.
   Historical inputs must match experiment dates; bulk historical acquisition may
   require a different access route than current snapshots.
2. [WorldPop](https://hub.worldpop.org/): spatial demand proxy; select a documented
   population product/year and keep demand assumptions separate.
3. [LENS](https://github.com/clarkzjw/LENS): observed Starlink network behavior;
   select a manageable subset of sites and periods before large downloads.
4. [WetLinks](https://github.com/sys-uos/WetLinks): colocated weather and network
   observations; repository specifies CC BY-SA 4.0, subject to source details.
5. [Ookla Open Data](https://github.com/teamookla/ookla-open-data): optional
   connectivity context; quarterly aggregates and sampling bias limit inference.
6. [ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels):
   optional regional/seasonal weather scenarios after a link model exists.

[ITU-R P.618](https://www.itu.int/rec/R-REC-P.618-14-202308-I) is a propagation
modelling reference, not a training dataset. Source availability and terms should
be checked again at implementation time.

## Incremental delivery and acceptance

1. **Synthetic boundary:** wrap current orbit calculations when the next experiment
   needs interchangeable providers. Preserve existing default experiment outputs
   within existing tolerances. No broad refactor solely to match this proposal.
2. **Demand and capacity:** add deterministic synthetic demand, shared capacity,
   and highest-elevation/load-aware baselines. Check traffic conservation and
   budget enforcement, including zero-access cases.
3. **Real orbits and geography:** add a small dated orbital snapshot and population
   subset. Validate orbit/frame conversion against an independent trusted reference;
   check invalid/stale elements and population aggregation conservation.
4. **Measured calibration:** ingest small LENS/WetLinks fixtures, preserve units
   and missingness, and evaluate on untouched sites/time periods. Compare delay,
   throughput, and interruption statistics appropriate to the model's scope.
5. **Adaptive benchmark:** compare optimization and learning methods under the
   same observations, constraints, and compute reporting. Reserve whole regions
   and later periods, with separation appropriate to temporal dependence. Include
   multiple seeds and sensitivity to demand, capacity, and weather assumptions.

## Decisions deferred until their implementation stage

- Geographic grid and resolution; start regional before global experiments.
- Traffic classes, queue model, service threshold, and fairness objective.
- Radio band, beam/gateway representation, and handover cost assumptions.
- Orbit library, Earth-orientation inputs, and permitted element age.
- Dataset release versions, time overlap, licenses, and storage budget.
- RL algorithm/framework, only after classical baselines and a validated environment.

## Handoff to the main research conversation

Read this plan together with the README. Treat interface names and source choices
as proposals to reconcile with the research roadmap. Continue the incremental
learning sequence; do not start bulk data ingestion or implement all interfaces
merely because this planning document exists. Update this file as design decisions
are accepted or superseded, keeping implemented status distinct from plans.
