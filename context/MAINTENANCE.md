# MAINTENANCE — how these files stay current

**For future Claude sessions and for me.** This defines *how*, *where*, and *how
often* every context file gets updated. If you're a Claude session unsure whether
to write something down or where it goes, this file is the answer.

The whole system depends on one thing: **the updates actually happening.** Eight
files that all need attention is eight files that all go stale. So the design is:
exactly one file changes every session, everything else has a specific, infrequent
trigger.

---

## ⛔ Never commit

**Claude must never run `git commit`.** Yusuf reviews and commits everything
himself, always. Also never `git push`, never `git reset`/`revert` on real
history, and never amend.

Claude *may*: edit files, `git add`/stage, and run read-only git commands
(`status`, `diff`, `log`). At the end of a session, stage the changes and
**summarize what should go in the commit message** — then stop and hand it over.

## The cadence table

| File | Where | How often | How |
|---|---|---|---|
| `STATUS.md` | `context/` | **Every session** | Rewrite in place. Holds **every** live loose end — no length limit. Delete each item the instant it closes. |
| `LOG.md` | `context/` | **Every session** | Append a dated entry at the top. 10–25 lines for a real work session; see the template in the file. |
| `DECISIONS.md` | `context/` | When a decision is made (~2×/month) | Append at the top. What / Why / Consequences. |
| `SETUP.md` | `context/` | When the environment changes | Edit in place. Replace planned steps with what actually worked. |
| `RESULTS.md` | `context/` | When a number lands (Phase 1+) | Create on first result, then append. **Does not exist yet.** |
| `PLAN.md` | `context/` | Phase gates (5× total) | Edit in place. Mark superseded sections rather than deleting them. |
| `LITERATURE.md` | `context/` | Phase gates (5× total, ~20 min) | Re-verify against arXiv, add what's new. |
| `SPEC.md` | `context/` | Phase 3 cost-model iteration only (1–2×) | Edit in place. **It's a contract — changing it invalidates prior runs.** |
| `CLAUDE.md` | repo root | When a standing rule changes (rare) | Edit in place. Keep short — it loads every session. |
| `MAINTENANCE.md` | `context/` | When the system itself changes | Edit in place. |

## The routine

**Every session:** run `/session-end`. It reads STATUS, infers what happened from
the conversation, appends to LOG, rewrites STATUS, appends to DECISIONS if a
decision was made, stages the changes, and hands you a suggested commit message.
Under two minutes.

**At each phase gate (5×):** re-verify the literature (~20 min — the
adaptive-horizon space moves fast and several key papers post-date model training
cutoffs), update PLAN if the schedule or grid shifted, and confirm SETUP still
reproduces from a clean checkout.

## Where a given piece of information goes

| If it's… | It goes in… |
|---|---|
| Where I am right now / what to do next | `STATUS.md` |
| What I did today, what broke, the workaround | `LOG.md` |
| A choice that constrains future work, + why | `DECISIONS.md` |
| A number, a result, a figure | `RESULTS.md` |
| A command, a version, a path, a task ID | `SETUP.md` |
| A schema field or cost-model rule | `SPEC.md` |
| A paper, a rebuttal, a field fact | `LITERATURE.md` |
| A schedule, gate, or grid change | `PLAN.md` |
| A rule I want every future session to follow | `CLAUDE.md` |

## The rules that make it work

1. **Log the *why*, not just the what.** "Switched to masked patches" is useless
   in December. "Switched because full blackout made the signal trivially
   separable and inflated AUROC" is what judges probe for.
2. **Never mark something done that wasn't verified.** "Attempted, blocked on X"
   beats an optimistic checkmark. This project has already been bitten twice by
   prose claiming progress while checkboxes stayed unchecked — once on AWS
   credits, once on LIBERO task IDs.
3. **Never invent a number, a result, or a task ID.** Unknown is `TBD`.
4. **STATUS is bounded by closure, not length.** It should hold every open loose
   end — an incomplete tracker is worse than a long one. What keeps it from
   sprawling is deleting items the moment they resolve, and ordering sections by
   how often they change so a routine session only rewrites the top. If it's
   growing because *history* is accumulating in it, that history belongs in LOG or
   DECISIONS.
5. **This repo is the single source of truth.** Not Drive, not project-knowledge
   uploads, not a chat transcript. If it isn't written here, it doesn't exist.
