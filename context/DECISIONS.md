# DECISIONS

Append-only, newest first. **Log the WHY, not just the what.** This file is
rebuttal ammunition — in December, "switched to masked patches" is useless;
"switched because full blackout made the signal trivially separable and inflated
AUROC" is exactly what a judge probes for.

Format: `## YYYY-MM-DD — <decision>` then **What**, **Why**, and **Consequences**
if it changes downstream work.

---

## 2026-08-04 — Keep torch 2.4.1+cu121 on LIBERO; do not install the README's 1.11.0+cu113

**What.** The LIBERO conda env runs **torch 2.4.1+cu121**. LIBERO's README
instructs `pip install torch==1.11.0+cu113` after `requirements.txt`; that step
was **deliberately skipped**. `requirements.txt` does not pin torch, so pip
resolved 2.4.1 as a `robomimic` dependency, and the resulting stack was tested
and works.

**Why.**

1. **It was verified before it was accepted.** The done-when test
   (`SETUP.md` § Step 5) built a `libero_object` env, reset, rendered both
   128×128 cameras with mean pixel 138.5, stepped a 7-dim action, and returned a
   110-float sim state. Nothing was assumed.
2. **Speed is a budget question, not a preference.** torch 1.11 predates
   meaningful Ampere optimisation. The A10G is sm_86 and the credit buys ~130
   GPU-hr *estimated*; a slower stack converts directly into fewer rollouts.
3. **Downgrading is cheap and reversible** — one pip command, ~3 minutes — so
   testing forward first strictly dominates reverting blind.
4. The system CUDA (13.2) is irrelevant either way: pip's torch wheels bundle
   their own CUDA runtime, so only the **driver** (595.71.05) has to be new
   enough, and it is by a wide margin.

**Consequences.**

- **Our numbers are not bit-comparable to any published LIBERO result**, which
  used the pinned stack. This costs nothing for the Phase-0 gate — that compares
  a *success rate* against 92.5%, not trajectories — but it means an exact
  trajectory-level reproduction is not available as a debugging tool.
- **If the gate misses its ±5 band, the torch version is a suspect** and
  reverting to `1.11.0+cu113` is the first diagnostic to run, before concluding
  anything about the policy or the env.
- The env is pinned by *record*, not by lockfile. `SETUP.md` § Step 5 lists the
  exact resolved versions; if this env breaks in November, suspect an unpinned
  transitive dependency drifting — the same failure mode that hit `robodiff`'s
  `huggingface_hub` in July.

## 2026-08-02 — LIBERO platform is the `libero_object` suite, per-suite training, one run

**What.** The three LIBERO tasks come from **`libero_object`**, trained as a
**single per-suite policy** (~500 demos, all 10 tasks), one training run. The
three tasks are **not yet named** — they get picked from the *measured* per-task
success rates the gate run produces, not chosen in advance. The Phase-0 gate is
rewritten to: **`libero_object` suite average within ±5 points of the published
92.5%**, band declared before looking.

This supersedes `PLAN.md` §0 row 1, which named handover, retrieve-dropped-object,
and drawer/container. **Two of those three tasks do not exist in LIBERO.**

**Why.** Four reasons, in descending weight.

1. **Budget.** ~130 GPU-hr of credit (*estimated*, unmeasured) against `PLAN.md`
   §10's 350–650, with the Phase-2 grid — the load-bearing risk — drawing on the
   same pool. One training run is affordable. Two is a bet on an unmeasured
   number. This is the strongest argument and it outranks the others.
2. **No goal ambiguity.** DP has no language conditioning. `libero_object`'s 10
   tasks have **different object sets per task**, so the image identifies the
   task. `libero_goal`'s 10 tasks share one scene and one object set
   `{bowl, cream cheese, wine bottle, plate}` and differ only in goal predicate —
   verified by diffing `(:objects` blocks. **This is the published ranking, not a
   coincidence:** Object 92.5 > Spatial 78.3 (two identical bowls) > Goal 68.3.
   It matters here specifically because the control signal is **inter-chunk
   consistency**: in a goal-ambiguous scene the policy is legitimately multimodal
   with no disturbance present, which inflates nominal inconsistency, inflates the
   conformal threshold calibrated on nominal rollouts, and makes disturbance
   indistinguishable from the policy never having known which task it was doing.
   The headline would have rested on a signal partly measuring task ambiguity.
3. **Headroom.** 92.5% nominal means a disturbance dropping success to 60% is
   unmistakable. At Goal's 68.3% the same effect is noise. The experiment needs
   room to fall.
