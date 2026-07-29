# STATUS

Everything currently open. Loads into every Claude Code session via `CLAUDE.md`.

**The rule: this file holds every live loose end, and an item is deleted the
instant it closes** — not archived here. History lives in `LOG.md` and
`DECISIONS.md`, so deletion loses nothing. There is no length limit; the bounding
force is closure. Sections are ordered by how often they change, so a routine
session only rewrites the top.

_Last updated: 2026-07-28_

---

## Current position

**Phase 0 — Setup & Baseline. Week 2 of 28.**

> **Week 1 starts 2026-07-17 (a Friday); weeks run Fri–Thu.** The week number is
> *computed from this anchor*, never asserted from memory:
> `week = floor((today - 2026-07-17) / 7) + 1`. Cross-checks against `PLAN.md` §2:
> Week 4 = Aug 7–13 (the Phase-0 gate), Week 25 = Jan 1–7, Week 28 = Jan 22–28
> (experiment freeze). Recompute every session — a stale week number is the
> cheapest possible way to lose track of the January wall.

Planning is well ahead of execution. Plan v2, the literature review, the cost
model, and the logging schema are all locked. **No code has been written and no
rollout has run.** Repo created 2026-07-27. **The compute stack is still
undecided** — what changed on 2026-07-28 is that one option (SageMaker) is now
confirmed to work, which is availability, not a choice.

**Next gate: Phase-0 gate, Week 4 (~Aug 13).**
Pass = Diffusion Policy reproduces published success rates on all three LIBERO
tasks. Fail = drop to 2 tasks → use released checkpoints → worst case PushT
becomes the quantitative platform and LIBERO becomes video-only.

## The single next concrete action

**Install Diffusion Policy and evaluate a released low-dim PushT checkpoint on
CPU.** Steps in `SETUP.md`. Budget the most time for the conda environment.

Unchanged from last session, unblocked by anything in the compute thread, and now
**two sessions overdue**. Not training — *evaluation of a released checkpoint*.
This separates "does the rollout pipe run end-to-end?" (an afternoon) from "can I
hit published numbers?" (a Week 4 compute question). If the checkpoint evaluates
and emits a Table A row, Phase 0 stops being a research risk and becomes a
billing question. If it errors, the real blocker surfaces now instead of in Week 4.

## Blocked / at risk

Nothing hard-blocked. A GPU exists; the critical path is local CPU work.

- **Phase-0 baseline reproduction is the critical path.** Standing risk for the
  whole project. If LIBERO checkpoints don't reproduce, everything downstream
  compresses against the Thanksgiving and January walls.
- **Schedule drift is now at the threshold STATUS itself named.** Last session
  said drift "becomes alarming if Week 3 opens the same way." **Week 3 opens
  Friday 2026-07-31**, and the Week-1 execution spine (DP install, PushT on CPU)
  still has not started — two full weeks of planning-only work. The compute thread
  was real and produced a usable answer, but it was never on the critical path.
  The next session must be code.
- **Bulk-grid compute would be marginal on the cheapest confirmed option, and
  capped.** If it ends up being SageMaker on-demand (~$1.5/hr, *estimated*), $200
  buys ~130 GPU-hr; three accounts ≈ 400 against a 350–650 requirement — the low
  end with zero slack for a re-run. **Plus a concurrency ceiling no earlier
  analysis modeled: SageMaker's instant quota grant caps at 1 instance per
  account**, so three accounts means at most three concurrent GPUs and no ability
  to burst. Credits still bind before wall-clock (~400 GPU-hr across 3 instances
  ≈ 5.5 days continuous, inside a 5-week Phase-2 window), so it is survivable —
  but it removes the option of buying back schedule with parallelism. Relieved by
  any one of: the EC2 Spot quota landing (16 vCPU = 4 concurrent `g6.xlarge`), the
  cap turning out raisable, or the real GPU-hr requirement measuring lower.

## Open decisions — mine to make

