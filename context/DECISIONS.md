# DECISIONS

Append-only, newest first. **Log the WHY, not just the what.** This file is
rebuttal ammunition — in December, "switched to masked patches" is useless;
"switched because full blackout made the signal trivially separable and inflated
AUROC" is exactly what a judge probes for.

Format: `## YYYY-MM-DD — <decision>` then **What**, **Why**, and **Consequences**
if it changes downstream work.

---

## 2026-07-31 — AWS EC2 `g5.2xlarge` is the Phase 0/1 compute platform; credits before cash

**What.** The compute stack, open since the project began, is now partly closed.
Phase 0 and Phase 1 run on **EC2 `g5.2xlarge` in `us-east-1`** on AWS account
`051388699393`, funded by its $200 of credit. RunPod and Vast are **not** rejected
— they are held in reserve for the Phase-2 grid. Kaggle and Colab are out.
SageMaker is not chosen; EC2 quota was won, which removes the reason SageMaker was
attractive (instant self-service grant to 1 instance).

**Why.** Two EC2 G-family quota appeals were approved on 2026-07-30, giving 8 vCPU
on-demand and 8 vCPU Spot — one `g5.2xlarge` either way, which is exactly what
single-GPU LIBERO reproduction needs. That removed the blocker.

The provider choice then turns on a distinction earlier analysis missed. On raw
price AWS loses badly: `LOG.md` 2026-07-28 priced $200 at ~130 GPU-hr on AWS
versus ~570 on a RunPod 4090, roughly 4×. But that comparison treats both as the
same kind of money and they are not. **The AWS $200 is credit; RunPod is cash, and
the payment methods on this project belong to other people.** Free credit at a bad
rate beats cheap cash that requires asking someone. The correct sequencing is
therefore to exhaust credits first and treat cash as the reserve, which is the
reverse of what $/GPU-hr alone would suggest.

Worth recording that this reverses a recommendation made three times earlier in
the same session — "provision RunPod today, don't wait on AWS." That advice was
correct *while blocked*, and stopped being correct the moment the quota landed. It
was conditioned on a premise that expired.

**Consequences.**

- **One account does not fund the project.** ~130 GPU-hr of credit against
  `PLAN.md` §10's 350–650 GPU-hr estimate covers Phase 0 and probably Phase 1, not
  the Phase-2 grid. Accounts two and three ($600 max) are now a *planned* step
  rather than a contingency, and the quota appeal is a known ~2-day procedure —
  budget that time per account instead of assuming instant access.
- **Every new account repeats the quota fight.** Procedure and the argument that
  actually worked are in `SETUP.md` § Quotas. Do not open an account expecting
  same-day GPU.
- **Budgets alarms are now a hard gate, not hygiene.** One `g5.2xlarge` left
  running drains the credit in under six days, and the credit is now the binding
  constraint on the whole phase.
- The `n_envs`-on-GPU question resolves against A10G 24 GB specifically, not
  against whatever a 4090 would have done. If Phase 2 later moves to RunPod, that
  measurement does not transfer.
- `PLAN.md` §10's "no provider has been chosen" caveat is **no longer accurate**
  for Phases 0–1 and must be updated at the Week-4 phase gate.

## 2026-07-29 — Diffusion Policy is vendored into this repo, not pinned by hash

**What.** `external/diffusion_policy/` is committed to this repo in full — 369
files, 31 MB, upstream commit `5ba07ac6661db573af695b419a7947ecb704690f`, MIT
licensed, **unmodified**. This reverses SETUP.md's original "pinned clones,
gitignored" policy. Submodules remain rejected. `.gitignore` now ignores
`external/*` and un-ignores vendored repos **one line at a time**.

**Why.** A recorded commit hash is only a *reference*, and a reference dies if
upstream is deleted or force-pushed. Experiments run to January 2027 and the fair
is March 2027, so the code has to survive independently of anyone else's
repository. The alternative considered and rejected was forking DP to a personal
GitHub account — equivalent insurance with a cleaner repo, but it leaves
reproduction dependent on two repos staying in sync.

**Consequences.**

- The repo is now **369 vendored files against 22 of my own**. The boundary must
  therefore be stated explicitly whenever the repo is shown: everything under
  `external/` is verifiably upstream at a known commit, everything I wrote is in
  `src/`. Expect "which part did you write?" from a judge and answer it in one
  sentence.
- **Never edit the vendored tree.** Wrap or subclass from `src/` instead — which
  is what `eval_pusht.py` already does. An edit inside `external/` is invisible in
  review, unattributable, and voids the unmodified-upstream guarantee.
- The nested `.git` had to be deleted before staging. Leaving it would have made
  git record a **gitlink (mode 160000)** — an accidental submodule that renders as
  an unclickable folder on GitHub and clones as an *empty* directory. Verified
  absent. **Any future vendoring must repeat this check.**
- The per-repo opt-in in `.gitignore` is load-bearing, not stylistic: **LIBERO
  ships ~100 GB of demonstration data**, and a blanket un-ignore of `external/`
  would attempt to commit it. If LIBERO is vendored later, vendor the code only.

## 2026-07-29 — `success_flag` on PushT is `max_reward >= 1.0`, and the continuous score is logged alongside it

**What.** PushT's env reward is `clip(coverage / 0.95, 0, 1)`; success is defined
as coverage ≥ 95%, i.e. `max_reward >= 1.0`. `max_reward` is additionally logged
as its own float field in Table A.

**Why.** `SPEC.md` requires `success_flag` but PushT hands you a continuous
coverage score, so a threshold had to be chosen and written down before it could
be chosen conveniently later. Logging the float as well is the raw-not-aggregated
principle: freeze the boolean at rollout time and every alternative threshold
becomes unrecoverable without re-running the grid.

**Consequences.** The first 50-episode run shows why this matters. Mean score
0.9453 and success rate 30/50 = 60% describe the *same* episodes, and the
distribution is bimodal — 30 at exactly 1.0, **17 in [0.9, 1.0)**, nothing in
[0.5, 0.9). With a third of episodes within ten points of a cutoff **inherited
from IBC rather than chosen**, a disturbance that shifts coverage slightly could
swing the success rate ~20 points while barely moving mean score. Since
`success_flag` is the binary feeding the asymmetric cost model, a
**success-threshold sensitivity sweep is now owed in Phase 3**, run alongside the
cost-ratio sweep. "Why 0.95?" cannot be answered with "it came with the
environment." Compounding it: 20/50 episodes hit the 300-step truncation, so
episode length is censored and the binary carries more weight than it appears to.

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