4. **Reproduction is bug insurance.** It is the only apples-to-apples comparison
   available, and its real value is not judges — it is catching a misconfigured
   env *before* it is baked into a Phase-2 grid that cannot be re-run after
   January. Precedent: the PushT checkpoint-config provenance trap
   (`SETUP.md` § Step 2), where the published YAML and the in-checkpoint config
   disagreed on the eval seed.

**Rejected alternatives, with the reason:**

- **Custom cross-suite 3-task policy** (~150 demos, one run). Verified viable and
  *correct*: `libero_object` is `LIBERO_Floor_Manipulation` (fixture `floor`)
  while Spatial and Goal are `LIBERO_Tabletop_Manipulation` with different
  fixtures and object sets, so three hand-picked tasks would be visually
  disambiguable with no confound and real skill diversity. **Rejected on budget
  and scope, not correctness** — it has no published number by construction, so it
  buys the diversity story at the cost of the bug insurance, and adding it as a
  *second* run is scope the schedule can't absorb.
- **`libero_10` (Long).** Best diversity — 8 distinct scenes, two-step tasks. DP
  reaches only 50.5%, so there is no headroom to attribute a failure to the
  injected disturbance rather than to the policy being bad.
- **Per-task policies** (~50 demos each). No ambiguity anywhere, but ~50 demos is
  likely data-starved and there is no published comparison.

**Consequences.**

- **The "three diverse tasks" claim is retired.** All three tasks are one template
  (pick up ⟨grocery⟩ → basket). Say this before a judge does. **The generality
  axis is PushT vs. LIBERO, not LIBERO task variety** — 2D planar pushing with
  keypoint obs and a 2-dim action space versus 7-DoF manipulation from 128×128
  RGB, two independently trained policies. If the ranking flip holds on both, that
  is stronger than three groceries and a drawer.
- **Per-task success rates are a free by-product**, not a separate cost. The gate
  run writes 500 Table A rows tagged by task; grouping by task in post-processing
  yields all 10 rates at zero extra compute. This is why the three tasks are
  picked *after* the run.
- **A second suite stays possible but is not planned.** Its real cost is not
  training — it is re-running everything downstream: the injector must work in a
  new scene type, and conformal calibration is per-policy so the Object threshold
  does not transfer. Revisit only after Phase 1, with a measured GPU-hr figure.
- `PLAN.md` §0 row 1 and §7's Phase-0 gate row are now stale and updated.

## 2026-08-02 — The disturbance injector gets built; LIBERO-Plus / LIBERO-Pro cannot be adopted

**What.** Neither LIBERO-Plus ([2510.13626](https://arxiv.org/abs/2510.13626)) nor
LIBERO-PRO ([2510.03827](https://arxiv.org/abs/2510.03827)) is adopted as the
perturbation harness. `src/disturbances/` is built from scratch, on top of
LIBERO's own `set_state()` / `regenerate_obs_from_state()`.

**Why.** **Both perturb only at episode initialization.** LIBERO-Plus's seven axes
(object layout, camera viewpoint, robot init state, language, lighting, background
texture, sensor noise) and LIBERO-PRO's four are all applied at scene setup,
before the rollout begins. Neither injects anything *during* execution, which is
this project's entire premise. Their question is "does the policy still succeed
from a perturbed start"; ours is "does the policy notice a mid-execution
disturbance in time to change what it commits to." Different experiments.

Also confirmed: neither implements **occlusion** or **delayed observation**.
LIBERO-Plus's camera / lighting / texture / sensor-noise axes are appearance
perturbations, not occlusion of the target object.

**Consequences.**

- **`PLAN.md` §3 Wk 5's ~2-week Phase-1 compression does not happen.** The plan
  branched on this audit; this is the branch where the injector is worth building.
  Budget Phase 1 at full size. Combined with Phase 0 becoming a training task,
  this is ~2–3 weeks of unplanned scope against 2 weeks of Phase-4 buffer.
- **Partial reuse, not zero.** LIBERO-Plus O2 "Target Object Pose" perturbs target
  (x,y,z)+(pitch,yaw,roll) via the Problem class — reusable displacement code,
  repointed at mid-episode via `regenerate_obs_from_state()`. O1 (adding
  distractor objects by editing BDDL) is not needed.
- **A sharper prior-work rebuttal, with 2025 citations** — added to `PLAN.md` §9:
  *"The LIBERO robustness benchmarks perturb the initial condition and ask whether
  the policy still succeeds. I perturb during execution and ask whether it notices
  in time to change what it commits to."* This is a better distinction than the
  one the plan had, and it came free from the audit.
- **`intermediate_state_ref` is unblocked.** `ControlEnv.get_sim_state()` returns
  the flattened MuJoCo state — exactly the snapshot the deferred Phase-4 decision
  specified, at ~KB/step rather than rendered frames.

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