- **Compute stack — still entirely undecided. No provider chosen.** AWS
  (SageMaker or EC2), RunPod, Vast, Kaggle and Colab all remain live. The one
  thing that changed 2026-07-28: SageMaker `ml.g5.2xlarge` also starts at quota 0,
  but **raises to 1 instance instantly, self-service, on any account** — so one
  option is known-obtainable in minutes rather than hypothetical. Currently **1
  account open** ($200, untouched); two more can be opened whenever needed, for a
  $600 maximum. **Resolving after the EC2 quota requests come back** — that
  outcome is the input the choice is waiting on. Deciding sooner means deciding on
  worse information, and Phase 1 will also supply a *measured* GPU-hr figure to
  replace the current estimate. **Nothing in Phase 0 is blocked by this** — PushT
  is CPU-local.
- **Tier-2 backup destination.** Deliberately deferred alongside the compute
  stack, but the reasoning inverted: it must **not** be colocated with compute,
  because the AWS accounts auto-close and would take their S3 buckets with them.
  Leading candidate is Google Drive. **Must close before the first real run writes
  rows.**
- **Competition venue — ScienceMontgomery vs. PG County.** PG County may be an
  easier ISEF path. Changes nothing about the project, the plan, or the schedule,
  but the two have different registration and abstract deadlines, so it can't stay
  unexamined. Low urgency; ScienceMontgomery registration isn't open yet anyway.
- **No rebuttal drafted for VLA-Corrector (2607.01804).** The lit review calls it
  the nearest neighbor — detect-and-correct → event-triggered adaptive horizon,
  i.e. the same combination this project makes, on VLAs. `PLAN.md` §9 has answers
  for DVAC/DEHP/AutoHorizon/Rewind-IL/AEGIS but not this one. Needs one before any
  mentor conversation. Pure reading and writing — good filler for a session where
  you don't want to fight dependencies.

## Waiting on the outside world

Things I don't control. Cheap to check, expensive to forget.

- **Two EC2 quota requests, filed 2026-07-28 in `us-east-1`, both PENDING.**
  `Running On-Demand G and VT instances` → 8 vCPU (`L-DB2E81BA`) and
  `All G and VT Spot Instance Requests` → 16 vCPU (`L-3819A6DF`). Expect 1–5
  business days; auto-denial within minutes is common and expected. **On denial,
  open a support case** — escalation path and justification wording in `SETUP.md`
  § Quotas. Not blocking anything; this is a ~4× headroom upgrade, not a
  prerequisite.
- **ScienceMontgomery 2027 registration — not yet open** (checked 2026-07-28).
  Re-check periodically. The abstract/registration deadline remains the one hard
  external wall, and it lands weeks before the March fair.
- **PG County science fair deadlines** — unknown, not yet checked. Pairs with the
  venue decision above.

## Deferred by design

Parked deliberately, with the reason and when it comes back. Not forgotten.

- **LIBERO task IDs — unverified.** STATUS previously claimed "identified"; they
  never were. Treat as unknown until confirmed to exist with the right
  observation/action space. **Returns: Week 2 (now).**
- **`intermediate_state_ref` should point to a MuJoCo sim-state snapshot, not
  rendered frames.** ~KB/step (~1 GB per thousand episodes, fits free Drive) vs.
  ~100× that for frames. Recorded in `SETUP.md`; implement when the logger is
  written. **Returns: Wk 7.**
- **Recoverability definitions.** `recoverable_at_detection_flag` and
  `ground_truth_failure_step` need real definitions of "recoverable" and
  "irreversible" — a research task, not a log write. Kept reachable via
  `intermediate_state_ref` logged live. **Returns: Phase 4.**
- **Cost model values.** Sweep bounds, latency-weighting, whether TP carries a
  replan cost. Structure is locked; values are meant to iterate against real
  detection-latency distributions. **Returns: Phase 3.**
- **Second detector signal** (chunk magnitude, ActProbe-style). Only if
  inter-chunk consistency separates weakly. Otherwise bank the time.
  **Returns: Week 9.**
- **Sponsor outreach.** Pitch idea + preliminary result, not a cold ask — so it
  fires once a reproduced baseline exists. Target postdocs / senior PhD students.
  **Returns: Week 4+.**
