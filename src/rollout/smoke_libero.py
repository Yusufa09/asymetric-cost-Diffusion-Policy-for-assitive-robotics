"""Minimal LIBERO rollout that emits Table A rows. A dry-run of the logger.

WHY THIS EXISTS: `SPEC.md` § Instrument-from-day-one gives two reasons for the
rule. The second is "it dry-runs the logging code on throwaway data so bugs
surface now rather than on the real grid." As of 2026-08-04 `src/logging/rows.py`
had only ever executed on PushT, on CPU, under `robodiff` — a different obs
space, a different action dim, and no vectorised subprocess workers. This script
runs the emitter against the real LIBERO path so schema mismatches cost minutes
instead of a gate run.

It uses a RANDOM policy. It is not an evaluation and its success rate means
nothing; the output to care about is that rows validate and land on disk.

Run on the instance (repo root on sys.path, `libero` pip-installed):

    MUJOCO_GL=egl python src/rollout/smoke_libero.py --n-episodes 4 --n-envs 2
"""

import argparse
import multiprocessing as mp
import os
import pathlib
import sys
import time
from datetime import datetime, timezone

# EGL must be set before mujoco is imported, or rendering silently returns black
# frames on a headless box. See SETUP.md § Step 5 workaround 3.
os.environ.setdefault("MUJOCO_GL", "egl")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
from omegaconf import OmegaConf  # noqa: E402

from src.logging.rows import append_rows, config_hash, git_commit  # noqa: E402


def build_env(n_envs, bddl, camera_size):
    from libero.libero.envs import OffScreenRenderEnv, SubprocVectorEnv

    kw = dict(
        bddl_file_name=bddl,
        camera_heights=camera_size,
        camera_widths=camera_size,
    )
    if n_envs == 1:
        env = OffScreenRenderEnv(**kw)
        return env, False
    # SubprocVectorEnv forks by default and EGL contexts do not survive fork —
    # workers die on first render and the parent only sees ConnectionResetError.
    # SETUP.md § Step 5 workaround 4.
    return SubprocVectorEnv([lambda: OffScreenRenderEnv(**kw) for _ in range(n_envs)]), True


def run_batch(env, vectorised, n, max_steps, rng):
    """Step a batch of episodes with random actions. Returns per-episode
    (max_reward, length). Episodes in a batch step in lockstep, so they cannot
    be timed apart — the caller records one wallclock for the whole batch."""
    env.reset()
    max_r = np.zeros(n)
    length = np.full(n, max_steps, dtype=int)
    live = np.ones(n, dtype=bool)

    for t in range(max_steps):
        act = rng.uniform(-1.0, 1.0, size=(n, 7) if vectorised else (7,))
        out = env.step(act if vectorised else act)
        _, reward, done, _ = out
        reward = np.atleast_1d(reward).astype(float)
        done = np.atleast_1d(done).astype(bool)
        max_r = np.maximum(max_r, reward)
        newly_done = done & live
        length[newly_done] = t + 1
        live &= ~done
        if not live.any():
            break
    return max_r, length


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--suite", default="libero_object")
    p.add_argument("--task-index", type=int, default=0)
    p.add_argument("--n-episodes", type=int, default=4)
    p.add_argument("--n-envs", type=int, default=2)
    p.add_argument("--max-steps", type=int, default=100)
    p.add_argument("--camera-size", type=int, default=128)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--condition", default="smoke-random")
    p.add_argument("--log", default="logs/table_a.jsonl")
    args = p.parse_args()

    from libero.libero import benchmark, get_libero_path

    suite = benchmark.get_benchmark_dict()[args.suite]()
    task = suite.get_task(args.task_index)
    bddl = os.path.join(
        get_libero_path("bddl_files"), task.problem_folder, task.bddl_file
    )
    print(f"[smoke_libero] task[{args.task_index}] = {task.name}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    commit = git_commit(REPO_ROOT)
    cfg_hash = config_hash(OmegaConf.create(vars(args)))
    rng = np.random.default_rng(args.seed)

    rows = []
    done_count = 0
    while done_count < args.n_episodes:
        n = min(args.n_envs, args.n_episodes - done_count)
        env, vectorised = build_env(n, bddl, args.camera_size)
        t0 = time.monotonic()
        max_r, length = run_batch(env, vectorised, n, args.max_steps, rng)
        wallclock = time.monotonic() - t0
        env.close()

        for i in range(n):
            seed = args.seed + done_count + i
            rows.append(
                {
                    "episode_id": f"{run_id}_{task.name}_{seed}",
                    "task_id": f"{args.suite}/{task.name}",
                    "seed": seed,
                    "condition": args.condition,
                    "disturbance_type": "none",
                    "disturbance_magnitude": None,
                    "disturbance_onset_step": None,
                    # LIBERO reward is sparse; success is reward 1.0. Logged as a
                    # float alongside the flag so the threshold stays recomputable,
                    # same decision as PushT (DECISIONS.md 2026-07-29).
                    "success_flag": bool(max_r[i] >= 1.0),
                    "max_reward": float(max_r[i]),
                    "episode_length": int(length[i]),
                    # No diffusion model in the loop: a random policy performs zero
                    # denoising and is re-queried every step. Both are measured, not
                    # estimated — SPEC.md forbids plausible-looking fill-ins.
                    "total_denoising_passes": 0,
                    "total_replans": int(length[i]),
                    "wallclock": wallclock,
                    "episodes_in_chunk": n,
                    "checkpoint_dir": None,
                    "git_commit": commit,
                    "config_hash": cfg_hash,
                }
            )
        done_count += n

    n_written = append_rows(REPO_ROOT / args.log, rows)
    print(f"[smoke_libero] wrote {n_written} Table A rows -> {args.log}")
    print(f"[smoke_libero] max_reward: {[round(r['max_reward'], 3) for r in rows]}")
    print(f"[smoke_libero] git_commit={commit} config_hash={cfg_hash}")


if __name__ == "__main__":
    # Must precede any env construction; see workaround 4 above.
    mp.set_start_method("spawn", force=True)
    main()
