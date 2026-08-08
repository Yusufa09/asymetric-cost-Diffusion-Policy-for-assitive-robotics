# SETUP

How to reproduce the environment from scratch. **Update whenever the environment
changes** — pinned commits, new dependencies, checkpoint locations, cloud config.

> **Status: Steps 1–3 executed and working as of 2026-07-29** on the MacBook Air
> (arm64, 8 cores, 16 GB). Steps 4+ are still the planned procedure. Where a step
> has been run, the recorded commands are the ones that *actually* worked,
> including workarounds.

---

## Repo layout

```
context/     project context — read CLAUDE.md for the index
src/
  rollout/     wrapper over DP/LIBERO rollout loops
  logging/     schema emitter (Tables A/B/C from SPEC.md)
  disturbances/  empty until Phase 1
  cost/        empty until Phase 3
configs/
external/    diffusion_policy/ is VENDORED (committed); everything else gitignored
logs/        gitignored — raw JSONL/CSV rows land here
```

**Vendoring policy: full copies, not submodules, opt-in per repo.**
*(Revised 2026-07-29 — this section previously said "pinned clones, gitignored.")*

Submodules stay rejected for the original reasons: detached HEAD, forgotten
`--recursive`, sync headaches. But a **recorded hash is only a reference**, and a
reference dies if upstream is deleted or force-pushed. Experiments run to January
2027 and the fair is March 2027, so the code must survive independently of anyone
else's repository.

So: **Diffusion Policy is committed to this repo in full** — 369 files, 31 MB, at
upstream commit `5ba07ac6661db573af695b419a7947ecb704690f`, MIT licensed with the
LICENSE file retained. Its nested `.git` was removed before staging; leaving it in
place would have made git record a **gitlink (mode 160000)** — an accidental
submodule, the exact thing this policy rejects. **If you vendor another repo,
delete its `.git` first and confirm `git ls-files` shows real paths, not a single
160000 entry.**

`.gitignore` ignores `external/*` and un-ignores vendored repos **one line at a
time**. Do not replace that with a blanket un-ignore: LIBERO ships ~100 GB of
demonstration data and a blanket rule would try to commit it. If LIBERO is
vendored later, vendor the *code* only.

**Never edit the vendored tree.** Wrap or subclass from `src/` instead. An edit
inside `external/` is invisible in review, unattributable, and voids the guarantee
that this is upstream code at a known commit. See `external/README.md`.

## Environment strategy

**Two separate conda environments** with a thin rollout/logging wrapper above both.

DP is pinned to an old stack (Python 3.9, old gym, a specific mujoco, robomimic,
pygame for the PushT renderer). LIBERO has its own stack (robosuite + mujoco) that
conflicts. Forcing them into one env is a known source of pain and buys nothing.

Use **conda, not bare venv** — the mujoco/mesa/GL dependencies resolve far more
reliably through conda. On Apple Silicon expect friction with mujoco and pygame
specifically. **That is the known tax, not you doing something wrong.**

## Step 1 — Diffusion Policy

```bash
git clone --depth 1 https://github.com/real-stanford/diffusion_policy.git external/diffusion_policy
mamba env create -f external/diffusion_policy/conda_environment_macos.yaml
# then the two fixes below — the env is NOT usable without them
mamba remove -n robodiff accelerate -y
mamba install -n robodiff -c conda-forge "huggingface_hub=0.25.2" -y
```

**Use `conda_environment_macos.yaml`, not `conda_environment.yaml`.** The latter
is the CUDA/linux env and cannot solve on osx-arm64. Both create an env named
`robodiff`.

**Done when** this prints `ALL OK` — note that `import diffusion_policy` alone
proves nothing, because DP ships no `__init__.py` and resolves as an implicit
namespace package even when every dependency is broken:

```bash
mamba run -n robodiff python -c "
import sys; sys.path.insert(0, 'external/diffusion_policy')
import torch, gym, pymunk, pygame, hydra, dill
from diffusers.schedulers.scheduling_ddpm import DDPMScheduler
from diffusion_policy.workspace.train_diffusion_unet_lowdim_workspace import TrainDiffusionUnetLowdimWorkspace
from diffusion_policy.env_runner.pusht_keypoints_runner import PushTKeypointsRunner
print('ALL OK', torch.__version__)"
```

- Pinned commit: `5ba07ac6661db573af695b419a7947ecb704690f`
- Installed size: env 1.6 GB (under miniforge, *not* in this repo) + 31 MB clone
- Actual install notes / workarounds (2026-07-29):
  1. **The conda half solves cleanly on osx-arm64** — 310 packages, 316 MB. The
     Apple-Silicon friction this file warned about did not materialize there.
     torch 1.12.1 (CPU), gym 0.21.0, pymunk, av all resolve.
  2. **The pip half fails**, and `mamba env create` exits 1 — but the conda env
     is already fully built at that point, so this is "run two more commands,"
     not "start over." `imagecodecs==2022.9.26` fails to compile (missing
     `libheif/heif.h`). **Ignore it**: it is imported only by `real_world/` and
     the robomimic *image* dataset, neither of which this project touches. Same
     for `robomimic`, `r3m`, `pytorchvideo`, `atomics`, `ray` — none are
     imported anywhere on the PushT low-dim path. `pygame` is the only pip
     package that matters and it installs before the failure.
  3. **`accelerate` must be removed.** The osx-arm64 CPU torch build ships
     without `torch.distributed`, so `accelerate` 0.13.2 dies on
     `from torch.distributed import ReduceOp` — and `diffusers` imports
     accelerate on the scheduler path. `diffusers` guards it behind
     `is_accelerate_available()`, which only checks that the package *exists*;
     deleting it makes the check return False and diffusers works. DP itself
     never imports accelerate.
  4. **`huggingface_hub` must be pinned to 0.25.2.** It is unpinned in the yaml,
     so conda installs 0.31.4, which removed `cached_download` — a symbol
     `diffusers` 0.11.1 still imports. 0.25.2 is the newest release that keeps
     it, so the downgrade stays minimal. This is the classic failure mode of an
     old pinned stack with an unpinned transitive dependency, and it will
     recur: **if this env breaks in November, suspect an unpinned dep drifting,
     not your code.**

**Escape hatch:** if `robodiff` fights you for more than an hour, Hugging Face's
**LeRobot** is a maintained modern reimplementation with a pip-installable PushT
checkpoint and a clean eval script. Try the canonical repo first — the plan is
built around it — but don't burn a day on dependency resolution.

## Step 2 — PushT checkpoint eval (do NOT train yet)

**This is the single most important tactical move in Phase 0.** Evaluate a
released checkpoint *before* training anything. It decouples two questions that
are otherwise tangled:

- "Can I run a rollout end-to-end and get a success/fail flag?" → answered by
  checkpoint eval, no training required.
- "Can I train to published success rate?" → the Week 4 gate, purely a compute
  question once the pipe works.

Grab a **low-dim (state-based)** PushT checkpoint from
`diffusion-policy.cs.columbia.edu/data/experiments/low_dim/pusht/` — state-based,
**not** image-based, because image-based effectively needs a GPU and low-dim runs
fine on CPU.

