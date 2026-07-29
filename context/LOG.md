# LOG

Dated session journal. Append-only, **newest first**: what you did, what you
observed, what broke, what's next.

This is the file `STATUS.md` can't be — STATUS is a snapshot that gets
overwritten; this is the history. Two payoffs: in January you write the abstract
from this instead of reconstructing it, and it is the **project data book**.
Commit timestamps give tamper-evident dating.

> **Resolved 2026-07-28:** the data book format is flexible, so this
> git-committed markdown log satisfies the requirement. No physical handwritten
> logbook is needed. Keep writing it contemporaneously anyway — that property is
> what makes it worth anything to a judge.

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

## 2026-07-28 — Compute stack investigation; AWS GPU access path found  (~2 hrs)

**Goal:** Resolve the compute-stack decision STATUS scheduled for today.

**Did:** Priced every candidate against PLAN §10's 350–650 GPU-hr estimate.
**One** AWS account open on the post-2025-07-15 Free Tier ($100 at signup + $100
for five onboarding tasks, **6-month expiry with automatic account closure**),
balance **$200, untouched**; two more can be opened on demand. Then established
the session's key fact by comparing two quota paths. SageMaker `ml.g5.2xlarge`
also **defaults to 0**, but the increase to **1 instance is self-service and
granted immediately, on any account** — no support case, no wait. EC2's G-family
quotas (`Running On-Demand G and VT instances` and `All G and VT Spot Instance
Requests`, independently adjustable, separate namespace from SageMaker's) also
default to **0 vCPU** but require a support case and 1–5 business days, with
denial common for accounts without billing history. So the difference between the
two surfaces is **not** quota vs. no quota — it is *minutes* vs. *days-with-a-
maybe*. Filed both EC2 requests in `us-east-1`:
`Running On-Demand G and VT instances` → 8 vCPU (`L-DB2E81BA`) and
`All G and VT Spot Instance Requests` → 16 vCPU (`L-3819A6DF`). Both **PENDING**
at end of session.

**Observed:** No rollout numbers — nothing was run. Pricing collected, all
approximate and none yet checked against a real invoice: EC2 `g6.xlarge`
on-demand $0.8048/hr, `g5.xlarge` $1.006/hr, EC2 Spot ~$0.30–0.40/hr, RunPod RTX
4090 $0.34/hr, Vast RTX 4090 ~$0.29–0.39/hr, SageMaker `ml.g5.2xlarge` ~$1.5/hr
(**estimated** from `g5.2xlarge` plus typical managed markup — not sourced, and
load-bearing, so verify it off Cost Explorer once real hours exist). The spread
that matters: $200 buys **~130 GPU-hr** on SageMaker on-demand versus **~570** on
EC2 Spot. That ~4× gap is the entire reason the EC2 request is worth filing.

**Second constraint, previously unmodeled: SageMaker's instant quota grant caps
at 1 instance.** So SageMaker gives at most **one concurrent GPU per account** —
three accounts, three concurrent instances, ~400 GPU-hr total. Credits bind before
wall-clock does (~400 GPU-hr over 3 instances ≈ 5.5 days of continuous 3-way
parallel running, inside a 5-week Phase-2 window), so the ceiling is survivable,
but it means the Phase-2 grid has **no ability to burst**. Whether the cap can be
raised above 1, and whether the instant grant applies to *training job* /
*processing job* / *spot training job* usage types as well as notebook usage, is
unknown and matters — those are the surfaces a batch grid would actually use.

**Broke / dead ends:** Three recommendations were made and reversed *within* the
session. Recording them because each reversal was forced by a fact, and the
sequence is the actual finding. (1) "Single-provider AWS on EC2 Spot" — killed on
learning EC2 G quotas default to 0 and are routinely denied for individual
accounts with no billing history. (2) "RunPod primary, ~$150–250 out of pocket" —
killed on learning SageMaker already works today. (3) The multi-account plan was
flagged against AWS Free Tier Terms (creating "more than one account to receive
additional benefits" ⇒ ineligible, standard rates charged); resolved as
non-applicable because the accounts belong to different people. Net cost: no
wasted spend, but the lesson is sharp — **AWS GPU access is gated by quota, not
by credits**, and SETUP.md's prior analysis had silently assumed EC2 access was
obtainable. That assumption was the load-bearing error.

**Decided:** *Nothing.* The compute stack is still open and now waits on the EC2
quota outcome. Recording that explicitly, because a DECISIONS.md entry locking
SageMaker as the Phase 0–1 surface was drafted this session and **removed before
commit** — what the session produced was a fact (SageMaker works without a support
case), and availability is not a choice. This is the **second time in ten days**
the compute stack has been written up as decided when it wasn't; the 2026-07-27
entry below records the first. The pattern is worth naming: the moment an option
is confirmed to work, the writeup wants to promote it to "chosen," and it takes a
deliberate pass to catch. Sole guard is `MAINTENANCE.md` rule 2 — never mark
something done that wasn't verified.

**Closed:** Data book format — flexible, so this markdown log qualifies. GitHub
repo confirmed private.

**Opened:** Competition venue is undecided — ScienceMontgomery vs. PG County,
the latter possibly an easier ISEF path. Changes nothing about the project or the
schedule, but the two have different registration and abstract deadlines, so it
cannot stay unexamined. ScienceMontgomery 2027 registration is **not yet open**.

**Next:** Install Diffusion Policy and evaluate a released low-dim PushT
checkpoint on CPU, per `SETUP.md`. Unchanged, unblocked by any of the above, and
now two sessions overdue.

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
