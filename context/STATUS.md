# STATUS

Everything currently open. Loads into every Claude Code session via `CLAUDE.md`.

**The rule: this file holds every live loose end, and an item is deleted the
instant it closes** — not archived here. History lives in `LOG.md` and
`DECISIONS.md`, so deletion loses nothing. There is no length limit; the bounding
force is closure. Sections are ordered by how often they change, so a routine
session only rewrites the top.

_Last updated: 2026-07-27_

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
rollout has run.** Repo created 2026-07-27.

**Next gate: Phase-0 gate, Week 4 (~Aug 13).**
Pass = Diffusion Policy reproduces published success rates on all three LIBERO
tasks. Fail = drop to 2 tasks → use released checkpoints → worst case PushT
becomes the quantitative platform and LIBERO becomes video-only.

## The single next concrete action

**Install Diffusion Policy and evaluate a released low-dim PushT checkpoint on
CPU.** Steps in `SETUP.md`. Budget the most time for the conda environment.

Not training — *evaluation of a released checkpoint*. This separates "does the
rollout pipe run end-to-end?" (an afternoon) from "can I hit published numbers?"
(a Week 4 compute question). If the checkpoint evaluates and emits a Table A row,
Phase 0 stops being a research risk and becomes a billing question. If it errors,
the real blocker surfaces now instead of in Week 4.

## Blocked / at risk

Nothing hard-blocked.

- **Phase-0 baseline reproduction is the critical path.** Standing risk for the
  whole project. If LIBERO checkpoints don't reproduce, everything downstream
  compresses against the Thanksgiving and January walls.
- **Schedule drift.** Today opens plan-Week 2 with the Week 1 execution spine (DP
  install, PushT on CPU) not started, so Week 2's own tasks are now due
  concurrently. Not alarming yet. It becomes alarming if Week 3 opens the same way.

## Open decisions — mine to make

- **Compute stack — entirely undecided.** No provider chosen. AWS, RunPod, Kaggle,
  Vast, and Colab all still live; AWS still on the table. Resolving 2026-07-28.
  Inputs: whether AWS credits exist and how large/long-lived, setup friction vs.
  cost, and whether the interactive layer and the Phase-2 bulk sink want the same
  provider. **Nothing in Phase 0 is blocked by this** — PushT is CPU-local.
- **No rebuttal drafted for VLA-Corrector (2607.01804).** The lit review calls it
  the nearest neighbor — detect-and-correct → event-triggered adaptive horizon,
  i.e. the same combination this project makes, on VLAs. `PLAN.md` §9 has answers
  for DVAC/DEHP/AutoHorizon/Rewind-IL/AEGIS but not this one. Needs one before any
  mentor conversation.

## Waiting on the outside world

Things I don't control. Cheap to check, expensive to forget.

- **ScienceMontgomery 2027 registration and abstract deadlines.** The one hard
  external wall — paperwork lands weeks before the March fair and can't be
  renegotiated against a compiler error.
- **Project data book format.** Does ScienceMontgomery/ISEF accept a
  git-committed markdown log, or is a physical bound notebook required? **Verify
  early** — a data book's value is that it was contemporaneous, so if handwriting
  is required, discovering that in November means the record can't be honestly
  reconstructed.
- **GitHub repo visibility.** Confirm `Yusufa09/asymetric-cost-...` is private
  before the first push. Everything here is unpublished research design.

## Deferred by design

Parked deliberately, with the reason and when it comes back. Not forgotten.

- **LIBERO task IDs — unverified.** STATUS previously claimed "identified"; they
  never were. Treat as unknown until confirmed to exist with the right
  observation/action space. **Returns: Week 2.**
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
  is reaching January having spent the budget on extra seeds.
- **Re-verify the literature at each phase gate** (~20 min × 5). Several key
  papers post-date model training cutoffs and the adaptive-horizon space moves fast.
- **Instrument from day one.** Every rollout, including the checkpoint-eval smoke
  test, emits schema rows. An unlogged rollout is a thrown-away rollout.

## Checklists

**Week 1 — carried over, execution not started**

- [ ] Install Diffusion Policy; get PushT running on CPU end-to-end
- [ ] Evaluate a released low-dim PushT checkpoint; emit one Table A log row
- [ ] Decide the compute stack (2026-07-28), then stand up the cloud env
- [ ] Confirm ScienceMontgomery 2027 registration + abstract deadline
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

## Recent decisions

Full archive with reasoning in `DECISIONS.md`.

- **2026-07-27** — Repo is the single source of truth; Drive copies retired.
- **2026-07-26** — Logging schema locked as a superset with a `[live]`/`[derived]` split; append-only JSONL/CSV as source of truth.
- **2026-07-26** — Cost model *structure* locked (swept ratio, 1×–1000× log-spaced, static base); values iterate in Phase 3.
- **2026-07-18** — Asymmetric cost promoted to headline; adaptive horizon demoted to mechanism.
