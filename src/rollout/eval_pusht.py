"""Evaluate a released Diffusion Policy PushT low-dim checkpoint and emit
SPEC.md Table A rows.

WHY THIS EXISTS INSTEAD OF `external/diffusion_policy/eval.py`
--------------------------------------------------------------
DP's eval.py unpickles its config from inside the .ckpt, so hydra never runs and
there is NO override syntax. Every knob is frozen in a 1 GB pickle, including:

  * env_runner.n_envs = null  -> resolves to n_train + n_test = 56 subprocesses,
    each with its own pymunk sim. That will thrash an 8-core / 16 GB laptop.
  * policy.n_action_steps = 8 -> THE EXECUTION HORIZON. The entire project is
    about adapting this at runtime (PLAN.md M1).
  * policy.num_inference_steps = 100 -> denoising passes per call, the
    denominator of the compute-savings result.

So we own the loading path from day one rather than rewriting it in Week 11.

WHAT IS AND IS NOT MEASURED PER EPISODE
---------------------------------------
Episodes inside a vectorised chunk step in lockstep, so not everything separates
cleanly. Per SPEC.md, anything not genuinely measurable is logged as null rather
than estimated:

  * EXACT per-episode: success_flag, max_reward, episode_length,
    total_replans, total_denoising_passes. MultiStepWrapper.step() breaks
    immediately once an env is done, so a finished episode stops accumulating
    reward and stops consuming policy calls. Counting calls while each env is
    still active therefore attributes compute exactly.
  * SHARED across a chunk: wallclock. Episodes cannot be timed apart when
    stepped together. `episodes_in_chunk` records how many shared it so the
    ambiguity is never silently lost.

Usage:
  python src/rollout/eval_pusht.py \
      --checkpoint data/checkpoints/pusht_lowdim_cnn/epoch=0550-....ckpt \
      --n-test 5 --n-train 0 --n-envs 5
"""

import argparse
import math
import pathlib
import sys
import time
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
# DP has no __init__.py anywhere, so `pip install -e` would install an empty
# package (find_packages() returns []). Its own scripts use sys.path, so do we.
sys.path.insert(0, str(REPO_ROOT / "external" / "diffusion_policy"))
sys.path.insert(0, str(REPO_ROOT))

import dill  # noqa: E402
import hydra  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
import tqdm  # noqa: E402

from diffusion_policy.common.pytorch_util import dict_apply  # noqa: E402
from src.logging.rows import append_rows, config_hash, git_commit  # noqa: E402


