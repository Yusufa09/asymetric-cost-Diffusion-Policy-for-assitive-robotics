# Disturbance-Robust Adaptive Execution Horizon for Assistive Manipulation

**Evaluated Under Asymmetric Cost.** ScienceMontgomery 2027 (Computer Science)
→ ISEF qualification.

A Diffusion Policy's inter-chunk consistency signal drives its execution horizon —
coast when confident, replan when uncertain — tested under injected disturbances
(object shift, occlusion, delayed observation) on three LIBERO tasks, with PushT
as the cheap dev environment and live demo.

**The finding:** under an assistive cost model where a missed failure far
outweighs a false alarm, the detector that looks best by AUROC is not the safest
to deploy. The ranking flips. **Prediction ≠ prevention.**

## Where things are

All project context lives in [`context/`](context/) and is the single source of
truth — not Google Drive, not project-knowledge uploads.

| File | What it is |
|---|---|
| [`context/STATUS.md`](context/STATUS.md) | **Start here.** Where the project is right now and the next concrete action. |
| [`context/LOG.md`](context/LOG.md) | Dated session journal / project data book. |
| [`context/DECISIONS.md`](context/DECISIONS.md) | Every decision with its reasoning. |
| [`context/PLAN.md`](context/PLAN.md) | Plan v2 — phases, week-by-week, experiment grid, gates. |
| [`context/SPEC.md`](context/SPEC.md) | Cost model + logging schema. The contract every rollout writes against. |
| [`context/LITERATURE.md`](context/LITERATURE.md) | Field map and reading roadmap. |
| [`context/SETUP.md`](context/SETUP.md) | Environment reproduction. |
| [`context/MAINTENANCE.md`](context/MAINTENANCE.md) | How, where, and how often each file gets updated. |

[`CLAUDE.md`](CLAUDE.md) loads automatically in Claude Code sessions and imports
STATUS, so a new conversation starts already oriented. Run `/session-end` to
update the context files and stage them for review.

## Timeline

28 weeks. Started mid-July 2026 → experiments frozen end of January 2027 → hard
stop mid-February → fair ~March 2027.
