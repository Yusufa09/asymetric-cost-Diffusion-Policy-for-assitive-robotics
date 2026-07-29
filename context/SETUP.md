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
