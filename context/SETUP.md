# SETUP

How to reproduce the environment from scratch. **Update whenever the environment
changes** — pinned commits, new dependencies, checkpoint locations, cloud config.

> **Status: nothing here has been executed yet.** Everything below is the planned
> procedure as of 2026-07-27. Replace the plan with what actually worked, including
> the workarounds — a session in November needs the real commands, not the intended
> ones.

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
external/    gitignored — cloned DP and LIBERO repos
logs/        gitignored — raw JSONL/CSV rows land here
```

**Vendoring policy: pinned clones, not submodules.** Clone third-party repos into
`external/` (gitignored) and record the exact commit hash below. Submodules are a
known source of confusion — detached HEAD, forgotten `--recursive`, sync headaches
— and a documented hash gives the same reproducibility for a solo project.

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
git clone https://github.com/real-stanford/diffusion_policy.git external/diffusion_policy
git -C external/diffusion_policy rev-parse HEAD   # record the hash below
mamba env create -f external/diffusion_policy/conda_environment.yaml
```

The env is named `robodiff`. Follow the repo README as source of truth — the
pinned deps are what they are; don't fight them.

**Done when:** `robodiff` activates and `python -c "import diffusion_policy"` runs
without error.

- Pinned commit: `TBD`
- Actual install notes / workarounds: `TBD`

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

Point the repo's eval script at it with `--device cpu`.

**Done when:** a success-rate number prints. Near the published PushT number ⇒ the
whole pipe is proven and Phase 0 becomes a billing question rather than a research
risk. An error ⇒ you found the real blocker in an afternoon instead of Week 4.

- Checkpoint used: `TBD`
- Success rate observed vs. published: `TBD`
- Exact eval command that worked: `TBD`

## Step 3 — Emit one Table A row

Wrap the eval so it writes a single per-episode JSONL row per `SPEC.md` Table A
(`episode_id`, `task_id=pusht`, `seed`, `condition=eval`, `success_flag`,
`wallclock`, `git_commit`). This dry-runs the logging code on throwaway data.

**Done when:** `logs/` contains one valid JSONL row.

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

- Destination: `TBD` — **deliberately unset**, because it likely wants to be the
  same provider as the compute stack, which is still open (see `STATUS.md`,
  resolving 2026-07-28). Fill this in as part of that decision.
- Sync command: `TBD`

**The rule: back up before the next run starts, not at end of session.** A
session that crashes mid-grid is exactly when you lose the rows you care about
most. This is a CLAUDE.md invariant.

**Restore test.** Once, before Phase 1 bulk runs: delete a local run, restore it
from the archive, and confirm the analysis reproduces. An untested backup is a
belief, not a backup.

- Restore test performed: `TBD`

## Cloud

**Undecided.** No provider has been chosen — AWS, RunPod, Kaggle, Vast, and Colab
are all still open. Being decided 2026-07-28; tracked in `STATUS.md`. Fill this
section in once the decision is made and log the reasoning in `DECISIONS.md`.

**Nothing in Phase 0 is blocked by it.** PushT is CPU-local, the DP install is
local, and the cost model was paper work. LIBERO (Week 2) is the first thing that
actually needs a GPU. If you catch yourself sinking hours into cloud setup before
DP evaluates locally, that's a signal you've drifted off the critical path.

### Prior analysis — inputs, **not** a decision

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

- Provider(s) chosen: `TBD`
- Account setup / smoke test notes: `TBD`
- Budget alarms configured: `TBD`
