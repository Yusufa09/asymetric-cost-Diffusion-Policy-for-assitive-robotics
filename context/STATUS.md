# STATUS

Everything currently open. Loads into every Claude Code session via `CLAUDE.md`.

**The rule: this file holds every live loose end, and an item is deleted the
instant it closes** — not archived here. History lives in `LOG.md` and
`DECISIONS.md`, so deletion loses nothing. There is no length limit; the bounding
force is closure. Sections are ordered by how often they change, so a routine
session only rewrites the top.

_Last updated: 2026-08-04_

---

## Current position

**Phase 0 — Setup & Baseline. Week 3 of 28.**

> **Week 1 starts 2026-07-17 (a Friday); weeks run Fri–Thu.** The week number is
> *computed from this anchor*, never asserted from memory:
> `week = floor((today - 2026-07-17) / 7) + 1`. Cross-checks against `PLAN.md` §2:
> Week 4 = Aug 7–13 (the Phase-0 gate), Week 25 = Jan 1–7, Week 28 = Jan 22–28
> (experiment freeze). Recompute every session — a stale week number is the
> cheapest possible way to lose track of the January wall.

PushT is done and reproduces (`test/mean_score` **0.9453** vs published 0.969,
n=50, 0.87 se). 58 Table A rows archived and restore-tested. GPU access is live.
LIBERO is cloned and fully audited **but nothing has run on it.**

**2026-08-02 closed the two Week-2 carryovers without spending a cent of GPU** —
LIBERO was audited by reading the repo, no install required. It produced five
findings, two of which changed the plan (see `LOG.md`), and **the LIBERO platform
decision is now closed**: `libero_object` suite, per-suite training, one run.

**Schedule read — honest version.** One week behind on the LIBERO track, ahead on
infrastructure. But the week is the small part: this session found **~2–3 weeks of
scope that was never in the plan** — Phase 0 is a *training* task (no DP-LIBERO
checkpoint exists) and Phase 1 does *not* compress (no adoptable harness). Against
2 weeks of designed buffer in Phase 4. **The buffer is now spoken for; treat Phase
4 as catch-up, not the recoverability stretch.** Front-loading risk before
Thanksgiving (Wk 19) is now binding, not advisory. Offsetting: **Phase 3 — the
headline — needs no GPU at all**, so the part most likely to slip is not the
contribution.

**Next gate: Phase-0 gate, Week 4 (~Aug 13).** Pass = `libero_object` suite
average within **±5 points of 92.5%** (band declared 2026-08-02, before looking).
**This date may slip and that is acceptable** — a measured GPU-hr figure is worth
more than hitting an arbitrary Friday. What must not slip is the gate's *content*.

## The single next concrete action

**Work out how to train Diffusion Policy on `libero_object` — there is no
existing path, and this is the last unknown before the gate.**

The env is up and measured (`SETUP.md` § Step 5). What does *not* exist is a
DP-on-LIBERO training setup:

- **LIBERO's own `lifelong/` framework trains BC-RNN / BC-Transformer / ViT-T**,
  not Diffusion Policy. Its `libero.lifelong.main` entrypoint is not usable as-is.
- **Vendored DP supports pusht / robomimic / kitchen / blockpush** — not LIBERO.

**The promising lead: LIBERO demos are robomimic-format HDF5.** Verified structure
is `data/demo_N/{actions, obs, dones, rewards, states, robot_states}`, which is
exactly what DP's `train_diffusion_unet_image_workspace` + robomimic dataset path
consumes. So this is probably a config/adapter job — `shape_meta`, obs-key
mapping, action normalization — not a from-scratch trainer. **Probably. Unverified.**

Do this reading **with the instance stopped** — it costs nothing and needs no GPU.

## Blocked / at risk

