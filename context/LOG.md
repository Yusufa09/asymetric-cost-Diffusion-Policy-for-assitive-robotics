# LOG

Dated session journal. Append-only, **newest first**: what you did, what you
observed, what broke, what's next.

This is the file `STATUS.md` can't be — STATUS is a snapshot that gets
overwritten; this is the history. Two payoffs: in January you write the abstract
from this instead of reconstructing it, and it is the **project data book**.
Commit timestamps give tamper-evident dating.

> **Open:** confirm whether a git-committed markdown log satisfies the
> ScienceMontgomery / ISEF data book requirement, or whether a physical
> handwritten logbook is required. Tracked in `STATUS.md`. Verify early — the
> value of a data book is that it was contemporaneous, so it can't be honestly
> reconstructed later.

## How much detail

**This file is not auto-loaded into sessions, so length here is free.** Write for
a judge and for January-you, not for brevity. A substantive work session is a
paragraph or two plus specifics — roughly 10–25 lines. A 20-minute admin session
is three. Length tracks what happened, not a quota.

Five properties make it a real research log:

1. **Contemporaneous.** Written the day it happened. Not reconstructed.
2. **Failed attempts included.** The three hours lost to a build error *is* the
   record. A log containing only successes reads as fabricated.
3. **Specific enough to reconstruct.** Actual commands, versions, config values,
   error text. "Got PushT working" is worthless in January; the exact incantation
   that resolved it is what you need.
4. **Raw observation before interpretation.** The number you saw, with seed and
   n, then what you think it means.
5. **Reasoning captured at the moment of choosing**, not rationalized afterward.

Numbers live in `logs/*.jsonl` per `SPEC.md` — this file records what you ran,
what you saw, and what you concluded, with pointers to run IDs.

Template:

```
## YYYY-MM-DD — <session focus>  (N hrs)

**Goal:** what I set out to do.

**Did:** commands, versions, configs, hashes. Specific.

**Observed:** raw numbers with seed and n; the published figure being compared
against; wallclock. Interpretation after the number, not instead of it.

**Broke / dead ends:** what failed, how long it cost, how it was diagnosed,
what actually fixed it. Do not skip this section.

**Decided:** anything that constrains future work → also append to DECISIONS.md.

**Next:** the handoff to the next session.
```

Log hours per session — it feeds the ISEF forms and tracks against the
10–12 hrs/week capacity assumption in `PLAN.md`.

---

## 2026-07-27 — Repo and context system stood up

**Did:** Created the repo and the `context/` documentation system — CLAUDE.md
(auto-loading handoff), STATUS, LOG, DECISIONS, PLAN, SPEC, LITERATURE, SETUP,
MAINTENANCE, plus the `/session-end` command. Migrated plan v2, the full
literature review, and the cost model / logging schema out of Drive and the
planning chats. Folded in the 2026-07-26 decisions that had never reached STATUS.

**Broke / learned:** Two drift problems surfaced during migration. (1) STATUS had
gone nine days without an update and was missing every decision from the Phase 0
chat. (2) Plan §6 was still the v1 logging schema, superseded by SPEC. Both
reconciled. Also corrected a false entry I had briefly recorded: the compute
stack was written up as a decision when it is in fact **still undecided** —
removed from DECISIONS and reopened as a question in STATUS.

**Next:** Install Diffusion Policy and evaluate a released low-dim PushT
checkpoint on CPU. See `SETUP.md`.

---

## Reconstructed entries

_The entries below predate this log and were reconstructed from the planning and
Phase 0 chat transcripts on 2026-07-27. Dates are approximate to the day._

## 2026-07-26 — Cost model and logging schema locked

**Did:** Worked through the four design axes of the cost model and settled the
structure-vs-values distinction. Specified all three logging tables as a superset
with a `[live]`/`[derived]` split. Discussed compute options; **nothing decided.**

**Broke / learned:** Google Drive's `create_file` path failed four times
including on a minimal test, so the spec never got written to Drive — it existed
only as paste-ready text in the chat until today's migration. Direct cause of the
"repo is the single source of truth" decision.

**Next:** Make the repo, then DP install.

## 2026-07-20 — Phase 0 chat opened

**Did:** Opened the Phase 0 working chat. Confirmed position (Week 1 of 28) and
identified the Week 1 critical path. Established that none of the Week 1 work
requires cloud compute — PushT is CPU-local, so the compute decision can be
deferred without blocking anything. Settled the checkpoint-eval-before-training
tactic and the two-conda-env strategy.

**Broke / learned:** Found the first STATUS drift — STATUS claimed AWS credits
confirmed, PushT rolling out, and LIBERO task IDs identified, while every
corresponding checklist box was unchecked and none had actually been verified.

**Next:** Cost model on paper; repo; DP install.

## 2026-07-18 — Literature review and plan v2

**Did:** Ran an intensive literature review across adaptive horizon, failure
detection, conformal tooling, recovery, and assistive cost-asymmetry. Rewrote the
plan as v2 with six changes folded in.

**Broke / learned:** **The project's central novelty claim collapsed.** Adaptive
execution horizon is a populated 2025–26 subfield, and AutoHorizon already runs
the originally-proposed K-sample MC-variance signal as a dominated baseline.
Response: promoted the asymmetric-cost evaluation to headline, demoted adaptive
horizon to mechanism, switched the control signal to inter-chunk consistency, and
adopted AEGIS's two controls.

**Next:** Set up the document/workflow system; start Phase 0.

## 2026-07-17 — Project planning

**Did:** Worked through the four open decisions from the handoff — tasks,
disturbances, uncertainty signal, framing. Locked all four. Built the first full
plan: phase map, week-by-week schedule, experiment grid, logging schema, metrics,
figures, per-stage kill criteria, and the 5-minute talk structure.

**Next:** Background literature review before starting any build work.