- **Drive copies not yet retired.** Plan, lit review, STATUS, and cost/schema now
  exist in both Drive and this repo. Repo is the source of truth; delete or mark
  the Drive versions read-only before they drift. **Returns: whenever, but soon.**

## Standing commitments

Easy to skip, costly to skip.

- **Earmark compute for the Phase-2 controls now** (~30 cells). The failure mode
  is reaching January having spent the budget on extra seeds. Sharper now that the
  budget is measured in ~130 GPU-hr units rather than assumed abundance.
- **Re-verify the literature at each phase gate** (~20 min × 5). Several key
  papers post-date model training cutoffs and the adaptive-horizon space moves fast.
- **Instrument from day one.** Every rollout, including the checkpoint-eval smoke
  test, emits schema rows. An unlogged rollout is a thrown-away rollout.
- **Budget alarms before launching any GPU instance.** The payment methods on
  these accounts belong to other people, notebook instances do not auto-stop, and
  a forgotten one drains $200 in under six days. Alarm on credit *balance*, not
  just spend.

## Checklists

**AWS — verification owed (all cheap, none blocking)**

- [ ] Check whether the SageMaker `ml.g5.2xlarge` cap can be raised **above 1**,
      and whether the instant self-service grant covers *training job* /
      *processing job* / *spot training job* usage types or only notebook/Studio.
      Each usage type is defaulted independently, and the batch types are the ones
      a Phase-2 grid would run on. Query in `SETUP.md` § Quotas.
- [ ] Verify the true `ml.g5.2xlarge` $/hr off Cost Explorer once real hours
      exist. The ~$1.5/hr figure is an *estimate* and it is load-bearing.
- [ ] Configure Budgets alarms on credit balance, on every account before
      launching anything.

**Week 1 — carried over, execution still not started**

- [ ] Install Diffusion Policy; get PushT running on CPU end-to-end
- [ ] Evaluate a released low-dim PushT checkpoint; emit one Table A log row
- [ ] Decide the compute stack — **not done.** Was scheduled for 2026-07-28;
      investigated that day but no provider chosen. Now waiting on the EC2 quota
      outcome
- [x] Confirm ScienceMontgomery 2027 registration + abstract deadline — checked
      2026-07-28, **registration not yet open**; re-check periodically
- [x] Write the asymmetric cost model on paper — `SPEC.md`
- [x] Design the logging schema — `SPEC.md`
- [x] Create the repo and context docs

**Week 2 — due now**

- [ ] Verify the 3 LIBERO task IDs
- [ ] Audit LIBERO-Plus / LIBERO-Pro for existing perturbation harnesses. 90
      minutes, and the highest-leverage 90 minutes in the schedule — if either
      implements object shift or occlusion, Phase 1 compresses by ~2 weeks and you
      inherit a standard others recognize. If not, you've confirmed your injector
      is worth building.
- [ ] Reproduce DP on one LIBERO task; confirm success rate near published

**Queued**

- [ ] Wk 3: logging schema live before any real run (per instrument-from-day-one, Table A should exist earlier)
- [ ] Wk 4: Phase-0 gate — train/verify DP on all 3 tasks, snapshot reproducible baseline
- [ ] Wk 4: at the phase gate, re-check `PLAN.md` §10 — its "no provider has been
      chosen" caveat is **still accurate**; update it only once a provider is
      actually chosen

## Recent decisions

Full archive with reasoning in `DECISIONS.md`.

- **2026-07-28** — *No decision.* A SageMaker entry was drafted and removed before commit; availability was confirmed, nothing was chosen. See the note at the top of `DECISIONS.md`.
- **2026-07-27** — Repo is the single source of truth; Drive copies retired.
- **2026-07-26** — Logging schema locked as a superset with a `[live]`/`[derived]` split; append-only JSONL/CSV as source of truth.
- **2026-07-26** — Cost model *structure* locked (swept ratio, 1×–1000× log-spaced, static base); values iterate in Phase 3.
- **2026-07-18** — Asymmetric cost promoted to headline; adaptive horizon demoted to mechanism.
