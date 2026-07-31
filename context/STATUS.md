# STATUS

Everything currently open. Loads into every Claude Code session via `CLAUDE.md`.

**The rule: this file holds every live loose end, and an item is deleted the
instant it closes** — not archived here. History lives in `LOG.md` and
`DECISIONS.md`, so deletion loses nothing. There is no length limit; the bounding
force is closure. Sections are ordered by how often they change, so a routine
session only rewrites the top.

_Last updated: 2026-07-31_

---

## Current position

**Phase 0 — Setup & Baseline. Week 3 of 28.**

> **Week 1 starts 2026-07-17 (a Friday); weeks run Fri–Thu.** The week number is
> *computed from this anchor*, never asserted from memory:
> `week = floor((today - 2026-07-17) / 7) + 1`. Cross-checks against `PLAN.md` §2:
> Week 4 = Aug 7–13 (the Phase-0 gate), Week 25 = Jan 1–7, Week 28 = Jan 22–28
> (experiment freeze). Recompute every session — a stale week number is the
> cheapest possible way to lose track of the January wall.

**Execution has started. The two-week planning-only streak is broken.** As of
2026-07-29 the rollout-and-logging pipeline runs end to end and the PushT
baseline reproduces: `test/mean_score` **0.9453** vs published **0.969** (n=50,
0.87 se, 95% CI contains the published value). 58 Table A rows exist, archived and
restore-tested. Diffusion Policy is now vendored into this repo.

**GPU access is live as of 2026-07-30.** Both EC2 quota requests were denied in 48
minutes and then **approved on appeal**: 8 vCPU on-demand (full ask) and 8 vCPU
Spot (of 16 asked). That is one `g5.2xlarge` either way in `us-east-1` on account
`051388699393` — exactly what single-GPU LIBERO work needs. **Nothing now blocks
LIBERO except doing it.**

**The Phase-0 gate is half met.** PushT is done. LIBERO is untouched and is now
the entire critical path.

**Next gate: Phase-0 gate, Week 4 (~Aug 13).**
Pass = DP reproduces published success rates on all three LIBERO tasks. Fail =
drop to 2 tasks → use released checkpoints → worst case PushT becomes the
quantitative platform and LIBERO becomes video-only.

## The single next concrete action

**Verify the 3 LIBERO task IDs exist with the right observation/action space, and
audit LIBERO-Plus / LIBERO-Pro for existing perturbation harnesses.** Budget 90
minutes for the audit — `PLAN.md` calls it the highest-leverage 90 minutes in the
schedule, and this session made that sharper: **PushT turned out to already ship
two of the three disturbances** (see Queued below), so the odds that LIBERO does
too are better than assumed. If either repo implements object shift or occlusion,
Phase 1 compresses by ~2 weeks and you inherit a standard others recognize.

Do this *before* downloading anything large — see the disk warning below.

## Blocked / at risk

- **LIBERO reproduction is now the whole critical path.** PushT no longer buys any
  information about it: different stack, different conda env, needs a GPU. If
  LIBERO checkpoints don't reproduce, everything downstream compresses against the
  Thanksgiving and January walls.
- **⚠ Budgets alarms are still not configured, and the AWS appeal text says they
  are.** Both submitted appeals assert *"I have Budgets alarms set on the credit
  balance"* as part of the risk argument that won the quota. They are not set.
  This is a **hard gate on launching any instance** — one `g5.2xlarge` left
  running drains $200 in under six days, and that credit is now the binding
  constraint on the whole phase. ~10 minutes to close. Alarm on credit *balance*,
  not just spend.
- **⚠ Disk: 31 GB free, and the LIBERO demo datasets total ~100 GB.** Do **not**
  run `download_libero_datasets.py` without `--datasets`. You need at most
  `libero_object` and `libero_goal` (est. ~15–20 GB, per-suite sizes unverified),
  and arguably only 3 individual task HDF5 files. **Demo data belongs on the GPU
  instance, not this laptop** — it is training data and training is cloud work.
  Locally you need only the LIBERO code and sim assets.
- **Credits do not cover the project.** ~130 GPU-hr (at the *estimated* ~$1.5/hr)
  against `PLAN.md` §10's 350–650 GPU-hr estimate. Funds Phase 0 and probably
  Phase 1, not the Phase-2 grid. Accounts 2 and 3 are now a planned step, and each
  repeats the ~2-day quota appeal — do not assume same-day GPU on a new account.
- **Schedule: Week 3 as of 2026-07-31, and Week 2's three LIBERO items are still
  unstarted.** They are no longer blocked on anything. The Phase-0 gate is Week 4
  (~Aug 13).

## Open decisions — mine to make