**Do not use `external/diffusion_policy/eval.py`.** It unpickles its config from
inside the `.ckpt`, so hydra never runs and there is no override syntax — every
knob is frozen in a 1 GB pickle, including `n_envs`, `n_test`, and
`policy.n_action_steps` (the execution horizon this entire project adapts). Use
`src/rollout/eval_pusht.py`, which loads the same payload and patches the config
before instantiating anything. It also emits Table A rows, so Steps 2 and 3
collapse into one command.

- Checkpoint used:
  `data/checkpoints/pusht_lowdim_cnn/epoch=0550-test_mean_score=0.969.ckpt`
  (1,044,185,793 bytes, from `.../low_dim/pusht/diffusion_policy_cnn/train_0/checkpoints/`)
- Exact eval command that worked (2026-07-29):

```bash
mamba run -n robodiff python src/rollout/eval_pusht.py \
  --checkpoint "data/checkpoints/pusht_lowdim_cnn/epoch=0550-test_mean_score=0.969.ckpt" \
  --n-test 2 --n-train 0 --n-envs 2
```

- Smoke test (2 episodes): **2/2 success, mean_score 1.0000, 106.5 s wall.**
- **Full reproduction — PASSED (2026-07-29).** 50 test episodes, CPU:

```bash
mamba run -n robodiff python src/rollout/eval_pusht.py \
  --checkpoint "data/checkpoints/pusht_lowdim_cnn/epoch=0550-test_mean_score=0.969.ckpt" \
  --n-test 50 --n-train 6 --n-envs 56
```

  | | |
  |---|---|
  | observed `test/mean_score` | **0.9453** (n=50, sd 0.194, se 0.027) |
  | published | 0.9690 |
  | gap | +0.0237 = **0.87 standard errors** |
  | 95% CI | **[0.8916, 0.9990]** — contains the published value |
  | wall clock | 8790.9 s (2 h 26 m), 56 rows written |

  The residual gap needs no explaining away: **DDPM sampling noise is unseeded**,
  and the published run was CUDA while this is CPU, so the RNG streams differ
  entirely. Same initial conditions, different sampling noise. If an exact-match
  reproduction is ever needed, the policy's sampling RNG must be seeded — it
  currently is not, which also means **repeat runs of this command will not be
  bit-identical.** That is fine for a mean over 50 episodes and would not be fine
  for debugging a single trajectory.

  Max `total_replans` observed was **38**, exactly the structural ceiling:
  `ceil(max_steps / n_action_steps) = ceil(300/8)`. Useful as a sanity check —
  if a future run exceeds it, termination is broken.
- **The bottleneck is entirely policy inference.** Env subprocesses sit at ~0% CPU
  and cost ~12 MB each, so **`n_envs` is a throughput knob, not a memory risk** —
  56 workers run fine on a 16 GB machine and raise driver utilisation from ~200%
  to ~650% CPU.

> **Do not read high CPU% as high throughput.** An earlier version of this file
> concluded "prefer one big chunk" from the utilisation number alone. That was
> wrong: the extra CPU was doing more *work*, not more *episodes*. Two effects
> push in opposite directions and only one of them is measured:
>
> 1. **Straggler waste — MEASURED at 25.5%.** The loop calls the policy on the
>    whole batch until the *last* episode finishes, so early finishers keep paying.
>    From the logged rows: 1586 batch-elements were actually needed, 2128 were
>    paid for (38 calls × 56 envs). Ideal speedup from eliminating this: **1.34×**.
>    It grows with the spread of episode lengths — here 20/50 episodes ran the
>    full 300 steps while the shortest took 79.
> 2. **Per-sample batch efficiency — MEASURED at 1.25× worse.** Large batches are
>    memory-bandwidth bound on this CPU. Timed per policy call:
>
>    | `n_envs` | s / call | s per episode-slot |
>    |---|---|---|
>    | 1 | 3.30 (stable over 35 calls) | **3.30** |
>    | 56 | 231.3 (8790.9 s / 38 calls) | **4.13** |
>
> **Combined, small `n_envs` wins on CPU: 1.34 × 1.25 ≈ 1.68×.** Sequential
> `n_envs=1` over the same 56 episodes projects to 1586 calls × 3.30 s ≈ **1 h 27 m**
> against the **2 h 26 m** actually spent at `n_envs=56`. So for a CPU run, prefer
> *small* chunks — the opposite of what this file said before.
>
> Caveats: the batch-1 figure comes from a single episode (per-call time was steady,
> but episode-to-episode variation is unmeasured), and this is one machine. **On GPU
> the tradeoff very likely reverses** — a GPU is starved at batch 1 and the straggler
> waste would be cheap next to the parallelism gain. Measure before assuming, and do
> not infer throughput from CPU%.

**Wrap any local run longer than a few minutes in `caffeinate`.** macOS sleeping
mid-run suspended a 25-minute evaluation on 2026-07-29. It survived (the process
resumed on wake) but that is luck, not design, and nothing is written until the
run ends — a sleep that turns into a shutdown loses the whole run:

```bash
caffeinate -is mamba run -n robodiff python src/rollout/eval_pusht.py ...
```

**Provenance trap, recorded because it would be very expensive to rediscover:**
the `config.yaml` published alongside the checkpoints says
`test_start_seed: 100000`, but the config *inside* the checkpoint says
**`4300000`** (with `training.seed: 42`). They disagree. **The checkpoint is the
authority** — `eval_pusht.py` reads from the payload, so it gets this right
automatically, but anything that reconstructs a config from the published YAML
will silently evaluate different initial conditions and then fail to reproduce
the published score for reasons that look like a bug in your code.

## Step 3 — Emit one Table A row

**Done — folded into Step 2.** `src/rollout/eval_pusht.py` writes Table A rows to
`logs/table_a.jsonl` via `src/logging/rows.py`, which validates every row against
the schema at write time (a typo raises instead of silently dropping a column).

Two schema decisions made here, both additive to `SPEC.md` Table A:

- **`success_flag` needed a definition and now has one.** PushT's env reward is
  `clip(coverage / 0.95, 0, 1)` and success is coverage ≥ 95%, i.e.
  `max_reward >= 1.0`. **The published 0.969 is a mean *score*, not a success
  rate** — do not compare it against a success percentage. `max_reward` is
  logged as its own float field so any success threshold stays recomputable.

