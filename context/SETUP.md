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

## Step 4 — LIBERO (Week 2)

Separate conda env. Pull the repo and start the dataset/asset download early so
it isn't a bottleneck.

- Pinned commit: `TBD`
- Task IDs (**unverified** — confirm these exist with the right observation/action
  space before building anything against them):
  - handover → `TBD` (LIBERO-Object, pick-place framing)
  - retrieve-dropped → `TBD` (LIBERO-Object)
  - drawer/container → `TBD` (LIBERO-Goal — contains drawer/cabinet tasks)

Also audit **LIBERO-Plus** and **LIBERO-Pro** for existing perturbation harnesses
before writing an injector. 90 minutes, potentially saves ~2 weeks of Phase 1.

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

| Quota | Code | Requested | Status |
|---|---|---|---|
| `Running On-Demand G and VT instances` | `L-DB2E81BA` | 8 vCPU | **PENDING** (filed 2026-07-28, `us-east-1`) |
| `All G and VT Spot Instance Requests` | `L-3819A6DF` | 16 vCPU | **PENDING** (filed 2026-07-28, `us-east-1`) |

```bash
aws service-quotas list-requested-service-quota-change-history --service-code ec2 --region us-east-1 --output table
```

Auto-denial within minutes is common and expected. Escalation path: Support →
Create case → **Service limit increase** or **Account and billing** (both free on
Basic; *not* Technical, which needs a paid plan). The strongest justification line
is that the account already runs SageMaker GPU workloads, so EC2 access is being
requested for cost efficiency on batch evaluation — verifiable in-account
evidence that this is a real workload.

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