def rollout(runner, policy, num_inference_steps):
    """Instrumented copy of PushTKeypointsRunner.run().

    Mirrors the upstream loop exactly, adding only per-episode accounting.
    Returns (all_rewards, per_episode_calls, chunk_meta).
    """
    env = runner.env
    n_envs = len(runner.env_fns)
    n_inits = len(runner.env_init_fn_dills)
    n_chunks = math.ceil(n_inits / n_envs)

    all_rewards = [None] * n_inits
    per_episode_calls = np.zeros(n_inits, dtype=np.int64)
    chunk_meta = [None] * n_inits

    for chunk_idx in range(n_chunks):
        start = chunk_idx * n_envs
        end = min(n_inits, start + n_envs)
        this_global_slice = slice(start, end)
        this_n_active_envs = end - start
        this_local_slice = slice(0, this_n_active_envs)

        this_init_fns = runner.env_init_fn_dills[this_global_slice]
        n_diff = n_envs - len(this_init_fns)
        if n_diff > 0:
            # pad the chunk; padded envs are discarded by this_local_slice
            this_init_fns.extend([runner.env_init_fn_dills[0]] * n_diff)
        assert len(this_init_fns) == n_envs

        env.call_each("run_dill_function", args_list=[(x,) for x in this_init_fns])

        obs = env.reset()
        past_action = None
        policy.reset()

        active_calls = np.zeros(n_envs, dtype=np.int64)
        done_arr = np.zeros(n_envs, dtype=bool)
        t0 = time.monotonic()

        # A run you cannot watch is a run you cannot debug. The call count is
        # hard-bounded by ceil(max_steps / n_action_steps), so this is a real
        # progress bar with a known denominator, not an open-ended spinner.
        max_calls = math.ceil(runner.max_steps / runner.n_action_steps)
        pbar = tqdm.tqdm(
            total=max_calls,
            desc=f"rollout chunk {chunk_idx + 1}/{n_chunks} (batch {n_envs})",
            dynamic_ncols=True,
        )

        while not np.all(done_arr):
            Do = obs.shape[-1] // 2
            np_obs_dict = {
                "obs": obs[..., : runner.n_obs_steps, :Do].astype(np.float32),
                "obs_mask": obs[..., : runner.n_obs_steps, Do:] > 0.5,
            }
            if runner.past_action and (past_action is not None):
                np_obs_dict["past_action"] = past_action[
                    :, -(runner.n_obs_steps - 1) :
                ].astype(np.float32)

            obs_dict = dict_apply(
                np_obs_dict, lambda x: torch.from_numpy(x).to(device=policy.device)
            )
            with torch.no_grad():
                action_dict = policy.predict_action(obs_dict)

            # An env that is already done breaks out of MultiStepWrapper.step()
            # without consuming anything, so only still-active envs are charged.
            active_calls[~done_arr] += 1

            np_action_dict = dict_apply(
                action_dict, lambda x: x.detach().to("cpu").numpy()
            )
            action = np_action_dict["action"][:, runner.n_latency_steps :]

            obs, reward, done_arr, info = env.step(action)
            done_arr = np.asarray(done_arr, dtype=bool)
            past_action = action

            pbar.update(1)
            pbar.set_postfix_str(f"{int(done_arr.sum())}/{n_envs} episodes done")

        pbar.close()
        elapsed = time.monotonic() - t0
        all_rewards[this_global_slice] = env.call("get_attr", "reward")[this_local_slice]
        per_episode_calls[this_global_slice] = active_calls[this_local_slice]
        for i in range(start, end):
            chunk_meta[i] = {"wallclock": elapsed, "episodes_in_chunk": this_n_active_envs}

    return all_rewards, per_episode_calls, chunk_meta


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--output-dir", default="data/eval_output")
    p.add_argument("--log", default="logs/table_a.jsonl")
    p.add_argument("--n-test", type=int, default=5)
    p.add_argument("--n-train", type=int, default=0)
    p.add_argument("--n-envs", type=int, default=5)
    p.add_argument("--n-test-vis", type=int, default=0)
    p.add_argument("--n-train-vis", type=int, default=0)
    p.add_argument("--device", default="cpu")
    p.add_argument("--condition", default="eval")
    args = p.parse_args()

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = pathlib.Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = torch.load(open(args.checkpoint, "rb"), pickle_module=dill, map_location="cpu")
    cfg = payload["cfg"]

    # The whole reason this file exists: these live inside the checkpoint.
    er = cfg.task.env_runner
    er.n_envs = args.n_envs
    er.n_test = args.n_test
    er.n_train = args.n_train
    er.n_test_vis = args.n_test_vis
    er.n_train_vis = args.n_train_vis

    cls = hydra.utils.get_class(cfg._target_)
    workspace = cls(cfg, output_dir=str(output_dir))
    workspace.load_payload(payload, exclude_keys=None, include_keys=None)

    policy = workspace.ema_model if cfg.training.use_ema else workspace.model
    policy.to(torch.device(args.device))
    policy.eval()

    num_inference_steps = cfg.policy.num_inference_steps
    runner = hydra.utils.instantiate(er, output_dir=str(output_dir))

    print(
        f"[eval_pusht] run_id={run_id} n_train={args.n_train} n_test={args.n_test} "
        f"n_envs={args.n_envs} device={args.device} "
        f"num_inference_steps={num_inference_steps}",
        flush=True,
    )

    t_start = time.monotonic()
    all_rewards, per_episode_calls, chunk_meta = rollout(runner, policy, num_inference_steps)
    total_elapsed = time.monotonic() - t_start

    commit = git_commit(REPO_ROOT)
    cfg_hash = config_hash(cfg)
    ckpt_dir = str(pathlib.Path(args.checkpoint).resolve())

    rows = []
    scores = {}
    for i, rewards in enumerate(all_rewards):
        prefix = runner.env_prefixs[i].rstrip("/")  # 'train' | 'test'
        seed = int(runner.env_seeds[i])
        max_reward = float(np.max(rewards))
        calls = int(per_episode_calls[i])
        scores.setdefault(prefix, []).append(max_reward)
        rows.append(
            {
                "episode_id": f"{run_id}_{prefix}_{seed}",
                "task_id": "pusht",
                "seed": seed,
                "condition": args.condition,
                "disturbance_type": "none",
                "disturbance_magnitude": None,
                "disturbance_onset_step": None,
                # PushT reward is clip(coverage/0.95, 0, 1); success is
                # coverage >= 0.95, i.e. max_reward >= 1.0.
                "success_flag": bool(max_reward >= 1.0),
                "max_reward": max_reward,
                "episode_length": len(rewards),
                "total_denoising_passes": calls * int(num_inference_steps),
                "total_replans": calls,
                "wallclock": chunk_meta[i]["wallclock"],
                "episodes_in_chunk": chunk_meta[i]["episodes_in_chunk"],
                "checkpoint_dir": ckpt_dir,
                "git_commit": commit,
                "config_hash": cfg_hash,
            }
        )

    n = append_rows(REPO_ROOT / args.log, rows)

    print(f"\n[eval_pusht] wrote {n} Table A rows -> {args.log}")
    print(f"[eval_pusht] total wallclock {total_elapsed:.1f}s")
    for prefix, vals in scores.items():
        succ = sum(v >= 1.0 for v in vals)
        print(
            f"[eval_pusht] {prefix}: mean_score={np.mean(vals):.4f}  "
            f"success_rate={succ}/{len(vals)}"
        )


if __name__ == "__main__":
    main()
