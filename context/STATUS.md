# STATUS

**Keep this to ONE PAGE.** It loads into every Claude Code session via
`CLAUDE.md`, so length here is a tax on every conversation. Decisions older than
the last three move to `DECISIONS.md`.

_Last updated: 2026-07-27_

---

## Current position

**Phase 0 — Setup & Baseline. Week 2 of 28.**

Planning is well ahead of execution. The design work is done — plan v2, the
literature review, the cost model, and the logging schema are all locked. **No
code has been written and no rollout has run.** The repo was created 2026-07-27.

**Next gate: Phase-0 gate, Week 4 (~Aug 13).**
Pass = Diffusion Policy reproduces published success rates on all three LIBERO
tasks. Fail = drop to 2 tasks → use released checkpoints → worst case PushT
becomes the quantitative platform and LIBERO becomes video-only.

## The single next concrete action

**Install Diffusion Policy and evaluate a released PushT checkpoint on CPU.**

Not training — *evaluation of a released checkpoint*. This is the highest-leverage
move available because it separates two questions that are otherwise tangled:
"does the rollout pipe run end-to-end?" (an afternoon) from "can I hit published
numbers?" (a Week 4 compute question). If the checkpoint evaluates and emits a
Table A row, Phase 0 stops being a research risk and becomes a billing question.
If it errors, the real blocker surfaces now instead of in Week 4.

Steps are in `SETUP.md`. Budget the most time for the conda environment.

## Last 3 decisions

Full archive with reasoning in `DECISIONS.md`.

- **2026-07-27** — Repo is the single source of truth; Drive copies retired.
- **2026-07-26** — Logging schema locked as a superset with a `[live]`/`[derived]` split; append-only JSONL/CSV as source of truth.
- **2026-07-26** — Cost model *structure* locked (swept ratio, 1×–1000× log-spaced, static base); values left to iterate in Phase 3.

## Open questions

- **Compute stack — entirely undecided.** No provider has been chosen. AWS,
  RunPod, Kaggle, Vast, and Colab are all still live options, and AWS is still on
  the table. Being resolved 2026-07-28. Inputs that will matter: whether AWS
  credits exist and how large/long-lived they are, setup friction vs. cost, and
  whether the interactive dev layer and the Phase-2 bulk sink want the same
  provider. **Nothing in Phase 0 is blocked by this** — PushT is CPU-local.
- **ScienceMontgomery 2027 registration and abstract deadlines.** The one hard
  external wall. Paperwork lands weeks before the March fair.
- **Does a git-committed `LOG.md` satisfy the ISEF/ScienceMontgomery project data
  book requirement,** or is a physical/handwritten logbook required? Changes how
  much ceremony `LOG.md` needs.

## Blocked / at risk

Nothing blocked.

**Standing risk — Phase-0 baseline reproduction is the critical path.** If LIBERO
checkpoints don't reproduce, everything downstream compresses against the
Thanksgiving and January walls.

**Live risk — schedule.** Today is the start of plan-Week 2, and the Week 1
execution spine (DP install, PushT on CPU) has not started. Week 2's own tasks
(LIBERO reproduction, task ID verification, LIBERO-Plus/Pro audit) are now due
concurrently. Not alarming yet; it becomes alarming if Week 3 opens the same way.

## Checklist

**Week 1 — carried over, execution not started**

- [ ] Install Diffusion Policy; get PushT running on CPU end-to-end
- [ ] Evaluate a released low-dim PushT checkpoint; emit one Table A log row
- [ ] Decide the compute stack (2026-07-28), then stand up the cloud env
- [ ] Confirm ScienceMontgomery 2027 registration + abstract deadline
- [x] Write the asymmetric cost model on paper — done, see `SPEC.md`
- [x] Design the logging schema — done, see `SPEC.md`
- [x] Create the repo and context docs

**Week 2 — due now**

- [ ] Verify the 3 LIBERO task IDs. STATUS previously claimed these were
      "identified" but they were never verified; treat as unknown until confirmed
      to exist with the right observation/action space.
- [ ] Audit LIBERO-Plus / LIBERO-Pro for existing perturbation harnesses.
      90 minutes, and the highest-leverage 90 minutes in the schedule — if either
      implements object shift or occlusion, Phase 1 compresses by ~2 weeks and you
      inherit a standard others recognize. If not, you've confirmed your injector
      is worth building.
- [ ] Reproduce DP on one LIBERO task; confirm success rate near published

**Queued**

- [ ] Wk 3: logging schema live before any real run (per instrument-from-day-one, Table A should exist earlier than this)
- [ ] Wk 4+: sponsor outreach, once a reproduced baseline exists