- **Compute stack — still entirely undecided. No provider chosen.** AWS
  (SageMaker or EC2), RunPod, Vast, Kaggle and Colab all remain live. Currently
  **1 account open** ($200, untouched); two more can be opened whenever needed, for
  a $600 maximum. **Resolving after the EC2 quota requests come back.** Phase 1
  will also supply a *measured* GPU-hr figure to replace the current estimate.
  Nothing in Phase 0's PushT work was blocked by this; **LIBERO is the first thing
  that actually needs a GPU, so this now gates real work.**
- **Tier-2 backup destination.** Must **not** be colocated with compute — the AWS
  accounts auto-close and would take their S3 buckets with them. Leading candidate
  is Google Drive. **Not yet urgent:** no `intermediate_state_ref` blobs exist, so
  nothing is currently at risk. **Must close before the first run that writes them.**
- **Competition venue — ScienceMontgomery vs. PG County.** PG County may be an
  easier ISEF path. Changes nothing about the project or schedule, but the two have
  different registration and abstract deadlines. Low urgency; ScienceMontgomery
  registration isn't open yet anyway.
- **No rebuttal drafted for VLA-Corrector (2607.01804).** The lit review calls it
  the nearest neighbor — detect-and-correct → event-triggered adaptive horizon, on
  VLAs. `PLAN.md` §9 has answers for DVAC/DEHP/AutoHorizon/Rewind-IL/AEGIS but not
  this one. Needs one before any mentor conversation. Pure reading and writing —
  good filler for a session where you don't want to fight dependencies.

## Waiting on the outside world

Things I don't control. Cheap to check, expensive to forget.

- **Two EC2 quota requests, filed 2026-07-28 in `us-east-1`, both PENDING.**
  `Running On-Demand G and VT instances` → 8 vCPU (`L-DB2E81BA`) and
  `All G and VT Spot Instance Requests` → 16 vCPU (`L-3819A6DF`). Expect 1–5
  business days; auto-denial within minutes is common and expected. **On denial,
  open a support case** — escalation path and justification wording in `SETUP.md`
  § Quotas.
- **ScienceMontgomery 2027 registration — not yet open** (checked 2026-07-28).
  Re-check periodically. The abstract/registration deadline remains the one hard
  external wall, and it lands weeks before the March fair.
- **PG County science fair deadlines** — unknown, not yet checked. Pairs with the
  venue decision above.

## Deferred by design

Parked deliberately, with the reason and when it comes back. Not forgotten.

- **Success-threshold sensitivity sweep.** PushT success is `coverage ≥ 0.95`,
  inherited from IBC, not chosen — and 17 of 50 episodes sit in [0.9, 1.0), just
  under it. Since `success_flag` feeds the cost model, the flip figure could be
  sensitive to a constant nobody defends. `max_reward` is logged as a float so
  every threshold stays recomputable. **Returns: Phase 3**, run alongside the
  cost-ratio sweep — same analysis shape, same figure logic. See `DECISIONS.md`.
- **Seeding the policy's sampling RNG.** DDPM sampling noise is currently unseeded,
  so repeat runs are not bit-identical. Fine for a 50-episode mean; not fine for
  debugging a single trajectory. **Returns: whenever a single-trajectory bug needs
  reproducing**, or Phase 2 if per-seed determinism is wanted in the grid.
- **`intermediate_state_ref` should point to a MuJoCo sim-state snapshot, not
  rendered frames.** ~KB/step (~1 GB per thousand episodes) vs. ~100× for frames.
  Recorded in `SETUP.md`; implement when the logger grows Table B. **Returns: Wk 7.**
- **Recoverability definitions.** `recoverable_at_detection_flag` and
  `ground_truth_failure_step` need real definitions of "recoverable" and
  "irreversible" — a research task, not a log write. **Returns: Phase 4.**
- **Cost model values.** Sweep bounds, latency-weighting, whether TP carries a
  replan cost. Structure is locked; values iterate against real detection-latency
  distributions. **Returns: Phase 3.**
- **Second detector signal** (chunk magnitude, ActProbe-style). Only if inter-chunk
  consistency separates weakly. Otherwise bank the time. **Returns: Week 9.**
- **Optimal `n_envs` on GPU.** Measured on CPU: small `n_envs` wins ~1.68× (25.5%
  straggler waste × 1.25× batch inefficiency). **This very likely reverses on GPU**,
  which is starved at batch 1. Measure, don't assume — and never infer throughput
  from CPU%. **Returns: first LIBERO GPU run.**
- **Sponsor outreach.** Pitch idea + preliminary result, not a cold ask. **A
  reproduced baseline now exists**, so this is unblocked. Target postdocs / senior
  PhD students. **Returns: Week 4+.**
