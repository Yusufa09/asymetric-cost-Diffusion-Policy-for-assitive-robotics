"""Append-only JSONL row emitter for the SPEC.md logging schema.

Principle (SPEC.md Part 2): log RAW per-event rows, never aggregates. A field
that is not measurable in a given run is written as `null` — never estimated,
never filled in with a plausible number. Aggregates are computed downstream from
these rows, forever.

NOTE ON THE PACKAGE NAME: this package is `src.logging`, which shadows the
stdlib `logging` module if `src/` itself is ever placed on `sys.path`. Always
put the REPO ROOT on sys.path and import as `src.logging.rows`. Never add
`src/` directly.
"""

import hashlib
import json
import pathlib
import subprocess

# SPEC.md Table A, plus additive fields. The schema is a contract: fields may be
# added (it is defined as a superset), never silently dropped or renamed.
TABLE_A_FIELDS = [
    "episode_id",
    "task_id",
    "seed",
    "condition",
    "disturbance_type",
    "disturbance_magnitude",
    "disturbance_onset_step",
    "success_flag",
    "episode_length",
    "total_denoising_passes",
    "total_replans",
    "wallclock",
    "checkpoint_dir",
    "git_commit",
    "config_hash",
    # --- additive, not in SPEC.md Table A as written ---
    # The continuous score behind success_flag. PushT's env reward is
    # clip(coverage / 0.95, 0, 1) and success is coverage >= 0.95, i.e.
    # max_reward >= 1.0. Logging the float keeps every success threshold
    # recomputable instead of freezing one at rollout time.
    "max_reward",
    # `wallclock` is per-CHUNK, not per-episode: episodes inside a vectorised
    # chunk step in lockstep and cannot be timed apart. This field records how
    # many episodes shared that wallclock so the ambiguity is never lost.
    "episodes_in_chunk",
]


def git_commit(repo_root):
    """HEAD of the analysis repo, suffixed `-dirty` if the tree is modified.

    Provenance is worthless if it silently claims a clean commit for a run
    executed against uncommitted code.
    """
    def _git(*args):
        return subprocess.check_output(
            ["git", "-C", str(repo_root), *args], text=True
        ).strip()

    try:
        commit = _git("rev-parse", "HEAD")
        if _git("status", "--porcelain"):
            commit += "-dirty"
        return commit
    except subprocess.CalledProcessError:
        return None


def config_hash(cfg):
    """Stable hash of the resolved config. This is what makes a run
    reproducible in January."""
    from omegaconf import OmegaConf

    text = OmegaConf.to_yaml(cfg, resolve=False)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def append_rows(path, rows):
    """Append rows to a JSONL file, creating parent dirs as needed.

    Validates field names against the schema so a typo becomes an error at
    write time rather than a silently missing column in December.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    allowed = set(TABLE_A_FIELDS)
    for row in rows:
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"row has fields not in Table A schema: {sorted(unknown)}")
        missing = allowed - set(row)
        if missing:
            raise ValueError(f"row is missing Table A fields: {sorted(missing)}")

    with path.open("a") as f:
        for row in rows:
            f.write(json.dumps({k: row[k] for k in TABLE_A_FIELDS}) + "\n")

    return len(rows)
