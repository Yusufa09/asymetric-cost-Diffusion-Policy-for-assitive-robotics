# Archive manifest

Durable copy of the raw per-episode rows. **Committed to git** — this directory is
the exception carved out of the `logs/` ignore rule. Procedure and rationale:
`context/SETUP.md` § Backing up raw results.

One line per run, newest first. Never edit or delete a row once written; if a run
was bad, say so in the note rather than removing it — the record of what was run
is part of the data book.

| Run ID | Date | Code commit | Rows | What it was |
|---|---|---|---|---|
| `20260729T005212Z` | 2026-07-29 | `2105254`-dirty | 56 | PushT low-dim checkpoint eval, full reproduction. n_test=50 + n_train=6, n_envs=56, CPU. `test/mean_score` **0.9453** vs published 0.969 (0.87 se). Archived in `table_a_20260729.jsonl.gz`. |
| `20260729T004902Z` | 2026-07-29 | `2105254`-dirty | 2 | PushT smoke test, n_test=2/n_envs=2. 2/2 success. First rows ever written against the SPEC Table A schema. Same archive file. |

**Note on the `-dirty` commit tag.** Both runs executed against uncommitted code
(`src/rollout/eval_pusht.py` and `src/logging/rows.py` were untracked at run
time), so `git_commit` in the rows honestly records `<hash>-dirty` rather than
claiming a clean tree. The code is staged in the commit that adds this line.
Future runs should execute against committed code so provenance is exact.

**Restore test performed 2026-07-29:** `gunzip -c` of the archive diffed
byte-identical against `logs/table_a.jsonl` (58 rows). Satisfies the SETUP.md
§ Backing up raw results requirement that a backup be tested, not assumed.
Tier-2 (blob) backup is still **not** configured — no `intermediate_state_ref`
blobs exist yet, so nothing is currently at risk from its absence.