- **⚠⚠ Budgets alarms STILL not configured — and the account is now on the Paid
  Plan, which removed the only structural protection.** Both submitted appeals
  assert *"I have Budgets alarms set on the credit balance"*. They are not set.
  **Carried unmet since 2026-07-31, and materially more dangerous as of
  2026-08-04.** The Free Plan blocked GPU instance types entirely and auto-closed
  the account at credit depletion, so overspend was *impossible*. Upgrading to
  Paid (required to launch `g5.2xlarge` at all) means that past $200 **the card on
  file — which is not mine — gets charged.** At ~$29/day a forgotten week is ~$200
  of someone else's money.
  - A cost budget must **exclude credits** from its calculation, or it reads
    $0.00 until the credits are gone — precisely too late.
  - An alarm only emails. **A Budgets _Action_ that auto-stops EC2 at ~90% is the
    only guard that enforces**, and it is the one that works while asleep.
- **Phase 0 is now a training task, not a download-and-evaluate task.** No released
  DP-on-LIBERO checkpoint was found (searched OpenVLA-OFT and the LeRobot hub,
  2026-08-02). Scope as *not found*, not *proven absent*. This is the single
  largest unplanned scope increase in the project so far.
- **The fallback ladder's middle rung is broken.** `PLAN.md` §7 says "use released
  checkpoints" if the gate fails. There are none for DP. Nearest substitute is
  `lerobot/pi0_libero_base` — a released flow-matching VLA with LIBERO weights,
  which keeps the chunked-horizon mechanism at zero training cost but changes the
  policy from DP to π0. **Unverified**: neither the checkpoint nor whether
  inter-chunk consistency behaves the same on a flow-matching model. Investigate
  only if the gate is actually failing; do not switch preemptively.
- **Credits do not cover the project.** ~130 GPU-hr (at the *estimated* ~$1.5/hr)
  against `PLAN.md` §10's 350–650 GPU-hr. Funds Phase 0 and probably Phase 1, not
  the Phase-2 grid. Accounts 2 and 3 are a planned step, each repeating the ~2-day
  quota appeal. **Both numbers in this bullet are estimates** — the measurement
  above is what replaces them.
- **Disk — resolved, no longer a risk.** `libero_object` demos measured at
  **7.0 GB** (10 files); instance sits at 37 G of 96 G used. The 100 GiB root was
  correct. Still **never run `download_libero_datasets.py` bare** — `--datasets`
  defaults to `all` (~100 GB). Always `--datasets libero_object --use-huggingface`.

## Open decisions — mine to make

- **The three `libero_object` task IDs — deliberately deferred, not unknown.**
  They get picked from the *measured* per-task success rates the gate run produces
  (500 Table A rows tagged by task; grouping by task is free post-processing).
  Picking them in advance would mean guessing from grasp geometry. **Do not name
  them before the gate run.**
- **Phase-2 compute funding.** EC2 `g5.2xlarge` on `051388699393` runs Phases 0–1.
  Open question is only what funds the Phase-2 grid — accounts 2 and 3 ($600 max)
  or cash on RunPod. RunPod and Vast are held in reserve, not rejected. **Decide
  once the measurement above supplies a real GPU-hr figure.**
- **Whether to train a second LIBERO suite at all.** Structurally possible; not
  planned. The real cost is not training — the injector must work in a new scene
  type, and conformal calibration is per-policy so the Object threshold does not
  transfer. **Revisit after the Phase-1 gate (Wk 10), with measured costs.** Note
  that neither candidate is good: `libero_10` has no headroom (50.5% nominal),
  `libero_goal` carries the ambiguity confound.
- **Tier-2 backup destination.** Must **not** be colocated with compute — the AWS
  accounts auto-close and would take their S3 buckets with them. Leading candidate
  is Google Drive. **Not yet urgent:** no `intermediate_state_ref` blobs exist.
  **Must close before the first run that writes them** — which is now closer,
  since `ControlEnv.get_sim_state()` makes them cheap to write.