> **⚠ Threshold sensitivity — carry this into Phase 1, and into `SPEC.md` at the
> Phase-3 gate (do not edit `SPEC.md` before then; its update trigger is Phase 3).**
>
> The same 50 episodes give **mean_score 0.9453** and **success rate 30/50 = 60%**.
> Both are correct. The distribution is bimodal with a third of episodes parked
> just below the cutoff:
>
> | bucket | n |
> |---|---|
> | `= 1.0` (coverage ≥ 95%, success) | 30 |
> | `0.9–1.0` (≈85–95% coverage, near-miss) | **17** |
> | `0.5–0.9` | 0 |
> | `< 0.5` (real failure, min 0.023) | 3 |
>
> **Why this is a risk, not a curiosity:** `success_flag` is the binary that feeds
> the asymmetric cost model, and the 0.95 coverage cutoff was inherited from IBC,
> not chosen. With 17/50 episodes within ten points of it, a disturbance that
> shifts coverage slightly could swing the success *rate* by ~20 points while
> barely moving mean_score — making downstream recovery-utility claims look far
> more (or less) dramatic than the underlying effect. A judge can ask "why 0.95?"
> and the answer cannot be "it came with the environment."
>
> Compounding it: **20/50 episodes hit the 300-step truncation**, so episode
> length is censored and the binary is doing more work than it appears.
>
> Mitigation already in place: `max_reward` is logged per episode, so every
> threshold stays recomputable forever. What is still owed is a **success-threshold
> sensitivity sweep**, run alongside the Phase-3 cost-ratio sweep — same shape of
> analysis, same figure logic. This is cheap insurance against the headline
> resting on an arbitrary constant.
- **`wallclock` is per-chunk, not per-episode**, because vectorised episodes step
  in lockstep and cannot be timed apart. `episodes_in_chunk` is logged alongside
  it so that ambiguity is never lost. Everything else is exact per-episode:
  `MultiStepWrapper.step()` breaks immediately once an env is done, so a finished
  episode stops accruing both reward and policy calls — which is what makes
  `total_replans` and `total_denoising_passes` genuinely per-episode rather than
  chunk-averaged.

**Note on `src/logging/`:** that package name shadows the stdlib `logging` module
if `src/` itself is ever put on `sys.path`. Always put the repo root on the path
and import `src.logging.rows`. Never add `src/` directly.

## Step 4 — LIBERO (Week 2/3)

Separate conda env. **Code only on this laptop** — the ~100 GB of demonstration
HDF5 belongs on the GPU instance. Do not run `download_libero_datasets.py` here.

```bash
git clone --depth 1 https://github.com/Lifelong-Robot-Learning/LIBERO.git external/LIBERO
```

- Pinned commit: `8f1084e3132a39270c3a13ebe37270a43ece2a01` (2025-03-15, HEAD of
  `main` at clone time 2026-08-02). Repo appears unmaintained since then.
- **VENDORED 2026-08-02** — committed in full, same policy as Diffusion Policy.
  **426 MB, 1116 files**, MIT (© 2023 Lifelong Robot Learning), LICENSE retained,
  nested `.git` removed before staging. Details in `external/README.md`.
- 404 MB of the 426 is `libero/libero/assets` (MuJoCo meshes/textures). Those are
  vendored deliberately: without them the sim does not run, so "code only" means
  *not the demo datasets*, not *not the assets*.
- **Datasets are not vendored and must never be.** Two guards on
  `external/LIBERO/libero/datasets/` — LIBERO's own nested `.gitignore`, and an
  explicit line in the top-level `.gitignore`. The second is the one that counts.
- **Bug found while vendoring, fixed:** the top-level `.gitignore` rule `data/`
  was unanchored, so it matched a directory named `data` at *any* depth and
  silently dropped `libero/configs/data/default.yaml` — the file this section
  cites for obs modalities and `obs_key_mapping`. Anchored to `/data/`. **After
  vendoring anything, diff files-on-disk against files-staged**; the command is in
  `external/README.md`. Diffusion Policy was checked at the same time and is
  clean — its 28 uncommitted files are all `__pycache__/*.pyc`.

### Observation / action space — VERIFIED 2026-08-02 by reading the code

No robosuite install was needed for any of this; it is all readable from the repo.

| | |
|---|---|
| robot / controller | Panda, `OSC_POSE` (`libero/libero/envs/env_wrapper.py:16-17`) |
| action dim | **7** — 6 OSC delta-pose + 1 gripper. Hard-coded in the eval loop's dummy action, `libero/lifelong/metric.py:120` |
| cameras | `agentview` + `robot0_eye_in_hand`, **128×128** (`env_wrapper.py:31-36`) |
| obs keys used | rgb `agentview_rgb`, `eye_in_hand_rgb`; low-dim `gripper_states` (2), `joint_states` (7) (`libero/configs/data/default.yaml:25-34`) |
| control freq | 20 Hz, default `horizon` 1000 (`env_wrapper.py:27-28`) |

**There is no low-dim-only path.** Unlike PushT, every LIBERO rollout renders two
128×128 camera streams, so **every LIBERO rollout costs GPU**. The CPU-local
prototyping tier ends at PushT. This changes the per-rollout cost assumption
behind the ~130 GPU-hr figure and should be remeasured on the first real run.

### Two mechanisms already present that this project needs

Both found in `libero/libero/envs/env_wrapper.py` — worth knowing before writing
anything in `src/disturbances/`:

- **`get_sim_state()` → `env.sim.get_state().flatten()`** (line 118). This is
  exactly the MuJoCo sim-state snapshot that `intermediate_state_ref` was
  deferred to point at (see § Backing up raw results). The deferred decision is
  directly implementable; no rendered frames needed.
- **`set_state()` / `regenerate_obs_from_state()`** (lines 127-145) — set flattened
  MuJoCo state, `sim.forward()`, re-derive observables. **This is the object-shift
  injector primitive**: read state, displace the target object's qpos, write it
  back mid-episode.

### Task IDs — suites enumerated, three not yet chosen

Canonical index order comes from `libero/libero/benchmark/libero_suite_task_map.py`,
**not** from `bddl_files/*/tasks_info.txt` — the two orderings differ, and the map
is what indexes into published per-suite results. Verified index → name:

| idx | `libero_object` (all 10 identical template) | `libero_goal` |
|---|---|---|
| 0 | pick_up_the_alphabet_soup_and_place_it_in_the_basket | **open_the_middle_drawer_of_the_cabinet** |
| 1 | pick_up_the_cream_cheese_… | put_the_bowl_on_the_stove |
| 2 | pick_up_the_salad_dressing_… | put_the_wine_bottle_on_top_of_the_cabinet |
| 3 | pick_up_the_bbq_sauce_… | **open_the_top_drawer_and_put_the_bowl_inside** |
| 4 | pick_up_the_ketchup_… | put_the_bowl_on_top_of_the_cabinet |
| 5 | pick_up_the_tomato_sauce_… | push_the_plate_to_the_front_of_the_stove |
| 6 | pick_up_the_butter_… | put_the_cream_cheese_in_the_bowl |
| 7 | pick_up_the_milk_… | turn_on_the_stove |
| 8 | pick_up_the_chocolate_pudding_… | put_the_bowl_on_the_plate |
| 9 | pick_up_the_orange_juice_… | put_the_wine_bottle_on_the_rack |

**The three planned framings do not map cleanly, and this is a real finding, not
a lookup failure:**

- **drawer/container opening → exact match.** `libero_goal[0]
  open_the_middle_drawer_of_the_cabinet`, or `libero_goal[3]` for the
  open-then-place variant.
- **handover → does not exist.** LIBERO has no handover task in any suite. The
  nearest framing is pick-and-place into a receptacle (basket / tray / plate).
- **retrieve-dropped-object → does not exist.** No dropped-object task. Nearest
  is retrieval *from a container*: `libero_spatial[4]
  pick_up_the_black_bowl_in_the_top_drawer_of_the_wooden_cabinet_and_place_it_on_the_plate`.
- **All 10 `libero_object` tasks are one template** differing only in the target
  grocery item, so "handover" and "retrieve-dropped" drawn from that suite would
  be *the same task twice*. Choosing both there would quietly collapse the
  3-task diversity claim.

