# DECISIONS

Append-only, newest first. **Log the WHY, not just the what.** This file is
rebuttal ammunition — in December, "switched to masked patches" is useless;
"switched because full blackout made the signal trivially separable and inflated
AUROC" is exactly what a judge probes for.

Format: `## YYYY-MM-DD — <decision>` then **What**, **Why**, and **Consequences**
if it changes downstream work.

---

> **2026-07-28 — no entry.** A compute-stack decision was drafted this session
> and removed before commit: SageMaker was written up as "locked" for Phases 0–1
> when nothing had actually been chosen. What the session produced was a *fact*
> (SageMaker `ml.g5.2xlarge` quota raises from 0 to 1 instantly and self-service,
> where EC2's G-family quotas need a support case and days) — not a choice. Facts go in
> `SETUP.md` and `LOG.md`. **This is the second time in ten days the compute stack
> has been falsely written up as decided** (see the 2026-07-27 LOG entry). The
> stack remains open until the EC2 quota outcome is known; it is tracked as an
> open question in `STATUS.md`.

## 2026-07-27 — Repo is the single source of truth; Drive copies retired

**What.** All project context lives in `context/` in this repo. The Google Drive
copies of the plan, literature review, STATUS, and cost/schema doc become stale
snapshots and should be deleted or explicitly labeled read-only.

**Why.** Two copies today becomes three stale copies by November. Drive also
flattened the markdown when it converted to Google Docs, and Drive's write path
proved unreliable (four failed `create_file` calls on 2026-07-26). Git gives
version history for free, which answers "why did the Phase-1 signal change in
October," not just "that it did."

**Consequences.** Project-knowledge uploads, if used at all, are exports from
this repo at phase gates — never edited in place.

## 2026-07-26 — Logging schema locked as a superset with a `[live]`/`[derived]` split

**What.** Three tables (per-episode, per-step, per-detection-event), every field
tagged `[live]` (written during rollout) or `[derived]` (computed offline).
Backend is append-only JSONL/CSV as source of truth, not W&B. Full spec in
`SPEC.md`.

**Why.** The rollout is one-shot and frozen by January; the analysis is
infinitely re-runnable. Any field not logged is unrecoverable without re-running
the grid, which by January is impossible. So the schema must be a superset of
every cost model we might iterate toward. Raw rows are a superset; aggregates
throw away information future-you needs.

**Consequences.** The headline flip depends only on `[live]` fields, so the
genuinely hard problem (defining "recoverable" and "irreversible failure") cannot
sink it. `intermediate_state_ref` must be logged from day one or the Phase-4
recoverability stretch dies silently.

## 2026-07-26 — Cost model *structure* locked; values left to iterate

**What.** Locked: 2×2 outcome model per episode, FN ≫ FP, single swept ratio
C = cost(FN)/cost(FP) over 1×–1000× log-spaced, static per-decision base
analysis, computed from raw per-event rows. Reserved for Phase 3: exact sweep
bounds, latency-weighting, whether TP carries a replan cost, the defended ratio.

**Why.** Two reasons, both about the schema rather than the cost model itself.
(1) The schema must be a superset of every reachable cost model, and you can't
size a superset without fixing the structure. (2) Committing the evaluation lens
*before* knowing which detector wins is what makes the eventual ranking flip
credible rather than retrofitted. The retrofitting failure isn't "you changed the
ratio" — it's "you reverse-engineered the evaluation to produce a flip."

**Consequences.** A late detection is a TP under the static model but a partial
cost under latency-weighting, so **never log a fixed TP/FP/FN/TN label** — log
raw timings and derive the label in post-processing.

## 2026-07-18 — Asymmetric-cost evaluation promoted to HEADLINE; adaptive horizon demoted to mechanism

**What.** N4 (asymmetric cost) is the finding; M1 (adaptive horizon) is the
system that produces it. Figure 4 became Figure 1. The talk and board are
restructured around the cost result.

**Why.** The literature review found the adaptive-horizon space is crowded —
DVAC, DEHP, HiPolicy, MoH, AutoHorizon, SGAC, VLA-Corrector, all 2025–26. Leading
with the mechanism invites the one question that can't be won. Cost-asymmetry is
the only lens no modern generative-policy detector paper uses.

**Consequences.** The original "M1 gates *when to think* — a control axis nobody
occupies" claim is false and removed everywhere. See the verbatim replacement in
`CLAUDE.md`.

## 2026-07-18 — Control signal switched from K-sample dispersion to inter-chunk consistency

**What.** Primary control signal is inter-chunk consistency (STAC/TIDE-style:
compare the newly generated chunk against the previously committed one over their
temporal overlap), conformal-calibrated. K-sample dispersion is retained **for
the live PushT demo meter only.**

**Why.** K-sampling costs ~8× the denoising passes, which directly cannibalizes
the compute-savings headline — the arithmetic of the guaranteed floor gets much
tighter if measuring confidence costs 8 passes per check. AutoHorizon already ran
this exact signal as a baseline (4 chunks per observation, MC variance) and
reported it hyperparameter-sensitive and latency-heavy.

**Consequences.** Clean role split: cheap signal drives control, intuitive signal
drives the story. "I asked the robot to plan eight times and it gave eight
different answers" explains itself to a judge in one sentence; "the clean-action
estimate jittered across the final denoising steps" does not. On one PushT
episode the K-sampling cost is irrelevant.

## 2026-07-18 — Added two Phase-2 controls: budget-matched blind trigger and random-trigger placebo

**What.** Conditions (d) budget-matched blind (adaptive's mean replan count, even
fixed schedule, signal ignored) and (e) random-trigger placebo (same count,
uniformly random timing). Run Wk 15 on the headline configuration only.

**Why.** Without them, "adaptive beat fixed-long" is answerable with "you just
replanned more," and the three-condition grid cannot separate *replanned at good
moments* from *replanned more*. Both controls hold budget fixed and vary only
placement, so beating both leaves exactly one explanation: the signal identifies
moments where replanning matters. AEGIS methodology — it reported 10.1% recovery
against 4.6% budget-matched blind and 5.1% random placebo, and the controls are
what make that number mean something.

**Consequences.** ~30 extra cells, under 20% added rollouts. Cannot run before
Wk 15 (you must know adaptive's budget to match it), so hooks are written Wk 11.
**Earmark the compute now** — the failure mode is reaching January having spent
the budget on extra seeds. Also protective: if adaptive ties the controls, that's
a real finding ("frequency matters more than timing") and a far better talk than
an unexplained null.

## 2026-07-18 — Assistive framing committed

**What.** The assistive angle is committed, not optional.

**Why.** N4 (the asymmetric-cost evaluation) *is* the assistive framing — the
cost asymmetry only means something if a missed failure hurts someone. Committing
locks the cost model and the task set.

**Consequences.** Honest scoping: LIBERO does not ship tasks named "handover" or
"retrieve-dropped," and it ships no disturbance injector. The assistive framing
lives in the narration and the cost model, not in a claim that the benchmark
shipped it that way. Keep that distinction clean and no judge can knock it down.

## 2026-07-17 — Tasks and disturbances locked

**What.** Tasks: object handover, retrieve-dropped-object, container/drawer
opening. Disturbances: object shift (headline + demo), occlusion, delayed
observation. Object-swap dropped.

**Why.** Not the count — the *spread*. The three tasks span distinct failure
mechanisms (free-body grasp, precision approach, articulated contact) and the
three disturbances span distinct sources (world-state, perception, timing). Three
flavors of the same thing would prove nothing about generality. Object-swap was
dropped because it changes *what the task is*, making failures ambiguous between
"disturbance" and "wrong goal."

**Consequences.** Magnitude sweep on object-shift only; occlusion and delayed-obs
run at a single representative level. One deep sweep plus two confirmatory points
is the efficient shape — full sweeps on all three is the compute trap. Rejected
alternatives: pouring (sim-fidelity sensitive), button press (motion too small for
meaningful mid-chunk disturbance), long-horizon (failure attribution too noisy).