- **Drive copies not yet retired.** Repo is the source of truth; delete or mark the
  Drive versions read-only before they drift. **Returns: whenever, but soon.**

## Standing commitments

Easy to skip, costly to skip.

- **Never edit `external/diffusion_policy/`.** It is vendored unmodified at
  `5ba07ac`. Wrap or subclass from `src/` instead. An edit there is invisible in
  review and voids the unmodified-upstream guarantee.
- **Wrap long local runs in `caffeinate -is`.** The machine slept mid-rollout on
  2026-07-29. Nothing is written until a run completes, so a sleep that becomes a
  shutdown loses everything.
- **Earmark compute for the Phase-2 controls now** (~30 cells). The failure mode is
  reaching January having spent the budget on extra seeds.
- **Re-verify the literature at each phase gate** (~20 min × 5). Several key papers
  post-date model training cutoffs and the adaptive-horizon space moves fast.
- **Instrument from day one.** Every rollout emits schema rows. Honored so far:
  both runs this session wrote Table A rows.
- **Back up raw rows before the next run starts**, gzipped to `logs/archive/` with
  a MANIFEST line. Done 2026-07-29 and restore-tested.
- **Budget alarms before launching any GPU instance.** Payment methods belong to
  other people; a forgotten instance drains $200 in under six days. Alarm on credit
  *balance*, not just spend.

## Checklists

**AWS — verification owed (all cheap, none blocking)**

- [ ] Check whether the SageMaker `ml.g5.2xlarge` cap can be raised **above 1**,
      and whether the instant self-service grant covers *training job* /
      *processing job* / *spot training job* usage types or only notebook/Studio.
      Query in `SETUP.md` § Quotas.
- [ ] Verify the true `ml.g5.2xlarge` $/hr off Cost Explorer once real hours exist.
      The ~$1.5/hr figure is an *estimate* and it is load-bearing.
- [ ] Configure Budgets alarms on credit balance, on every account before
      launching anything.

**Week 2 — due now**

- [ ] Verify the 3 LIBERO task IDs
- [ ] Audit LIBERO-Plus / LIBERO-Pro for existing perturbation harnesses (90 min)
- [ ] Reproduce DP on one LIBERO task; confirm success rate near published —
      **needs the compute decision first**
- [x] Install Diffusion Policy; PushT running on CPU end-to-end — `robodiff` env,
      procedure in `SETUP.md` § Step 1
- [x] Evaluate a released low-dim PushT checkpoint; emit Table A rows — run
      `20260729T005212Z`, `test/mean_score` 0.9453 vs published 0.969, 56 rows
- [x] Logging schema live (was queued for Wk 3; done early per
      instrument-from-day-one) — `src/logging/rows.py`, 58 rows in
      `logs/archive/table_a_20260729.jsonl.gz`
- [x] Backup + restore test — `logs/archive/MANIFEST.md`, verified byte-identical

**Queued**

- [ ] Wk 4: Phase-0 gate — verify DP on all 3 LIBERO tasks, snapshot reproducible
      baseline
- [ ] Wk 4: at the phase gate, re-check `PLAN.md` §10 — its "no provider has been
      chosen" caveat is **still accurate**; update it only once one actually is
- [ ] Wk 5: object-shift injector. **Only object-shift needs building** — PushT
      already ships `keypoint_visible_rate` (occlusion) and `n_latency_steps`
      (delayed observation). Caveat: visibility resamples every step rather than
      persistently occluding a region, and neither has a clean LIBERO analogue, so
      these are dev proxies, not the real injector.

## Recent decisions

Full archive with reasoning in `DECISIONS.md`.

- **2026-07-29** — Diffusion Policy vendored into this repo (369 files, MIT,
  unmodified at `5ba07ac`) rather than pinned by hash; `.gitignore` uses per-repo
  opt-in so LIBERO's ~100 GB can never be swept in by a blanket rule.
- **2026-07-29** — PushT `success_flag` = `max_reward >= 1.0` (coverage ≥ 95%),
  with the continuous score logged alongside it.
- **2026-07-28** — *No decision.* A SageMaker entry was drafted and removed before
  commit; availability was confirmed, nothing was chosen.
- **2026-07-27** — Repo is the single source of truth; Drive copies retired.
- **2026-07-26** — Logging schema locked as a superset with a `[live]`/`[derived]`
  split; append-only JSONL/CSV as source of truth.
- **2026-07-26** — Cost model *structure* locked (swept ratio, 1×–1000× log-spaced,
  static base); values iterate in Phase 3.
- **2026-07-18** — Asymmetric cost promoted to headline; adaptive horizon demoted
  to mechanism.