### Suite choice — RESOLVED 2026-08-02: `libero_object`, per-suite training

**The three tasks are deliberately still `TBD`.** They get picked from the
*measured* per-task success rates the gate run produces (see below), not chosen in
advance. Full reasoning in `DECISIONS.md` 2026-08-02.

**The fact that decided it — DP has no language conditioning**, so a per-suite
policy can only tell its 10 tasks apart from the image. Verified by diffing
`(:objects` and `(:fixtures` blocks:

| suite | problem | fixtures | tasks distinguishable from image? | DP |
|---|---|---|---|---|
| `libero_object` | **`LIBERO_Floor_Manipulation`** | `floor` | **yes** — different object set per task | **92.5** |
| `libero_spatial` | `LIBERO_Tabletop_Manipulation` | table, cabinet, stove | partly — two identical black bowls | 78.3 |
| `libero_goal` | `LIBERO_Tabletop_Manipulation` | table, cabinet, stove, wine rack | **no** — all 10 share one scene and one object set `{bowl, cream cheese, wine bottle, plate}` | 68.3 |
| `libero_10` | 8 distinct scenes | varies | yes | 50.5 |

**The published ranking is this property, not task difficulty.** And it is
load-bearing here: the control signal is inter-chunk consistency, so on a
goal-ambiguous suite the policy is legitimately multimodal *with no disturbance
present* — inflating nominal inconsistency, inflating the conformal threshold
calibrated on nominal rollouts, and making disturbance indistinguishable from the
policy never having known which task it was doing.

**Training recipe matters as much as suite choice.** DP trains **one policy per
suite** (one set of weights, ~500 demos, all 10 tasks), which is what produced the
published numbers. The ambiguity confound is a property of *that recipe*, not of
the tasks — a single-task policy has one goal and no ambiguity, and a hand-picked
cross-suite trio would be visually disambiguable (Object is a floor scene, the
others are tabletop). Both alternatives were priced and rejected on budget, not
correctness; see `DECISIONS.md`.

**Consequence to own out loud:** all 10 `libero_object` tasks are one template, so
the three tasks are three grocery items, not three skills. **The generality axis is
PushT vs. LIBERO** — 2D planar pushing, keypoint obs, 2-dim actions versus 7-DoF
manipulation from 128×128 RGB — not LIBERO task variety.

### Perturbation-harness audit — DONE 2026-08-02. Verdict: build the injector.

Both extensions exist and both perturb **only at episode initialization**.
Neither injects a disturbance mid-execution, which is this project's entire
premise, so neither can be adopted as the injector.

