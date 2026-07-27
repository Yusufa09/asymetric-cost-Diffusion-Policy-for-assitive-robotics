---
description: Update STATUS, LOG, and DECISIONS from this session, then stage for review
---

End-of-session ritual. The value of this repo is entirely in whether this
actually happens, so keep it fast — under two minutes of my time.

Work from what happened in **this conversation**. Don't ask me to summarize
things you already watched me do. Ask only about what you genuinely can't infer.

## Steps

1. **Read `context/STATUS.md`** and skim `context/LOG.md` for the most recent
   entry, so you know what state you're updating from.

2. **Infer what happened this session** from the conversation: what got built,
   what broke, what was learned, what decisions were made. If something material
   is ambiguous — especially whether a thing actually *works* vs. was merely
   attempted — ask me. One batched question, not a series.

3. **Append to `context/LOG.md`** (newest first, directly under the header, above
   any previous entry). Use the template. 3–5 lines. Record what broke and the
   workaround, not just what succeeded — that's the part future-you needs.

4. **Rewrite `context/STATUS.md`.** Update the date, current position, **the
   single next concrete action**, the last-3-decisions list, open questions, and
   the checklists. It is a snapshot, not a journal: delete what's no longer true
   rather than accumulating. **Keep it to one page** — it loads into every
   session, so length here taxes every future conversation.

5. **If a decision was made, append to `context/DECISIONS.md`** (newest first)
   with **What / Why / Consequences**. The *why* is the whole point — it's
   rebuttal ammunition for judges. A decision here means a choice that constrains
   future work, not a routine implementation detail.

6. **Flag drift.** If STATUS previously claimed something was done that this
   session revealed was not, say so plainly rather than quietly correcting it.
   This exact gap — prose claiming progress while checkboxes stayed unchecked —
   has already bitten this project twice.

7. **Update other context files only if genuinely stale:**
   - `SETUP.md` — the environment changed, or a documented step didn't work as written
   - `SPEC.md` — only for a real schema/cost-model change (rare; it's a contract)
   - `PLAN.md` / `LITERATURE.md` — phase gates only
   - `RESULTS.md` — create it when the first real number lands, then append

8. **Stage, then hand off.** `git add` the context changes plus any code from this
   session, then print a suggested commit message — a real one summarizing the
   session, not "update docs." **Then stop.**

## Rules

- **Never run `git commit`.** I commit everything myself. Never push, never
  reset/revert real history, never amend. Staging and read-only git are fine.
- Never mark something done that wasn't verified. "Attempted, blocked on X" is
  more useful than an optimistic checkmark.
- Never invent a number, a result, or a task ID. Unknown is `TBD`.
- Keep the writing terse. These files are read under time pressure in January.
