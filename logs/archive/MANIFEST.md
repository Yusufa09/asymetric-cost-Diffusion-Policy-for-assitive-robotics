# Archive manifest

Durable copy of the raw per-episode rows. **Committed to git** — this directory is
the exception carved out of the `logs/` ignore rule. Procedure and rationale:
`context/SETUP.md` § Backing up raw results.

One line per run, newest first. Never edit or delete a row once written; if a run
was bad, say so in the note rather than removing it — the record of what was run
is part of the data book.

| Run ID | Date | Code commit | Rows | What it was |
|---|---|---|---|---|
| _(none yet — first row lands with the PushT checkpoint eval, SETUP.md Step 3)_ | | | | |