- **Competition venue — ScienceMontgomery vs. PG County.** PG County may be an
  easier ISEF path. Changes nothing about the project or schedule, but the two have
  different registration and abstract deadlines. Low urgency.
- **No rebuttal drafted for VLA-Corrector (2607.01804).** The lit review calls it
  the nearest neighbor. `PLAN.md` §9 now has answers for DVAC/DEHP/AutoHorizon/
  Rewind-IL/AEGIS/LIBERO-Plus/LIBERO-PRO and the three-tasks critique, but not
  this one. Needs one before any mentor conversation. Pure reading and writing —
  good filler for a session where you don't want to fight dependencies.

## Waiting on the outside world

Things I don't control. Cheap to check, expensive to forget.

- **ScienceMontgomery 2027 registration — not yet open** (checked 2026-07-28).
  Re-check periodically. The abstract/registration deadline remains the one hard
  external wall, and it lands weeks before the March fair.
- **PG County science fair deadlines** — unknown, not yet checked. Pairs with the
  venue decision above.

## Deferred by design

Parked deliberately, with the reason and when it comes back. Not forgotten.

- **Success-threshold sensitivity sweep.** PushT success is `coverage ≥ 0.95`,
  inherited from IBC, not chosen — and 17 of 50 episodes sit in [0.9, 1.0), just
  under it. `max_reward` is logged as a float so every threshold stays
  recomputable. **Returns: Phase 3**, alongside the cost-ratio sweep.
- **Seeding the policy's sampling RNG.** DDPM sampling noise is unseeded, so repeat
  runs are not bit-identical. Fine for a 50-episode mean; not fine for debugging a
  single trajectory. **Returns: whenever a single-trajectory bug needs reproducing**,
  or Phase 2 if per-seed determinism is wanted in the grid.
- **`intermediate_state_ref` → MuJoCo sim-state snapshot, not rendered frames.**
  ~KB/step vs ~100× for frames. **Now unblocked on the LIBERO side** —
  `ControlEnv.get_sim_state()` (`envs/env_wrapper.py:118`) returns exactly this.
  **Returns: Wk 7**, when the logger grows Table B.
- **Recoverability definitions.** `recoverable_at_detection_flag` and
  `ground_truth_failure_step` need real definitions of "recoverable" and
  "irreversible" — a research task, not a log write. **Returns: Phase 4** — but see
  the buffer warning above; Phase 4 is now catch-up.
- **Cost model values.** Sweep bounds, latency-weighting, whether TP carries a
  replan cost. Structure locked; values iterate against real detection-latency
  distributions. **Returns: Phase 3.**
- **Second detector signal** (chunk magnitude, ActProbe-style). Only if inter-chunk
  consistency separates weakly. **Returns: Week 9.**
- **Custom cross-suite 3-task policy.** Verified *correct* on 2026-08-02 —
  `libero_object` is a floor scene, Spatial/Goal are tabletop with different
  fixtures, so three hand-picked tasks would be visually disambiguable with real
  skill diversity and no confound. **Rejected on budget and scope, not
  correctness.** **Returns: only if the Object suite gate fails** and a
  cheaper-than-a-second-suite option is wanted.
- **Sponsor outreach.** Pitch idea + preliminary result, not a cold ask. A
  reproduced baseline exists, so this is unblocked. Target postdocs / senior PhD
  students. **Returns: Week 4+.**
- **The remaining 8 vCPU of Spot quota.** AWS granted 8 of 16 and routed the rest
  to **AWS Sales**, not support. Skipped deliberately: it only buys checkpoint-
  resume handoff across a Spot reclaim. **Returns: only if the Phase-2 grid
  actually needs concurrency.** If contacted, give the real January 2027 timeline.
- **Drive copies not yet retired.** Repo is the source of truth; delete or mark the
  Drive versions read-only before they drift. **Returns: whenever, but soon.**

## Standing commitments

Easy to skip, costly to skip.