| | LIBERO-Plus | LIBERO-PRO |
|---|---|---|
| paper | [arXiv 2510.13626](https://arxiv.org/abs/2510.13626) | [arXiv 2510.03827](https://arxiv.org/abs/2510.03827) |
| code | `github.com/sylvestf/LIBERO-plus` | `github.com/Zijian007/LIBERO-PRO` |
| dimensions | objects layout, camera viewpoint, robot init state, language, lighting, background texture, sensor noise (7) | manipulated objects, initial states, instructions, environments (4) |
| scale | 10,030 eval tasks across the 4 suites | — |
| timing | **initialization only** | **initialization only** |

What the audit actually bought, which is not nothing:

1. **The 2-week Phase-1 compression does not happen.** PLAN §3 Wk 5 assumed a
   harness might be adoptable. It is not. Budget the injector in full.
2. **LIBERO-Plus O2 "Target Object Pose"** randomizes the target object's initial
   (x,y,z) + (pitch,yaw,roll) "by modifying the Problem class interface." That is
   reusable *code* for computing and applying an object displacement — pair it
   with `regenerate_obs_from_state()` above to move the displacement mid-episode.
   O1 adds distractor objects by editing BDDL files; not needed here.
3. **Neither implements occlusion or delayed observation.** LIBERO-Plus's camera /
   lighting / texture / sensor-noise axes are appearance perturbations, not
   occlusion of the target object. Both remain to be built.
4. **The prior-work distinction gets sharper, with citations.** The two 2025
   robustness benchmarks perturb the *initial condition* and measure whether the
   policy still succeeds. This project perturbs *during execution* and measures
   whether the policy notices in time to change what it commits to. Worth adding
   to `PLAN.md` §9 as a rebuttal answer.

### Published Diffusion-Policy-on-LIBERO numbers — the Phase-0 gate problem

Searched 2026-08-02. **No released Diffusion Policy LIBERO checkpoint was found**
in the sources checked (OpenVLA-OFT, LeRobot model hub — which ships
`lerobot/diffusion_pusht`, `lerobot/pi0_libero_base`, `lerobot/pi05_libero_base`,
`lerobot/xvla-libero`, but no DP-LIBERO). Treat as "not found," not "proven
absent" — but plan as if training is required.

The commonly-cited DP baseline is **78.3 / 92.5 / 68.3 / 50.5** (Spatial /
Object / Goal / Long), reported in
[OpenVLA-OFT Table I](https://arxiv.org/html/2502.19645v1), attributed there to
Kim et al., **trained from scratch**. Protocol: **10 tasks × 50 episodes = 500
trials, reported as a per-suite average.**

**Three reasons the Phase-0 gate is not checkable as written** ("DP reproduces
published success rates on all three LIBERO tasks"):

1. **No per-task published numbers exist** — only per-suite averages over all 10.
2. **No released checkpoint** — "reproduce" means *train DP on LIBERO first*.
3. **A 3-task subset spanning two suites** has no published comparison at all.

**Gate as rewritten 2026-08-02:** train DP on the **`libero_object` suite**,
evaluate **all 10 tasks × 50 episodes**, and pass if the **suite average is within
±5 points of 92.5%** — band declared here, before looking, because deciding what
"close enough" means after seeing the number is how a gate stops being a gate.
PushT precedent: 0.9453 vs 0.969 published, 0.87 SE, accepted.

Evaluating 10 tasks rather than 3 costs **rollouts only, not extra training** —
the per-suite policy already covers all 10. And per-task success rates fall out
for free: 500 Table A rows tagged by task, grouped in post-processing. That
readout is what picks the three tasks, so **do not name them before this run.**

### First GPU session — measure before training

The two numbers this project's feasibility rests on are both **estimates**:
~$1.5/hr and ~130 GPU-hr. Neither has been measured. Before committing to a
training run, time **one rollout and one training epoch**. ~20 minutes, and it
also settles the `n_envs` question — the CPU measurement favoured small batches
(1.68×, `SETUP.md` § Step 2) and that very likely reverses on an A10G starved at
batch 1. Measure; do not infer throughput from CPU%.

## Step 5 — EC2 instance + LIBERO env — EXECUTED 2026-08-04, WORKS

**Status: verified working end to end.** A LIBERO env builds, resets, renders two
128×128 RGB streams, and steps a 7-dim action on the GPU. Commands below are the
ones that *actually ran*, including three workarounds the README does not mention.

### The instance

| | |
|---|---|
| type | `g5.2xlarge`, `us-east-1` |
| **instance ID** | `TBD` — read off EC2 → Instances and record it. The Name tag `libero-gpu` is enough to restart from the console, but the ID is what AWS CLI and support cases key on |
| AMI | `ami-04496a4d4cc3ce989` — *Deep Learning Base AMI with Single CUDA (Ubuntu 24.04)* |
| GPU | **NVIDIA A10G, 23028 MiB**, driver `595.71.05` |
| CUDA (system) | 13.2 — **irrelevant**, pip's torch bundles its own runtime; only the driver version matters |
| OS / user | Ubuntu 24.04.4 LTS / `ubuntu` |
| root volume | 100 GiB gp3 → 96 G usable, 18 G used by the AMI, **78 G free** |
| instance store | `nvme1n1`, **419 G**, unmounted, **free** — ephemeral scratch, wiped on stop |

**AMI trap.** Searching "Deep Learning Base OSS" in the console lands you in
**AWS Marketplace AMIs**, which returns third-party repackages (e.g. "Galaxys
Cloud") carrying a **software surcharge of $2.40–3.20/hr on top of EC2**. That
would roughly triple the burn rate. Official AWS images are owned by `amazon`
and have **no software cost line**. Verify owner and price before selecting.

**Free-tier trap.** The post-2025-07 AWS **Free Plan blocks GPU instance types
entirely** — `g5.2xlarge` is not launchable on it. Upgrading to the Paid Plan is
required, credits carry over to their original expiry, and credits are consumed
before the card. **But the Free Plan's auto-close-on-credit-depletion is what
made overspend structurally impossible; upgrading removes that.** A Budgets
*Action* that auto-stops EC2 is the only guard that enforces rather than notifies.

### Install — the commands that worked

```bash
# 1. miniconda (not preinstalled on this AMI)
curl -fsSL -o mc.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash mc.sh -b -p $HOME/miniconda3 && $HOME/miniconda3/bin/conda init bash

# 2. env — NOTE the channel override, see workaround 1
conda create -n libero python=3.8.13 -y -c conda-forge --override-channels

# 3. LIBERO at the pinned commit
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git ~/LIBERO
cd ~/LIBERO && git checkout 8f1084e3132a39270c3a13ebe37270a43ece2a01

# 4. deps  (writes ~/.libero/config.yaml FIRST — see workaround 2)
~/miniconda3/envs/libero/bin/pip install -r requirements.txt
~/miniconda3/envs/libero/bin/pip install -e .
```

Clone is **743 MB** on Linux (vs 650 MB on macOS — filesystem block size).

### Three workarounds the README does not mention

1. **Anaconda ToS blocks `conda create`.** The default channels
   (`repo.anaconda.com/pkgs/main`) now require accepting a Terms of Service
   agreement, and `conda create` fails with a ToS error until you do. **Fixed
   with `-c conda-forge --override-channels`** — no agreement to accept, and
   conda-forge carries no commercial-use restriction. Preferred over
   `conda tos accept` on both legal and reproducibility grounds.

2. **⚠ LIBERO calls `input()` on first import and will HANG.**
   `libero/libero/__init__.py:71` prompts *"Do you want to specify a custom path
   for the dataset folder? (Y/N)"* when `~/.libero/config.yaml` is absent. Over a
   non-interactive SSH session this hangs with no output and no error — it looks
   like a crash, not a prompt. **Pre-write the config so the branch never runs:**

   ```bash
   mkdir -p ~/.libero && cat > ~/.libero/config.yaml <<EOF
   benchmark_root: /home/ubuntu/LIBERO/libero/libero
   bddl_files: /home/ubuntu/LIBERO/libero/libero/bddl_files
   init_states: /home/ubuntu/LIBERO/libero/libero/init_files
   datasets: /home/ubuntu/LIBERO/libero/datasets
   assets: /home/ubuntu/LIBERO/libero/libero/assets
   EOF
   ```

3. **`MUJOCO_GL=egl` is mandatory, and it fails silently.** The instance has no
   display. Without it, rendering either errors on GL init or — worse — returns
   an all-black image that passes every shape assertion. **Always assert on pixel
   content, never on shape.** Put `export MUJOCO_GL=egl` in `~/.bashrc`.

### torch: 2.4.1 kept, README's 1.11.0+cu113 NOT installed

`requirements.txt` does not pin torch, so pip resolved **torch 2.4.1+cu121**
(pulled by `robomimic`). LIBERO's README then says to install `1.11.0+cu113`.
**We tested 2.4.1 first and it works**, so the downgrade was skipped — see
`DECISIONS.md` 2026-08-04.

Note `gym 0.25.2` emits an unmaintained/NumPy-2.0 warning on import. Harmless
here — numpy is pinned to 1.22.4.

### Done-when test — passed 2026-08-04

Importing `libero` proves nothing (as with DP in Step 1). The real test builds an
env, resets, and **asserts on pixel content**:

```python
import os; os.environ["MUJOCO_GL"] = "egl"
import numpy as np, torch
from libero.libero import benchmark, get_libero_path
from libero.libero.envs import OffScreenRenderEnv
bd = benchmark.get_benchmark_dict()["libero_object"]()
task = bd.get_task(0)
bddl = os.path.join(get_libero_path("bddl_files"), task.problem_folder, task.bddl_file)
env = OffScreenRenderEnv(bddl_file_name=bddl, camera_heights=128, camera_widths=128)
env.seed(0); obs = env.reset()
assert obs["agentview_image"].mean() > 1.0, "BLACK FRAME — EGL not working"
env.step(np.zeros(7)); print(env.get_sim_state().shape)
```

Observed 2026-08-04:

| | |
|---|---|
| torch | `2.4.1+cu121`, `cuda avail: True`, `NVIDIA A10G` |
| task 0 | `pick_up_the_alphabet_soup_and_place_it_in_the_basket` |
| `agentview_image` | `(128,128,3) uint8`, **mean pixel 138.5** — real geometry, not black |
| `robot0_eye_in_hand_image` | `(128,128,3)` |
| obs keys | `agentview_image`, `robot0_eye_in_hand_image`, `object-state`, `robot0_gripper_qpos`, `robot0_proprio-state` |
| `env.step(np.zeros(7))` | OK — confirms 7-dim action |
| **`get_sim_state()`** | **`(110,)` float** — `intermediate_state_ref` confirmed cheap and implementable |
| env build + first reset | **8.0 s** |

`get_sim_state()` returning a 110-float vector is the concrete confirmation of the
deferred Tier-2 decision: a per-step state snapshot is ~880 bytes, not ~100× that
for rendered frames.

### Connecting

`~/.ssh/config` on the laptop (key at `~/.ssh/libero-gpu.pem`, mode `400`):

```
Host libero-gpu
    HostName <public-ip>          # changes on every stop/start unless an EIP is attached
    User ubuntu
    IdentityFile ~/.ssh/libero-gpu.pem
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60
```

Security group allows SSH from `0.0.0.0/0` **deliberately** — work happens from
multiple networks and `My IP` breaks on every ISP lease change. Key-only auth
(password auth is off by default on this AMI) is what carries the security here.

### Workaround 4 — `SubprocVectorEnv` requires `spawn`, not `fork`

**EGL contexts do not survive `fork`.** mujoco initializes EGL at import time in
the parent; `SubprocVectorEnv` then forks, and every child dies on its first
render. The symptom is **not** a useful error — the parent raises
`ConnectionResetError: [Errno 104] Connection reset by peer` from
`venv.py:474`, with the child's actual failure never surfacing. Cost ~15 min to
diagnose.

```python
import multiprocessing as mp
if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
```

The vector-env construction must also sit behind `if __name__ == "__main__":`,
because `spawn` re-imports the module in every child. `SubprocVectorEnv` wraps
its factories in `CloudpickleWrapper`, so lambdas are still fine.

**This must be carried into the rollout harness in `src/`,** not just benchmark
scripts — the Phase-2 grid depends on vectorised rollouts working.

### `libero_object` demo data — MEASURED 2026-08-04

```bash
python benchmark_scripts/download_libero_datasets.py --datasets libero_object --use-huggingface
```

**Use `--use-huggingface`.** Without it the script prompts interactively (another
`input()` — same hang as workaround 2) *and* defaults to the original UT-Austin
links, which the script's own message says "may expire soon." For a project
running to March 2027 the HF mirror is the safer source. Also note
`--datasets` **defaults to `all`** — running it bare pulls ~100 GB.

| | |
|---|---|
| download size | **7.0 GB**, 10 HDF5 files, ~660–805 MB each |
| download time | **< 2 minutes** on EC2 |
| disk after | 37 G used of 96 G — **100 GiB root was correct; 34 GiB would have failed** |
| **demos per task** | **50** — previously "commonly cited, unverified" |
| trajectory length | min 136, max 196, **mean 156.2** (≈7,808 steps/task, ≈78k/suite) |
| per-demo keys | `actions (T,7) f8`, `dones`, `rewards`, `states`, `robot_states`, `obs` |
| obs in demos | `agentview_rgb`, `eye_in_hand_rgb` (T,128,128,3) uint8; `gripper_states` (2), `joint_states` (7), `ee_pos`/`ee_ori` (3), `ee_states` (6) |

### Env throughput — MEASURED 2026-08-04. The `n_envs` question is closed.

100 steps/config, zero-action, `libero_object` task 0, 128×128 dual camera,
**no policy in the loop** — this is the env-only floor (physics + render).

| `n_envs` | build (s) | **total steps/s** | per-env steps/s | speedup |
|---|---|---|---|---|
| 1 | 3.0 | 65.3 | 65.3 | 1.00× |
| 4 | 6.1 | 214.0 | 53.5 | 3.28× |
| **8** | 8.9 | **233.2** | 29.1 | **3.57×** |
| 16 | 20.5 | 231.0 | 14.4 | 3.54× |

**Use `n_envs=8`.** Throughput saturates exactly at the vCPU count — MuJoCo
physics is CPU-bound and `g5.2xlarge` has 8 vCPU. n=16 buys nothing and triples
build time.

> **This reverses the PushT/CPU conclusion, as § Step 2 predicted it would.** On
> CPU, small `n_envs` won by ~1.68×. On the A10G, parallel wins by 3.57×. The
> earlier caveat — *"on GPU the tradeoff very likely reverses; measure, don't
> assume"* — is now confirmed rather than suspected.

**Gate-run projection (env time only, `n_envs=8`):**

| scope | @400 max-steps | @600 max-steps |
|---|---|---|
| 3 tasks × 50 eps | 4.3 min (~$0.09) | 6.4 min (~$0.13) |
| **10 tasks × 50 eps (full suite)** | **14.3 min (~$0.29)** | **21.5 min (~$0.43)** |

**This settles the Phase-0 gate scope question on cost grounds.** Evaluating all
10 tasks rather than 3 costs ~10–15 extra minutes of env time, not hours — so the
reproduction check against the published 92.5% and the free per-task readout are
effectively free. Take them.

**⚠ Caveat that keeps this honest: policy inference is NOT in these numbers.**
No trained policy exists yet. On PushT, inference dominated wall-clock entirely
(`SETUP.md` § Step 2). A diffusion policy denoising every `n_action_steps` will
add materially to this, and the figures above are a **floor, not a forecast**.
Re-measure with the real policy in the loop before trusting any grid projection.

### ⚠ The analysis repo is NOT on the instance — and the logger has never run there

As of 2026-08-04 the instance has **LIBERO only**. This repo — and therefore
`src/logging/rows.py` — has never executed against the LIBERO path. The emitter
has only ever run on PushT, on CPU, under `robodiff`: a different observation
space, a different action dim, and no vectorised subprocess workers.

**`SPEC.md` § Instrument-from-day-one is satisfied in letter but not in spirit.**
The 2026-08-04 `n_envs` sweep was a zero-action step-rate microbenchmark with no
policy, no episodes and no success flags, so Table A — which is per-episode and
keyed on `condition` / `disturbance_type` / `success_flag` — genuinely has no row
shape for it, and those numbers belong in this file. But the rule's *second*
stated reason is "it dry-runs the logging code on throwaway data so bugs surface
now rather than on the real grid," and that was missed. The first time the emitter
meets LIBERO must not be during a gate run you are paying for and cannot repeat.

**Fix, on the next instance start, before anything expensive:**

```bash
# 1. get the repo onto the box (SSH agent forwarding, or a read-only deploy key)
git clone <repo-url> ~/asymetric-cost-dp
# 2. the logger needs omegaconf; it is already in the libero env via hydra-core
# 3. dry-run the emitter against the real obs/action space
cd ~/asymetric-cost-dp
MUJOCO_GL=egl ~/miniconda3/envs/libero/bin/python src/rollout/smoke_libero.py \
    --n-episodes 4 --n-envs 2 --max-steps 100
```

`src/rollout/smoke_libero.py` runs a **random** policy — it is not an evaluation
and its success rate is meaningless. What it proves is that rows validate against
`TABLE_A_FIELDS`, that `git_commit` and `config_hash` resolve on the instance, and
that `spawn` + `SubprocVectorEnv` + the emitter coexist. Costs ~1 minute of GPU.

Two schema decisions it encodes, both additive and consistent with prior ones:

- **`success_flag` = `max_reward >= 1.0`**, with `max_reward` logged as a float
  alongside it. Same treatment as PushT (`DECISIONS.md` 2026-07-29) so every
  success threshold stays recomputable. **Assumption to verify against a real
  policy: LIBERO's reward is sparse 0/1.** A random policy will almost certainly
  score 0.0 everywhere, so the smoke test cannot confirm this — it only confirms
  the plumbing.
- **`total_denoising_passes` = 0, `total_replans` = `episode_length`.** A random
  policy performs no denoising and is re-queried every step. Both are *measured*,
  not estimated — `SPEC.md` forbids plausible-looking fill-ins, and `null` would
  be wrong here because the true value is known.

Rows land in `logs/table_a.jsonl` **on the instance**, which is not the same file
as the laptop's. Pull them down before stopping, or they sit on a volume that
gets deleted at teardown.

### Billing discipline — this is now the binding constraint

- **Running bills on uptime, not utilization.** An idle instance costs the same
  as one training. ~$1.21/hr list ⇒ **~$29/day**, **~$203/week** = the whole credit.
- **Stopped still bills EBS**: 100 GiB gp3 ≈ **$8/month ≈ $0.26/day**, and EBS is
  billed on *provisioned*, not used, capacity.
- **Terminate — don't just stop — once GPU work ends (~November).** Stopped from
  August to January is ~$45 of a $200 credit for a box doing nothing. Phases 3
  and 5 need no GPU at all.
- On teardown, confirm **Volumes**, **Snapshots**, and **Elastic IPs** are all
  empty. Orphaned volumes bill forever with no instance attached and nothing in
  the console flagging it.
- Session cost reference: **install from launch to verified env = 21 min ≈ $0.42.**

## Backing up raw results

**The rollout is one-shot and the grid cannot be re-run after January, so the raw
rows are the only irreplaceable artifact in this project.** They live in `logs/`,
which is gitignored — meaning that by default they exist on exactly one local
disk with no redundancy. That is the single largest unforced risk here. Fix it
before the first row is written, not after.

Two tiers, because the artifacts differ by four orders of magnitude in size:

**Tier 1 — per-episode tables (small, committed to git).** Tables A/B/C rows are
plain JSONL. Even at the full Phase-2 grid this is megabytes, not gigabytes.
Gzip them into `logs/archive/` and commit — `.gitignore` already exempts
`logs/archive/*.jsonl.gz`. Git then gives you versioning, offsite redundancy via
the remote, and tamper-evident timestamps that reinforce the data-book claim.

```bash
gzip -kc logs/<run_id>.jsonl > logs/archive/<run_id>.jsonl.gz
```

Keep `logs/archive/MANIFEST.md` as a one-line-per-run index: run ID, date, git
commit of the code, row count, and what the run was. It is also committed.

**Tier 2 — trajectory blobs (large, cloud).** `intermediate_state_ref` targets,
video, and checkpoints are far too large for git.

- Destination: `TBD` — still deliberately unset, but the *reasoning inverted on
  2026-07-28*. It should **not** be colocated with compute. The AWS accounts
  auto-close at 6 months and take their S3 buckets with them, so a colocated
  bucket is a backup that deletes itself in January. Leading candidate is Google
  Drive (provider-independent, survives spot reclaims / quota denials / account
  closure; 15 GB free, ~$2/mo for 100 GB). **Must close before the first real run
  writes rows.**
- Sync command: `TBD`
- **Size decision that belongs here, not Phase 4:** make `intermediate_state_ref`
  point to a **MuJoCo sim-state snapshot, not rendered frames.** At ~KB/step
  that's ~1 GB for a thousand episodes and fits in free Drive; at frame
  resolution it is ~100× that, and Tier-2 backup becomes both a real cost and a
  real sync problem. Cheap to fix now, and getting it wrong is exactly how the
  Phase-4 recoverability stretch dies silently.

**The rule: back up before the next run starts, not at end of session.** A
session that crashes mid-grid is exactly when you lose the rows you care about
most. This is a CLAUDE.md invariant.

**Restore test.** Once, before Phase 1 bulk runs: delete a local run, restore it
from the archive, and confirm the analysis reproduces. An untested backup is a
belief, not a backup.

- Restore test performed: `TBD`

## Cloud

**STILL UNDECIDED as of 2026-07-28.** No provider has been chosen. What changed
this session is *availability*, not the decision: one option is now confirmed to
work. **The decision waits on the EC2 quota outcome** and is tracked in
`STATUS.md`.

| Layer | Where | Status |
|---|---|---|
| Local (CPU) | MacBook Air | The only settled row. PushT low-dim, DP install, logging schema, **all of Phase 3** (pure post-processing, no GPU) |
| Interactive GPU (Ph 0–1, Wk 12) | `TBD` | **Undecided.** SageMaker `ml.g5.2xlarge` is *confirmed obtainable in minutes* (A10G 24GB, 8 vCPU, 32 GB RAM; quota 0 → 1 instantly, self-service) — obtainable is not chosen |
| Bulk grid (Wk 13–15) | `TBD` | **Undecided.** Candidates: SageMaker managed-spot processing jobs, EC2 Spot, other accounts' credits, RunPod |
| Tier-2 blob storage | `TBD` | Deliberately open — see § Backing up raw results. Must close before the first real run |

Unresolved input that will shape the choice, recorded so it isn't re-derived:
AWS on-demand runs ~2.5× RunPod for less GPU (~$0.80–1.00/hr vs ~$0.34/hr for an
RTX 4090), so the credits are the only thing that makes AWS competitive at all.
Worth weighing when the quota outcome lands — **not itself a decision.**

**Nothing in Phase 0 is blocked by any of this.** PushT is CPU-local, the DP
install is local, and the cost model was paper work. LIBERO (Week 2) is the first
thing that actually needs a GPU. If you catch yourself sinking hours into cloud
setup before DP evaluates locally, that's a signal you've drifted off the
critical path.

### AWS account facts

- Post-2025-07-15 Free Tier: **$100 at signup + $100 for five onboarding tasks**,
  **6-month expiry, and the account auto-closes** at expiry or credit depletion,
  whichever comes first. Remaining credits are forfeited at close.
- Accounts belong to different people; each carries its own $200. Up to 3
  available. **Currently open: 1** (as of 2026-07-28); the other two can be opened
  whenever needed. Maximum realistic pool: **$600**.
- Balance on the open account: **$200, untouched.**
- Timing is not a constraint: all GPU work finishes by **mid-November** (Phase 3
  and Phase 5 need no GPU at all), so a 6-month clock started in July has ~2.5
  months of slack. The only rule is that **nothing irreplaceable stays in these
  accounts past January.**

### Quotas — the thing that actually gates GPU access

SageMaker and EC2 quotas are **separate namespaces**. SageMaker quotas are also
split **per usage type** — notebook instance, Studio/JupyterLab, training job,
processing job, spot training job, endpoint — and each is defaulted
independently. Approval on one says nothing about the others.

**SageMaker `ml.g5.2xlarge` — defaults to 0, but raises to 1 instantly.** The
increase to **1 instance** is self-service and granted immediately on any account,
with no support case and no wait (verified 2026-07-28). So the real distinction
against EC2 is not *quota vs. no quota* — both start at 0 — it is **minutes vs.
days-with-a-maybe.**

> **Hard ceiling: 1 concurrent instance per account.** Three accounts ⇒ three
> concurrent GPUs, ~400 GPU-hr total. No ability to burst. Credits still bind
> before wall-clock (~400 GPU-hr across 3 instances ≈ 5.5 days continuous, inside
> a 5-week Phase-2 window), so this is survivable — but it must be planned for,
> and no earlier analysis in this repo modeled it.

Two things about this cap are **unknown and worth checking before Phase 2**:
whether it can be raised above 1 at all, and whether the instant grant covers
*training job* / *processing job* / *spot training job* usage types or only
notebook/Studio usage. Those are the surfaces a batch grid would actually run on,
and each usage type is defaulted independently. Query them:

```bash
aws service-quotas list-service-quotas --service-code sagemaker --region us-east-1 --query "Quotas[?contains(QuotaName,'g5.2xlarge')].[QuotaName,Value]" --output table
```

- EC2 G-family: **both quotas default to 0 vCPU** on new accounts and are
  separately adjustable. Units are vCPUs, not instances.

Account **`051388699393`**, AWS correspondence on **`free.yusuf999@gmail.com`**
(*not* the primary Gmail — this has already cost one session ~20 min).

| Quota | Code | Requested | Status |
|---|---|---|---|
| `Running On-Demand G and VT instances` | `L-DB2E81BA` | 8 vCPU | **GRANTED 8** (2026-07-30, on appeal) |
| `All G and VT Spot Instance Requests` | `L-3819A6DF` | 16 vCPU | **GRANTED 8 of 16** (2026-07-30, on appeal) |

```bash
aws service-quotas list-requested-service-quota-change-history --service-code ec2 --region us-east-1 --output table
```

#### The appeal procedure that actually worked (verified 2026-07-28 → 07-30)

Both requests were **denied in 48 minutes** with an identical template citing
*"large bills due to sudden, unexpected spikes."* Both were then **approved on
appeal within ~8–12 hours.** Expect this sequence; the first denial is not a real
answer.

Escalation path: Support → Create case → **Service limit increase** or **Account
and billing** (both free on Basic; *not* Technical, which needs a paid plan). If
the denial arrives on an existing case, **Reply on that case — do not open a new
one, and do not click "Resolve case."** A denied quota case stays *open*, so no
"reopen" step is needed despite what the denial email says.

**What the denial is actually screening for.** The template says *bills*, but a
new account with no billing history requesting G-family GPU in `us-east-1` matches
the crypto-mining fraud profile. The appeal must argue *risk*, not research merit
— a Tier-1 agent will not read a paper, and attaching one is wasted effort. Four
levers, in descending order of observed value:

1. **Offer to accept less.** "I'm happy to accept a smaller increase or a lower
   initial cap if that makes it easier to approve." Abuse requests never negotiate
   down. Costs nothing when one instance is all you need anyway.
2. **Make the ask exactly one instance** and say so — 8 vCPU *is* one
   `g5.2xlarge`, not headroom to scale out.
3. **Name the spend ceiling.** $200 of credit makes a large bill structurally
   impossible; say that explicitly against their stated reason.
4. **Link public upstream software** a miner would never cite
   (`real-stanford/diffusion_policy`, `Lifelong-Robot-Learning/LIBERO`). Verify
   the URLs resolve first — a 404 reads as fabrication. **Never link this repo
   while it is private**, for the same reason.

A named school or program adds verifiable affiliation and is the cheapest
remaining signal, if privacy allows.

> The earlier advice here — justify via existing in-account SageMaker GPU usage —
> was **never tested**, because no SageMaker workload had run. Do not rely on it.

**Spot quotas above one instance route to AWS Sales**, not to support. The
remaining 8 vCPU of the Spot request was deferred there
(`aws.amazon.com/contact-us/aws-sales/`). Not pursued: it only buys interruption
handoff, and Sales conversations orbit spend commitments, which is a poor use of
time on a credit-funded account.

**Region discipline: `us-east-1`, always.** Quotas, AMIs, S3 buckets, and egress
all care, and requesting a quota in the wrong region is the most common wasted
cycle.

### Two SageMaker gotchas — *if* SageMaker is chosen

1. **Conda envs do not survive a Notebook Instance restart.** Only
   `/home/ec2-user/SageMaker` is on the persistent EBS volume; everything else is
   rebuilt from the AMI on every start. Install the LIBERO/robosuite env *into*
   that path or it evaporates the first time you stop the instance. SageMaker
   **Studio** persists the whole home directory on EFS and sidesteps this — prefer
   Studio if the quota allows.
2. **Notebook instances do not auto-stop.** Attach AWS's `auto-stop-idle`
   lifecycle configuration at creation time. At ~$1.5/hr a forgotten instance
   drains $200 in under six days, and the card on file is not yours. Set a Budgets
   alert on credit **balance**, not just spend.

- Provider(s) chosen: **`TBD` — none.** Decision pending the EC2 quota outcome
- Account setup / smoke test notes: `TBD`
- Budget alarms configured: `TBD` — **do this before launching anything**

### Prior analysis — one premise falsified, the rest still stands

> **Amended 2026-07-28, not overturned.** The SageMaker objections below assumed
> EC2 access was *obtainable*. It is quota-gated and still unconfirmed — that was
> the load-bearing error, and it is why SageMaker is back in contention rather
> than eliminated. Two of the four objections also turn out to be narrower than
> written: "job-submission model" and "custom-container requirement" apply to
> training/processing jobs, **not** to notebook/Studio instances, and the
> job-submission model may actually suit the Phase-2 grid, which is embarrassingly
> parallel and fire-and-forget (PLAN §3 Wk 14 asks for exactly "managed spot +
> checkpointing", which SageMaker Managed Spot provides and EC2 Spot would require
> writing by hand). The managed markup objection stands and is real. **None of
> this decides anything** — it re-opens SageMaker as a candidate. The closing two
> bullets below remain the sharpest guidance in this section.

Worked through on 2026-07-20 and recovered from the Phase-0 chat on 2026-07-27.
Recorded here so tomorrow's decision starts from this rather than re-deriving it.
**None of it is binding** — the stack was explicitly reopened (see `LOG.md`
2026-07-27), and a decision entry claiming otherwise was removed as false.

- **The layered shape that was on the table:** a low-friction *interactive* layer
  (Kaggle free tier for dev iteration, RunPod for training and interactive
  rollouts) plus a separate *bulk* sink for the Phase-2 grid (~200–400 GPU-hr,
  embarrassingly parallel, fire-and-forget). The two layers have genuinely
  different requirements and do not have to be the same provider.
- **SageMaker was ruled out, and free credits do not revive it.** The objections
  are structural, not financial: the job-submission model, the managed markup,
  idle billing, and the custom-container requirement. If AWS is used at all, the
  shape is plain EC2 spot plus a checkpoint-resume wrapper — which is the right
  shape for interruptible bulk rollouts anyway.
- **Where free AWS credits actually pay off:** the bulk sink only. That is the one
  place cost and friction point the same direction — setup amortizes over one big
  batch, and the work is not interactive. Free credits do *not* justify moving the
  interactive layer to EC2, because the VPC / security group / key pair / AMI /
  EBS / spot-request tax is recurring and lands on the resource you have least of.
- **The hinge is credit pool SIZE and EXPIRY** — the recommendation flips on it.
  Four figures and lasting past January ⇒ EC2 spot is a good bulk sink. Roughly
  $100 (Educate-style) or expiring early ⇒ the credits cannot cover a 200–400
  GPU-hr grid, so you would pay the setup tax, exhaust the pool mid-grid, and end
  up paying anyway — strictly worse than not using AWS at all. **Find the number
  before committing, not in November.**

Two things worth carrying into the decision regardless of who wins:

- **The scarce resource is 10–12 hrs/week against the January wall, not dollars.**
  Weigh recurring setup friction on the interactive layer, not just $/GPU-hr.
- **Set billing alarms against credit *balance*, not just spend.** A forgotten
  instance drains free credits exactly like it drains dollars, and a drained
  credit is a silent failure you won't notice until you need the compute.

**The hinge above got its answer on 2026-07-28: $200 per account, 6-month expiry
with auto-close, up to 3 accounts.** That is neither of the two cases this
analysis anticipated — not four figures, not ~$100 — so the flip it describes
doesn't fire cleanly either way. It landed in the middle, which is why the
decision now turns on quota access rather than on pool size.
