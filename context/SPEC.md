# SPEC — Cost Model & Logging Schema

Locked 2026-07-26. Supersedes `PLAN.md` §6.

> **This is a contract, not a description.** Every rollout writes against it. The
> rollout is one-shot and frozen by January; the analysis is infinitely
> re-runnable. Any field not logged is unrecoverable without re-running the grid,
> which by January is impossible.

**Purpose:** fix the *structure* of the asymmetric-cost evaluation and the logging
schema now, so that (a) the schema is a superset of every cost model we might
iterate toward, and (b) the eventual ranking flip is credible — the evaluation
lens was committed before the winning detector was known, not retrofitted.

| Locked now (structure) | Iterates through Phase 3 (values) |
|---|---|
| Cost is a swept FN:FP ratio | The exact sweep bounds |
| Costs computed from raw per-event rows | Whether to latency-weight |
| FN ≫ FP is the asymmetry | Whether TP carries a replan cost |
| The 2×2 outcome model | The specific defended ratio |

---

## Part 1 — Cost model

### Outcome model (per episode)

Unit = the episode. Disturbed = positive; nominal = negative. The detection
decision yields a 2×2:

| Outcome | Meaning | Cost |
|---|---|---|
| TP | correctly flagged a real failure | response cost (replan / pause) |
| FP | false alarm on a nominal rollout | unnecessary pause |
| FN | missed a real failure | the failure actually happening |
| TN | correctly stayed quiet | 0 (baseline) |

**Asymmetry: FN ≫ FP.** This is "prediction ≠ prevention" in numbers.

### Base parameterization — LOCKED

Single swept ratio **C = cost(FN) / cost(FP)**, bounds **1× – 1000×,
log-spaced**. C=1 recovers the symmetric regime; the flip, if it exists, occurs
at some order of magnitude rather than some linear value — hence log spacing.
Base analysis: **static per-decision expected cost.**

One scalar, one axis, one flip curve. Maximally legible to a non-specialist judge
in five seconds at a poster.

### Extension — RESERVED (decide in Phase 3, from logged data)

**Latency-weighted cost.** The cost of a missed or late detection scales with
*how late* it was. Detecting one step before irreversible failure costs nearly as
much as never detecting; early detection is cheap because it's recoverable. Uses
`detection_latency` + `time_to_failure_at_detection`. This is where the deep
result probably lives.

### Second-order variant — RESERVED

TP carries a replan cost (denoising passes / a visible pause to the user). Ties
the cost model to the compute-savings result, unifying the two halves of the
project. Uses `total_denoising_passes`.

### Classification subtlety — drives a schema rule

A **late detection is a TP under the static model but a partial cost under
latency-weighting.** Therefore: **do not log a fixed TP/FP/FN/TN label.** Log raw
`detection_step`, `onset_step`, and failure timing; **derive** the label in
post-processing. This keeps both models computable from the same rows. It is the
raw-not-aggregated principle in miniature.

### Defense of the range (memorize)

> "I don't know the exact ratio, and that's the point — I show which detector is
> safest across the whole plausible range."

Anchor in the assistive framing: FP = a harmless pause the user waits through;
FN = hot liquid on a lap, a dropped fragile object, an unsafe grasp. Plus one
classical assistive-robotics / medical-alarm cost-sensitive citation, where
10×–1000× asymmetries are standard. Arguing the ratio is *large and uncertain* is
a far stronger position than defending a single number.

### Headline protection

**The flip figure depends only on `[live]` fields.** Derived fields feed optional
extensions. The one genuinely hard measurement problem in the whole schema
(defining recoverability) therefore cannot sink the headline.

---

## Part 2 — Logging schema

**Principle: log RAW per-event rows, never aggregates.** If you log "detection
latency averaged 4.2 steps," you can never recompute a cost model that weights
individual latencies. If you log every event's latency as its own row, you can
compute *any* cost function over them, forever.

**Backend:** append-only JSONL/CSV as the source of truth — **not** W&B. The cost
post-processor needs recomputable raw rows, not a dashboard that already
summarized them. A dashboard on top is optional.

**Tags:** `[live]` = written during the rollout. `[derived]` = computed in an
offline labeling pass afterward.

