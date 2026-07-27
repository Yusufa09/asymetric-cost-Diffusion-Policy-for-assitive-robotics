# CLAUDE.md

Science fair project repo. This file loads automatically at the start of every
Claude Code session — it is the handoff prompt, so it must stay short.

@context/STATUS.md

## ⛔ Never commit

**Never run `git commit`.** I review and commit everything myself, always — no
exceptions, not even for docs, not even when I say "add the files." Also never
`git push`, never `git reset`/`revert` on real history, never `--amend`.

You *may* edit files, `git add`/stage, and run read-only git commands (`status`,
`diff`, `log`). When work is done: stage it, tell me what the commit message
should say, and stop.

## The project

**Disturbance-Robust Adaptive Execution Horizon for Assistive Manipulation,
Evaluated Under Asymmetric Cost.** ScienceMontgomery 2027 (Computer Science)
→ ISEF qualification.

A Diffusion Policy's inter-chunk consistency signal drives its execution
horizon — coast when confident, replan when uncertain — tested under injected
disturbances (object shift, occlusion, delayed observation) on three LIBERO
tasks, with PushT as the cheap dev environment and live demo.

**Headline (N4):** under an assistive cost model where a missed failure far
outweighs a false alarm, the detector that looks best by AUROC is not the safest
to deploy. The ranking flips.

**Thesis:** prediction ≠ prevention. Detection AUROC is a gate reported in
passing, not a result. Every results claim leads with downstream recovery
utility and detection latency.

**Mechanism (M1):** horizon adaptation as the recovery response to detected
disturbance. This is the system, not the finding.

## How I work

- Give me direct recommendations, not hedged options. Document the reasoning
  alongside the decision.
- Tell me when something is weak. I'd rather hear it from you than from a judge.
- Strong ML / generative-model background. RL and robot learning are newer to me.
- Prefer the minimum code that solves the problem. No speculative abstractions.

## Never claim (these are wrong and a judge can break them in one sentence)

- **Never** claim adaptive execution horizon is a new control axis. It is a
  populated 2025–26 subfield: DVAC, DEHP, HiPolicy, MoH, AutoHorizon, SGAC,
  VLA-Corrector.
- **Never** claim diffusion policies are open-loop. They are receding-horizon;
  the vulnerability is *long execution horizons*.
- **Never** claim a better detector than Sentinel/ActProbe. The claim is that the
  evaluation everyone uses ranks detectors wrong for deployment.

Prior-work distinction, verbatim: *"Adaptive-horizon methods optimize efficiency
in nominal conditions. Detection-and-recovery methods respawn or escalate. I join
the two — horizon adaptation as the recovery response to injected external
disturbances — and evaluate under asymmetric cost, which none of them do."*

## Invariants (violating these costs a re-run of the grid, which is impossible after January)

- **Log raw per-event rows, never aggregates.** The rollout is one-shot; the
  analysis is infinitely re-runnable. Any unlogged field is unrecoverable.
- **Instrument from day one.** Every rollout — including checkpoint-eval smoke
  tests — emits schema rows. An unlogged rollout is a thrown-away rollout.
- **Never log a TP/FP/FN/TN label.** Log raw timings; derive labels in
  post-processing so every cost model stays computable.
- **The headline depends only on `[live]` fields.** `[derived]` fields feed
  optional extensions and must never become load-bearing.
- **`intermediate_state_ref` every step** or the Phase-4 recoverability stretch
  dies silently.
- Source of truth is append-only JSONL/CSV, not W&B.

## Context files

| File | What it is | Update trigger |
|---|---|---|
| `context/STATUS.md` | Where I am right now + **every open loose end**. Bounded by closure, not length. | Every session |
| `context/LOG.md` | Dated session journal / project data book. Detailed — not auto-loaded. | Every session (append) |
| `context/DECISIONS.md` | Decision archive with the WHY. | When a decision is made |
| `context/PLAN.md` | Plan v2 — phases, week-by-week, grid, gates. | Phase gates (5×) |
| `context/SPEC.md` | Cost model + logging schema. The locked contract. | Phase 3 only |
| `context/LITERATURE.md` | Field map + reading roadmap. | Phase gates (5×) |
| `context/SETUP.md` | Env reproduction: pinned commits, conda, checkpoints. | When env changes |
| `context/RESULTS.md` | Headline numbers as they land. | Not created yet — Phase 1 |
| `context/MAINTENANCE.md` | **How, where, and how often each file is updated.** | When the system changes |

Unsure whether to write something down, or where it goes? `MAINTENANCE.md` has
the cadence table and a where-does-this-go index.

## Session end

Run `/session-end`. It updates STATUS, appends to LOG, appends any decision to
DECISIONS, and stages the changes for me to commit. Do not skip it — the value of
this repo is entirely in whether the update actually happens.

## Standing reminders

- Earmark compute for the Phase-2 controls now. The failure mode is reaching
  January having spent the budget on extra seeds.
- Re-verify the literature at each phase gate (~20 min × 5). The adaptive-horizon
  space moves fast and several key papers post-date model training data.
- Log the *why*, not just the what. "Switched to masked patches" is useless in
  December. "Switched because full blackout made the signal trivially separable
  and inflated AUROC" is what judges probe.