- **Never edit `external/diffusion_policy/`.** Vendored unmodified at `5ba07ac`.
  Wrap or subclass from `src/` instead.
- **Same for `external/LIBERO/`** — cloned at `8f1084e`, gitignored, not vendored.
  If it is ever vendored, delete its `.git` first and vendor the **code only**;
  a blanket un-ignore would try to commit ~100 GB of demo data.
- **Wrap long local runs in `caffeinate -is`.** The machine slept mid-rollout on
  2026-07-29. Nothing is written until a run completes.
- **Earmark compute for the Phase-2 controls now** (~30 cells). The failure mode is
  reaching January having spent the budget on extra seeds. **Now sharper — the
  Phase-4 buffer is already spoken for.**
- **Re-verify the literature at each phase gate** (~20 min × 5). Several key papers
  post-date model training cutoffs. Confirmed useful: the 2026-08-02 audit found
  two 2025 benchmarks that produced a better prior-work rebuttal than the plan had.
- **Instrument from day one.** Every rollout emits schema rows — including the
  LIBERO measurement run and the gate run.
- **Back up raw rows before the next run starts**, gzipped to `logs/archive/` with
  a MANIFEST line. Done 2026-07-29 and restore-tested.
- **Budget alarms before launching any GPU instance.** **Currently unmet — see
  Blocked.**
- **AWS mail lives on `free.yusuf999@gmail.com`, not the primary Gmail.** Account
  `051388699393`. The Gmail MCP is bound to `yusufaae09@gmail.com` and returns
  *empty* for AWS queries, which reads as "no reply yet" rather than "wrong inbox."
  Cost 20 min on 2026-07-31. Use Apple Mail for anything AWS.
- **Declare tolerance bands before looking at a number.** Phase-0 band is ±5 points
  on the `libero_object` suite average. Deciding "close enough" after seeing the
  result is how a gate stops being a gate.

## Checklists

**AWS — verification owed**

- [ ] **Configure Budgets alarms on credit balance** — blocking, see Blocked
- [ ] Verify the true `g5.2xlarge` $/hr off Cost Explorer once real hours exist.
      The ~$1.5/hr figure is an *estimate* and it is load-bearing.
- [ ] Check whether the SageMaker `ml.g5.2xlarge` cap can be raised **above 1**,
      and whether the instant self-service grant covers *training job* /
      *processing job* / *spot training job* usage types. Query in `SETUP.md`
      § Quotas. (Low priority — EC2 is the chosen platform.)
- [x] EC2 G/VT quota granted and verified — 8 vCPU on-demand + 8 vCPU Spot,
      `us-east-1`, account `051388699393`
- [x] $200 credit confirmed resident on `051388699393`

**Week 3 — status**

- [x] LIBERO cloned, code only — `8f1084e`, 650 MB, `external/LIBERO`
- [x] Observation/action space verified from source — 7-dim `OSC_POSE`, dual
      128×128 RGB + 9-dim proprio. `SETUP.md` § Step 4
- [x] Suites enumerated with canonical indices; the three planned framings shown
      not to exist in LIBERO — `SETUP.md` § Step 4, `DECISIONS.md` 2026-08-02
- [x] LIBERO-Plus / LIBERO-PRO audit (90 min) — both initialization-only, injector
      must be built. `DECISIONS.md` 2026-08-02
- [x] Suite decision closed — `libero_object`, per-suite training
- [x] Phase-0 gate criterion rewritten and band declared — `PLAN.md` §7
- [ ] **Budgets alarms + Budgets Action (auto-stop EC2)** — still unmet, now
      higher stakes on the Paid Plan. See Blocked.
- [x] Launched `g5.2xlarge` (`ami-04496a4d4cc3ce989`, A10G 23 GB, driver
      595.71.05, 100 GiB gp3); LIBERO conda env installed and **verified rendering
      headless** — `SETUP.md` § Step 5, four workarounds recorded