### Table A — per-episode (one row per rollout)

| Field | Source | Notes |
|---|---|---|
| `episode_id` | `[live]` | primary key |
| `task_id` | `[live]` | |
| `seed` | `[live]` | |
| `condition` | `[live]` | ∈ {fixed-long, always-replan, adaptive, budget-blind, random-placebo} |
| `disturbance_type` | `[live]` | includes `none` — **nominal episodes MUST be logged**: they are the FP denominator and the conformal calibration set |
| `disturbance_magnitude` | `[live]` | null if nominal |
| `disturbance_onset_step` | `[live]` | null if nominal |
| `success_flag` | `[live]` | |
| `episode_length` | `[live]` | for normalization |
| `total_denoising_passes` | `[live]` | the compute-savings figure |
| `total_replans` | `[live]` | the budget the controls must match |
| `wallclock` | `[live]` | |
| `checkpoint_dir` | `[live]` | provenance |
| `git_commit` | `[live]` | provenance |
| `config_hash` | `[live]` | provenance — this is what makes a run reproducible in January |

### Table B — per-step (one row per timestep)

| Field | Source | Notes |
|---|---|---|
| `episode_id` | `[live]` | |
| `step_idx` | `[live]` | |
| `signal_value` | `[live]` | inter-chunk consistency — the control signal |
| `signal_value_demo` | `[live]` | K-sample dispersion, PushT only, nullable |
| `threshold_value` | `[live]` | conformal threshold in effect |
| `replan_fired_flag` | `[live]` | |
| `horizon_remaining` | `[live]` | |
| `denoising_passes_this_step` | `[live]` | |
| `intermediate_state_ref` | `[live]` | pointer to saved sim state — **the bridge to recoverability analysis** |

### Table C — per-detection-event (one row per disturbance — the headline's fuel)

| Field | Source | Notes |
|---|---|---|
| `episode_id` | `[live]` | |
| `disturbance_onset_step` | `[live]` | |
| `detection_step` | `[live]` | null if never detected |
| `detection_latency` | `[live]` | `detection_step − onset_step`; ∞/null if never |
| `ground_truth_failure_flag` | `[live]` | did the episode actually fail |
| `ground_truth_failure_step` | `[derived]` | when failure became **irreversible** — needs a definition |
| `recoverable_at_detection_flag` | `[derived]` | was it still recoverable when detected |
| `time_to_failure_at_detection` | `[derived]` | `ground_truth_failure_step − detection_step`; the latency-weighting input |

---

## Part 3 — Superset reachability check

| Analysis | Requires |
|---|---|
| Static base cost | only `[live]` detection fields (derive labels from `detection_step` + `ground_truth_failure_flag`) |
| Latency-weighted cost | `detection_latency` + `time_to_failure_at_detection` |
| TP-carries-replan-cost | `total_denoising_passes` |
| Recoverability (Phase 4) | `intermediate_state_ref` |

Every discussed cost model is reachable from these columns. **That is the entire
reason for locking the structure in Week 1.**

---

## Part 4 — Two named weaknesses

**1. The `[derived]` detection fields are a research task, not a log write.**
"Recoverable" and "irreversible failure" need non-trivial definitions —
recoverable by whom? by any policy or by yours? within how many steps? Do not let
their presence in the schema fool you into thinking they're cheap. Keep them
reachable-but-deferred via `intermediate_state_ref`: log the state pointer live
every step, label offline in Phase 4. **Without `intermediate_state_ref` from day
one, the recoverability stretch dies silently.**

**2. The base cost model needs none of the derived fields.** Feature, not bug —
the headline flip is computable from purely `[live]` data, so it survives even if
recoverability labeling is never done or turns out ill-defined.

---

## Instrument-from-day-one rule

The first real rollout — **including the checkpoint-eval smoke test** — emits
Table A rows. Two reasons: it dry-runs the logging code on throwaway data so bugs
surface now rather than on the real grid, and it guarantees no expensive rollout
ever produces un-analyzable output.

`PLAN.md` slots the schema into Week 3. The per-episode block should exist
earlier: **any Week 1–2 validation rollout run without logging is a rollout you
throw away.**