- [x] Pulled `libero_object` demos only — **7.0 GB**, 10 files, **50 demos/task**,
      mean traj 156.2 steps
- [x] **Env throughput measured — `n_envs=8` optimal, 233.2 steps/s.** Reverses
      the PushT/CPU finding exactly as § Step 2 predicted
- [ ] **Record the instance ID** in `SETUP.md` § Step 5 (currently `TBD`)
- [ ] **Get this repo onto the instance** — it has LIBERO only, so
      `src/logging/rows.py` is not even present there
- [ ] **Run `src/rollout/smoke_libero.py`** on the next instance start, before
      anything expensive. **The logger has never executed against the LIBERO
      path** — only PushT/CPU/`robodiff`. Written 2026-08-04, not yet run. ~1 min
      of GPU. See `SETUP.md` § "The analysis repo is NOT on the instance"
- [ ] **Time one training epoch** — blocked on the item below, not on GPU access
- [ ] **Build the DP-on-LIBERO training path** (no existing one — see next action)
- [ ] Train DP on `libero_object`

**Queued**

- [ ] Wk 4: Phase-0 gate — `libero_object` suite average within ±5 of 92.5%;
      snapshot reproducible baseline; **read off per-task rates and pick the three
      tasks**
- [ ] Wk 4: create `context/RESULTS.md` when the first LIBERO number lands
- [ ] Wk 5: object-shift injector — **full build, not integration.** On PushT,
      only object-shift needs building: `keypoint_visible_rate` (occlusion) and
      `n_latency_steps` (delayed observation) already ship. Caveat: visibility
      resamples every step rather than persistently occluding a region, and
      neither has a clean LIBERO analogue, so these are dev proxies. On LIBERO,
      all three need building — start from `set_state()` /
      `regenerate_obs_from_state()`.

## Recent decisions

Full archive with reasoning in `DECISIONS.md`.

- **2026-08-04** — Keep torch **2.4.1+cu121** on LIBERO; skip the README's
  `1.11.0+cu113`. Verified working before accepting it, and a 2022 stack on
  Ampere converts directly into fewer rollouts against a ~130 GPU-hr budget.
  Cost: our numbers are not bit-comparable to published LIBERO results, so if the
  gate misses its ±5 band, reverting torch is the first diagnostic.
- **2026-08-02** — LIBERO platform is the `libero_object` suite, per-suite
  training, one run; the three tasks are picked from measured per-task rates at
  the gate, not named in advance. Decided on budget first, then on the fact that
  `libero_goal`'s ten tasks share one scene and one object set, which would have
  contaminated an inter-chunk-consistency detector with the policy's own
  goal ambiguity.
- **2026-08-02** — The disturbance injector gets built from scratch. LIBERO-Plus
  and LIBERO-PRO both perturb at episode initialization only; neither matches a
  mid-execution disturbance experiment. Phase 1 does not compress.
- **2026-07-31** — EC2 `g5.2xlarge` is the Phase 0/1 compute platform; credits are
  spent before cash, because the AWS $200 is credit and RunPod is cash that
  belongs to someone else. Phase-2 funding still open.
- **2026-07-29** — Diffusion Policy vendored into this repo (369 files, MIT,
  unmodified at `5ba07ac`); `.gitignore` uses per-repo opt-in.
- **2026-07-29** — PushT `success_flag` = `max_reward >= 1.0` (coverage ≥ 95%),
  with the continuous score logged alongside it.
- **2026-07-26** — Logging schema locked as a superset with a `[live]`/`[derived]`
  split; append-only JSONL/CSV as source of truth.
- **2026-07-26** — Cost model *structure* locked (swept ratio, 1×–1000× log-spaced,
  static base); values iterate in Phase 3.
- **2026-07-18** — Asymmetric cost promoted to headline; adaptive horizon demoted
  to mechanism.
