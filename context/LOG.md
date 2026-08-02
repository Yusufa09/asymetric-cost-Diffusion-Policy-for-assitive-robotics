# LOG

Dated session journal. Append-only, **newest first**: what you did, what you
observed, what broke, what's next.

This is the file `STATUS.md` can't be — STATUS is a snapshot that gets
overwritten; this is the history. Two payoffs: in January you write the abstract
from this instead of reconstructing it, and it is the **project data book**.
Commit timestamps give tamper-evident dating.

> **Resolved 2026-07-28:** the data book format is flexible, so this
> git-committed markdown log satisfies the requirement. No physical handwritten
> logbook is needed. Keep writing it contemporaneously anyway — that property is
> what makes it worth anything to a judge.

## How much detail

**This file is not auto-loaded into sessions, so length here is free.** Write for
a judge and for January-you, not for brevity. A substantive work session is a
paragraph or two plus specifics — roughly 10–25 lines. A 20-minute admin session
is three. Length tracks what happened, not a quota.

Five properties make it a real research log:

1. **Contemporaneous.** Written the day it happened. Not reconstructed.
2. **Failed attempts included.** The three hours lost to a build error *is* the
   record. A log containing only successes reads as fabricated.
3. **Specific enough to reconstruct.** Actual commands, versions, config values,
   error text. "Got PushT working" is worthless in January; the exact incantation
   that resolved it is what you need.
4. **Raw observation before interpretation.** The number you saw, with seed and
   n, then what you think it means.
5. **Reasoning captured at the moment of choosing**, not rationalized afterward.

Numbers live in `logs/*.jsonl` per `SPEC.md` — this file records what you ran,
what you saw, and what you concluded, with pointers to run IDs.

Template:

```
## YYYY-MM-DD — <session focus>  (N hrs)

**Goal:** what I set out to do.

**Did:** commands, versions, configs, hashes. Specific.

**Observed:** raw numbers with seed and n; the published figure being compared
against; wallclock. Interpretation after the number, not instead of it.

**Broke / dead ends:** what failed, how long it cost, how it was diagnosed,
what actually fixed it. Do not skip this section.

**Decided:** anything that constrains future work → also append to DECISIONS.md.

**Next:** the handoff to the next session.
```

Log hours per session — it feeds the ISEF forms and tracks against the
10–12 hrs/week capacity assumption in `PLAN.md`.

---

## 2026-08-02 — LIBERO audited without installing it. Three planned tasks don't exist; no DP checkpoint does either.  (~2.5 hrs)

**Goal:** Close the two Week-2 carryover items — verify the 3 LIBERO task IDs, and
audit LIBERO-Plus / LIBERO-Pro for an adoptable perturbation harness. Both are
GPU-free, so neither waits on the Budgets alarms.

**Did.** Cloned LIBERO code only — `git clone --depth 1`, pinned
`8f1084e3132a39270c3a13ebe37270a43ece2a01` (2025-03-15; repo looks unmaintained
since). **650 MB** (404 MB assets, 13 MB init_files), disk still 28 GB free. Did
*not* run `download_libero_datasets.py`; the ~100 GB is demo HDF5 and belongs on
the instance.

Then read the repo instead of installing it. **No robosuite, no mujoco, no conda
env, no GPU** — task definitions, the env wrapper, the benchmark registry and the
BDDL files are all plain text. This is worth repeating for LIBERO-side questions
in future sessions: the arm64 mujoco tax is avoidable for anything static.

Verified from source: Panda + `OSC_POSE`; **action dim 7** (6 delta-pose +
gripper, hard-coded at `libero/lifelong/metric.py:120` as `np.zeros((env_num,7))`);
obs = `agentview` + `robot0_eye_in_hand` RGB **128×128** plus `gripper_states`(2)
and `joint_states`(7) (`libero/configs/data/default.yaml:25-34`); 20 Hz.

**Observed — five findings, in ascending order of how much they cost.**

1. **Indexing trap.** Canonical task order is `libero_suite_task_map.py`, **not**
   `bddl_files/*/tasks_info.txt`. The two list the same 10 tasks in different
   orders. Published per-suite results index against the map. Using the wrong one
   mislabels every task silently.

2. **Two injector primitives already exist**, both in `envs/env_wrapper.py`:
   `get_sim_state()` → flattened MuJoCo state (line 118) is exactly what
   `intermediate_state_ref` was deferred to point at — that deferred decision is
   implementable as written. `set_state()` / `regenerate_obs_from_state()` (lines
   127-145) set state → `sim.forward()` → re-derive observables, which is the
   object-shift injector: read state, displace target qpos, write back
   mid-episode.

3. **The three planned framings do not exist in LIBERO.** Not "not found" —
   absent. `PLAN.md` §0 row 1 names handover, retrieve-dropped-object, and
   drawer/container. Only the third exists (`libero_goal[0]
   open_the_middle_drawer_of_the_cabinet`). There is no handover task in any
   suite and no dropped-object task; nearest analogues are pick-place into a
   receptacle and `libero_spatial[4]` (retrieve from a drawer). Worse, all 10
   `libero_object` tasks are **one template** differing only in grocery item, so
   drawing two framings from that suite would have been the same task twice.

4. **Perturbation audit — verdict: build the injector.** LIBERO-Plus
   ([2510.13626](https://arxiv.org/abs/2510.13626), 7 axes, 10,030 tasks) and
   LIBERO-PRO ([2510.03827](https://arxiv.org/abs/2510.03827), 4 axes) both
   perturb **at episode initialization only**. Neither injects anything during
   execution, which is the entire premise here. So `PLAN.md` §3 Wk 5's hoped-for
   ~2-week Phase-1 compression **does not happen** — the branch the plan called
   "you've confirmed your injector is worth building." Partial credit: LIBERO-Plus
   O2 "Target Object Pose" is reusable displacement code, and neither implements
   occlusion or delayed observation, so those remain fully ours. Genuine gain: a
   sharpened, citable prior-work distinction — *they perturb the initial
   condition and ask whether the policy still succeeds; we perturb during
   execution and ask whether it notices in time.*

5. **No released DP-on-LIBERO checkpoint, and no per-task published numbers.**
   Searched OpenVLA-OFT and the LeRobot hub (which ships `diffusion_pusht`,
   `pi0_libero_base`, `pi05_libero_base`, `xvla-libero` — no DP-LIBERO). Scope
   as *not found*, not *proven absent*. The cited DP baseline **78.3 / 92.5 /
   68.3 / 50.5** (Spatial/Object/Goal/Long) comes from
   [OpenVLA-OFT Table I](https://arxiv.org/html/2502.19645v1), attributed to Kim
   et al., **trained from scratch**, protocol 10 tasks × 50 episodes = 500 trials
   **averaged per suite**. Also verified: **DP trains one policy per suite**, so
   the suite is the cost unit, not the task.

**Broke / dead ends.** No build failures — nothing was installed. The real cost
was a **wrong recommendation I made and then had to reverse mid-session**: I first
recommended all three tasks from `libero_goal` on the reasoning that it is the
only suite with mechanically distinct skills. That was wrong, and the evidence is
in the BDDL files. Every `libero_goal` task is the same problem
(`LIBERO_Tabletop_Manipulation`) with an **identical object set**
`{akita_black_bowl_1, cream_cheese_1, wine_bottle_1, plate_1}` — same scene, same
objects, only the goal predicate differs. DP has **no language conditioning**, so
a suite policy cannot tell those 10 tasks apart from the image. That is not a
curiosity, it is the published ranking: Object 92.5 (distinct object sets per
task) > Spatial 78.3 (two identical bowls) > Goal 68.3 (one scene, ten goals).
**And it would have contaminated the headline** — the control signal is
inter-chunk consistency, so in a goal-ambiguous scene the policy is legitimately
multimodal with *no disturbance present*, inflating nominal inconsistency,
inflating the conformal threshold calibrated on nominal rollouts, and making
disturbance indistinguishable from the policy never having known which task it
was doing. Caught by diffing `(:objects` blocks across suites — ~20 min to find,
would have cost a phase to discover in November.

Second thing that needed correcting: I framed the per-suite/per-task choice as
fixed, when it is not. The ambiguity confound is a property of the **training
recipe**, not the suite — a single-task policy has one goal and no ambiguity. Also
verified `libero_object` is `LIBERO_Floor_Manipulation` (fixture: `floor`) while
Spatial and Goal are `LIBERO_Tabletop_Manipulation`, so a hand-picked cross-suite
set *would* be visually disambiguable. That option was priced and rejected on
budget, not on correctness.

**Decided.** Phase 0/1 platform is the **`libero_object` suite**, per-suite
training, one run — see `DECISIONS.md`. Gate rewritten to suite average within
±5 points of 92.5%, band declared before looking. Also settled by evidence rather
than choice: the disturbance injector gets built from scratch.

**Schedule read.** Week 3 of 28 (`floor((Aug 2 − Jul 17)/7)+1`). One week behind
on the LIBERO track, ahead on infrastructure. But the week is the small part —
findings 4 and 5 are **~2–3 weeks of scope that was not in the plan** (Phase 0 is
now a training task; Phase 1 does not compress) against 2 weeks of designed buffer
in Phase 4. Buffer is now spoken for; treat Phase 4 as catch-up. Front-loading
risk before Thanksgiving (Wk 19) is now binding, not advisory. Offsetting good
news: **Phase 3, the headline, needs no GPU at all.**

**Next.** Budgets alarm on credit balance (~10 min, still unmet and still the hard
gate). Then launch `g5.2xlarge`, install the LIBERO env, pull `libero_object`
only, and **before training, time one rollout and one training epoch** — that
20-minute measurement replaces both the ~$1.5/hr and ~130-GPU-hr estimates, which
are load-bearing and unmeasured, and settles the `n_envs`-on-GPU question.

---

## 2026-07-31 — AWS GPU quotas: denied, appealed, approved. Compute unblocked.  (~2 hrs)

**Goal:** Check the two EC2 quota requests filed 2026-07-28, and resolve the
compute-stack decision that was explicitly gated on them.

**Did.** Read the AWS correspondence, drafted appeals for both denials, submitted
them, and read the outcomes.

Cases, both filed 2026-07-28 15:47 ET in `us-east-1`:

| Case | Quota | Code | Asked |
|---|---|---|---|
| 178526806600160 | `Running On-Demand G and VT instances` | `L-DB2E81BA` | 8 vCPU |
| 178526807000059 | `All G and VT Spot Instance Requests` | `L-3819A6DF` | 16 vCPU |

Both **denied 2026-07-28 16:35 ET**, 48 minutes after filing, with byte-identical
template text: *"Service quotas are put in place to help you gradually ramp up
activity and decrease the likelihood of large bills due to sudden, unexpected
spikes."* Not an auto-denial — a human acknowledged at 15:48 restating the exact
quota and target value before declining. Both invited appeal by reopening with a
detailed use case.

Appeal reasoning, which is the part worth keeping: the template says *bills*, but
a three-day-old account with no billing history requesting G-family GPU capacity
in `us-east-1` is feature-for-feature the **crypto-mining fraud profile**. The
appeal's job is therefore not to argue research merit — a Tier-1 agent will not
read a paper — it is to look unlike a miner. Four levers used: (1) the ask is
*exactly* one `g5.2xlarge`, not headroom to scale out; (2) $200 of credit is a
hard spend ceiling, so a large bill is structurally impossible; (3) named public
upstream software a miner would never cite — `real-stanford/diffusion_policy` and
`Lifelong-Robot-Learning/LIBERO`, both verified HTTP 200 before sending; (4) an
explicit offer to **accept a smaller increase or lower initial cap**, which
inverts the signal since abuse requests never negotiate down. Evidence of a real
workload came from the reproduced PushT baseline (0.945 vs 0.969 published, n=50).
Decided against attaching a paper — it answers a question nobody asked. School and
magnet-program name were cut for privacy, at a known cost in verifiable
affiliation.

Appeals submitted **2026-07-30 00:56 ET** on both cases (via **Reply**, not
"Resolve case" — neither case had actually been closed, so no reopen was needed).

**Observed.** Both appeals succeeded:

- **178526806600160 — approved in full**, 2026-07-30 08:49 ET (Pradnya K.). New
  quota 8. Escalated to the EC2 service team at 02:43 before approval.
- **178526807000059 — partially approved**, 2026-07-30 12:30 ET (Harshit S.).
  8 vCPU of the 16 requested; remainder routed to AWS Sales rather than denied.

Net: **8 vCPU on-demand + 8 vCPU Spot G/VT in `us-east-1`** = one `g5.2xlarge`
either way. Verified applied in the Service Quotas console. $200 credit confirmed
resident on account `051388699393`. Appeal-to-resolution turnaround ~8 hrs
(on-demand) and ~12 hrs (Spot) — far inside the 1–5 business days SETUP assumed.

Consequence not previously modeled: at the *estimated* ~$1.5/hr, $200 buys roughly
**130 GPU-hr** against `PLAN.md`'s 350–650 GPU-hr estimate. **One account does not
fund this project.** It funds Phase 0 and probably Phase 1. Accounts two and three
are now derisked, though — the quota path is a known, ~2-day, winnable procedure
rather than a gamble.

**Broke / dead ends.** ~20 min lost searching the wrong mailbox. The Gmail MCP is
bound to `yusufaae09@gmail.com` only, and every AWS query against it returned
empty — which reads as "no reply yet" rather than "wrong account," so the failure
was silent and misleading. Apple Mail has **four** accounts configured; the AWS
correspondence lives on **`free.yusuf999@gmail.com`**, account **`051388699393`**.
Resolved by enumerating accounts via AppleScript through the Control-your-Mac MCP.
Recorded here because it will recur every time this project touches AWS mail.

Also noted: the Spot approval opens "Hello Team" and refers to *"your
mid-September launch timeline"*, which appears in neither case and contradicts the
January 2027 date actually submitted. The agent appears to have crossed wires with
another ticket. Harmless to the outcome, but **do not repeat that date back to
AWS** if Sales is ever contacted.

**Integrity flag — the submitted appeal text is currently inaccurate.** Both
appeals assert *"I have Budgets alarms set on the credit balance."* They are not
set. This was flagged as blocking before sending and went out anyway. It is a
written claim to AWS support inside a risk argument, and it is the one thing
standing between a forgotten instance and the credits just won. Setting them
closes the gap; it is a 10-minute task and it is now a hard gate on launching.

**Decided.** AWS EC2 `g5.2xlarge` is the Phase 0/1 compute platform; credits are
spent before cash. This reverses a recommendation made three times earlier in the
same session. → `DECISIONS.md`.

**Next.** LIBERO task-ID verification + LIBERO-Plus / LIBERO-Pro perturbation
audit — 90 min, no GPU required, still the highest-leverage block in the schedule.
Budgets alarms before any instance launch.

## 2026-07-29 — Execution starts: DP installed, PushT baseline reproduced, DP vendored  (~4.5 hrs)

**Goal:** Break the two-week planning-only streak. Execute the Week-1 spine:
install Diffusion Policy, evaluate a released PushT low-dim checkpoint on CPU,
emit the first Table A rows. Explicitly *not* training.

**Did.** Cloned `real-stanford/diffusion_policy` at
`5ba07ac6661db573af695b419a7947ecb704690f`. Built the conda env from
**`conda_environment_macos.yaml`** — note SETUP.md said `conda_environment.yaml`,
which is the CUDA/linux file and cannot solve on osx-arm64; that was a doc bug,
now fixed. Env is 1.6 GB / 310 packages (torch 1.12.1 CPU, gym 0.21.0, py3.9).
Downloaded the low-dim CNN checkpoint
`epoch=0550-test_mean_score=0.969.ckpt` (1,044,185,793 bytes, verified against
`content-length`) from `.../low_dim/pusht/diffusion_policy_cnn/train_0/`.

Wrote `src/rollout/eval_pusht.py` and `src/logging/rows.py` (~355 lines total).
**Did not use DP's `eval.py`** — it unpickles its config from inside the `.ckpt`,
so hydra never runs and nothing is CLI-overridable, including `n_envs`, `n_test`,
and `policy.n_action_steps` (the execution horizon this whole project adapts).
Our wrapper loads the payload, patches the config before instantiating, and emits
Table A rows, collapsing SETUP Steps 2 and 3 into one command. `rollout()` is an
instrumented copy of `PushTKeypointsRunner.run()` that additionally tracks
per-episode policy calls.

**Observed.** Smoke test (run `20260729T004902Z`, n_test=2, n_envs=2, seeds
4300000–1): 2/2 success, mean_score 1.0000, 106.5 s.

Full reproduction (run `20260729T005212Z`, **n=50 test episodes**, seeds
4300000–4300049, n_train=6, n_envs=56, CPU, 8790.9 s = 2 h 26 m):

- `test/mean_score` = **0.9453** (sd 0.194, se 0.027)
- published = **0.9690**; gap +0.0237 = **0.87 standard errors**; 95% CI
  [0.8916, 0.9990] contains the published value → **reproduction PASSES**
- success rate (coverage ≥ 95%) = **30/50 = 60%**
- distribution is **bimodal**: 30 at exactly 1.0, **17 in [0.9, 1.0)**, 0 in
  [0.5, 0.9), 3 below 0.5 (min 0.023)
- 20/50 episodes hit the 300-step truncation; `total_replans` ranged 10–38

Interpretation: the residual 0.024 gap needs no explanation — **DDPM sampling
noise is unseeded** and the published run was CUDA vs. our CPU, so RNG streams
differ entirely. Same initial conditions, different sampling noise. Max
`total_replans` = 38 exactly matches the structural ceiling
`ceil(max_steps/n_action_steps) = ceil(300/8)`; useful as a future sanity check.

The **bimodality is the real finding.** Mean score 0.945 and success rate 60%
describe the same 50 episodes, and a third of episodes sit just under the 0.95
coverage cutoff with nothing in the middle. `success_flag` is the binary feeding
the asymmetric cost model, and that cutoff was inherited from IBC, not chosen.

**Broke / dead ends.**

1. **`mamba env create` exits 1 on the pip block** (~25 min). `imagecodecs==2022.9.26`
   fails to compile: `fatal error: 'libheif/heif.h' file not found`. The conda env
   is fully built by then, so this is "run two more commands," not "start over."
   Ignored it — verified by grep that `imagecodecs`, `robomimic`, `r3m`,
   `pytorchvideo`, `atomics` and `ray` are imported nowhere on the PushT low-dim
   path. `pygame` is the only pip package that matters and installs first.
2. **`import diffusers` → `ImportError: cannot import name 'ReduceOp'`** (~20 min).
   The osx-arm64 CPU torch build ships without `torch.distributed`
   (`is_available()` False), so `accelerate` 0.13.2 dies on import; diffusers
   pulls it via `modeling_utils.py:52`. Fixed by **removing accelerate entirely** —
   diffusers guards it behind `is_accelerate_available()`, which merely checks the
   package exists, so deleting it makes the check return False. DP never imports it.
3. **`ImportError: cannot import name 'cached_download'`** (~15 min). `huggingface_hub`
   is unpinned in the yaml, so conda installed 0.31.4, which removed that symbol;
   diffusers 0.11.1 still imports it. Pinned to **0.25.2**, the newest release that
   keeps it. Classic old-pinned-stack / unpinned-transitive-dep drift — **if this
   env breaks in November, suspect a drifting dep, not your code.**
4. **Machine slept mid-run.** The 2 h 26 m rollout was suspended and resumed on
   wake. It survived, but nothing is written until the run completes, so a sleep
   that became a shutdown would have cost the whole run. Use `caffeinate -is`.
5. **I dropped upstream's `tqdm` progress bar** when copying the rollout loop,
   making a 2.5-hour run completely opaque — I could not answer "how long is
   left" and produced three wrong extrapolations before falling back to the one
   estimate with a structural basis (the 38-call ceiling), which was correct.
   Restored, with `ceil(max_steps/n_action_steps)` as the denominator.

**Two claims I made and then had to retract, recorded so they aren't re-derived:**
(a) "56 subprocesses will thrash the laptop" — false; env workers are ~12 MB each
and idle at 0% CPU. (b) "Prefer one big chunk" — false, and it briefly went into
SETUP.md before being corrected. Measured: straggler waste is **25.5%** (1586
batch-elements needed vs 2128 paid) and batch-56 costs **1.25×** more per
episode-slot than batch-1 (4.13 s vs 3.30 s), so small `n_envs` wins ~1.68× on
CPU. **Do not infer throughput from CPU%** — the extra utilisation was doing more
work, not more episodes. Likely reverses on GPU; measure rather than assume.

**Unplanned finding — two of three Phase-1 disturbances already exist in PushT.**
`env_runner.keypoint_visible_rate` (per-keypoint Bernoulli dropout,
`pusht_keypoints_env.py:93`) is occlusion; `env_runner.n_latency_steps`
(`pusht_keypoints_runner.py:48-50, 225-227`) is delayed observation, exactly as
PLAN §3 Wk 6 specifies. Only object-shift needs building. Caveats: visibility
resamples every step rather than persistently occluding a region, and neither has
a clean LIBERO analogue — a dev proxy, not the real injector. This is the PushT
counterpart of the LIBERO-Plus/Pro audit still queued for Week 2.

**Provenance trap found.** The `config.yaml` published alongside the checkpoints
says `test_start_seed: 100000`; the config **inside** the checkpoint says
**4300000** (with `training.seed: 42`). They disagree, and the checkpoint is the
authority. Anything reconstructing config from the published YAML evaluates
different initial conditions and then fails to reproduce for reasons that look
like a code bug. `eval_pusht.py` reads the payload, so it is right by construction.

**Decided.** Diffusion Policy is **vendored** — committed into this repo in full
(369 files, 31 MB, MIT, unmodified) rather than gitignored behind a pinned hash.
See DECISIONS.md. Also: `success_flag` for PushT is defined as `max_reward >= 1.0`
(coverage ≥ 95%), with `max_reward` logged as a float so any threshold stays
recomputable.

**Backed up.** `logs/archive/table_a_20260729.jsonl.gz` (58 rows, both runs),
**restore-tested byte-identical** — the first time the SETUP.md backup invariant
has actually been exercised rather than asserted.

**Next.** Phase-0 PushT gate is met. LIBERO is now the critical path: verify the
3 task IDs, audit LIBERO-Plus/Pro for perturbation harnesses (90 min, highest
leverage in the schedule). Compute stack still open pending the EC2 quota outcome.

## 2026-07-28 — Compute stack investigation; AWS GPU access path found  (~2 hrs)

**Goal:** Resolve the compute-stack decision STATUS scheduled for today.

**Did:** Priced every candidate against PLAN §10's 350–650 GPU-hr estimate.
**One** AWS account open on the post-2025-07-15 Free Tier ($100 at signup + $100
for five onboarding tasks, **6-month expiry with automatic account closure**),
balance **$200, untouched**; two more can be opened on demand. Then established
the session's key fact by comparing two quota paths. SageMaker `ml.g5.2xlarge`
also **defaults to 0**, but the increase to **1 instance is self-service and
granted immediately, on any account** — no support case, no wait. EC2's G-family
quotas (`Running On-Demand G and VT instances` and `All G and VT Spot Instance
Requests`, independently adjustable, separate namespace from SageMaker's) also
default to **0 vCPU** but require a support case and 1–5 business days, with
denial common for accounts without billing history. So the difference between the
two surfaces is **not** quota vs. no quota — it is *minutes* vs. *days-with-a-
maybe*. Filed both EC2 requests in `us-east-1`:
`Running On-Demand G and VT instances` → 8 vCPU (`L-DB2E81BA`) and
`All G and VT Spot Instance Requests` → 16 vCPU (`L-3819A6DF`). Both **PENDING**
at end of session.

**Observed:** No rollout numbers — nothing was run. Pricing collected, all
approximate and none yet checked against a real invoice: EC2 `g6.xlarge`
on-demand $0.8048/hr, `g5.xlarge` $1.006/hr, EC2 Spot ~$0.30–0.40/hr, RunPod RTX
4090 $0.34/hr, Vast RTX 4090 ~$0.29–0.39/hr, SageMaker `ml.g5.2xlarge` ~$1.5/hr
(**estimated** from `g5.2xlarge` plus typical managed markup — not sourced, and
load-bearing, so verify it off Cost Explorer once real hours exist). The spread
that matters: $200 buys **~130 GPU-hr** on SageMaker on-demand versus **~570** on
EC2 Spot. That ~4× gap is the entire reason the EC2 request is worth filing.

**Second constraint, previously unmodeled: SageMaker's instant quota grant caps
at 1 instance.** So SageMaker gives at most **one concurrent GPU per account** —
three accounts, three concurrent instances, ~400 GPU-hr total. Credits bind before
wall-clock does (~400 GPU-hr over 3 instances ≈ 5.5 days of continuous 3-way
parallel running, inside a 5-week Phase-2 window), so the ceiling is survivable,
but it means the Phase-2 grid has **no ability to burst**. Whether the cap can be
raised above 1, and whether the instant grant applies to *training job* /
*processing job* / *spot training job* usage types as well as notebook usage, is
unknown and matters — those are the surfaces a batch grid would actually use.

**Broke / dead ends:** Three recommendations were made and reversed *within* the
session. Recording them because each reversal was forced by a fact, and the
sequence is the actual finding. (1) "Single-provider AWS on EC2 Spot" — killed on
learning EC2 G quotas default to 0 and are routinely denied for individual
accounts with no billing history. (2) "RunPod primary, ~$150–250 out of pocket" —
killed on learning SageMaker already works today. (3) The multi-account plan was
flagged against AWS Free Tier Terms (creating "more than one account to receive
additional benefits" ⇒ ineligible, standard rates charged); resolved as
non-applicable because the accounts belong to different people. Net cost: no
wasted spend, but the lesson is sharp — **AWS GPU access is gated by quota, not
by credits**, and SETUP.md's prior analysis had silently assumed EC2 access was
obtainable. That assumption was the load-bearing error.

**Decided:** *Nothing.* The compute stack is still open and now waits on the EC2
quota outcome. Recording that explicitly, because a DECISIONS.md entry locking
SageMaker as the Phase 0–1 surface was drafted this session and **removed before
commit** — what the session produced was a fact (SageMaker works without a support
case), and availability is not a choice. This is the **second time in ten days**
the compute stack has been written up as decided when it wasn't; the 2026-07-27
entry below records the first. The pattern is worth naming: the moment an option
is confirmed to work, the writeup wants to promote it to "chosen," and it takes a
deliberate pass to catch. Sole guard is `MAINTENANCE.md` rule 2 — never mark
something done that wasn't verified.

**Closed:** Data book format — flexible, so this markdown log qualifies. GitHub
repo confirmed private.

**Opened:** Competition venue is undecided — ScienceMontgomery vs. PG County,
the latter possibly an easier ISEF path. Changes nothing about the project or the
schedule, but the two have different registration and abstract deadlines, so it
cannot stay unexamined. ScienceMontgomery 2027 registration is **not yet open**.

**Next:** Install Diffusion Policy and evaluate a released low-dim PushT
checkpoint on CPU, per `SETUP.md`. Unchanged, unblocked by any of the above, and
now two sessions overdue.

---

## 2026-07-27 — Repo and context system stood up

**Did:** Created the repo and the `context/` documentation system — CLAUDE.md
(auto-loading handoff), STATUS, LOG, DECISIONS, PLAN, SPEC, LITERATURE, SETUP,
MAINTENANCE, plus the `/session-end` command. Migrated plan v2, the full
literature review, and the cost model / logging schema out of Drive and the
planning chats. Folded in the 2026-07-26 decisions that had never reached STATUS.

**Broke / learned:** Two drift problems surfaced during migration. (1) STATUS had
gone nine days without an update and was missing every decision from the Phase 0
chat. (2) Plan §6 was still the v1 logging schema, superseded by SPEC. Both
reconciled. Also corrected a false entry I had briefly recorded: the compute
stack was written up as a decision when it is in fact **still undecided** —
removed from DECISIONS and reopened as a question in STATUS.

**Next:** Install Diffusion Policy and evaluate a released low-dim PushT
checkpoint on CPU. See `SETUP.md`.

---

## Reconstructed entries

_The entries below predate this log and were reconstructed from the planning and
Phase 0 chat transcripts on 2026-07-27. Dates are approximate to the day._

## 2026-07-26 — Cost model and logging schema locked

**Did:** Worked through the four design axes of the cost model and settled the
structure-vs-values distinction. Specified all three logging tables as a superset
with a `[live]`/`[derived]` split. Discussed compute options; **nothing decided.**

**Broke / learned:** Google Drive's `create_file` path failed four times
including on a minimal test, so the spec never got written to Drive — it existed
only as paste-ready text in the chat until today's migration. Direct cause of the
"repo is the single source of truth" decision.

**Next:** Make the repo, then DP install.

## 2026-07-20 — Phase 0 chat opened

**Did:** Opened the Phase 0 working chat. Confirmed position (Week 1 of 28) and
identified the Week 1 critical path. Established that none of the Week 1 work
requires cloud compute — PushT is CPU-local, so the compute decision can be
deferred without blocking anything. Settled the checkpoint-eval-before-training
tactic and the two-conda-env strategy.

**Broke / learned:** Found the first STATUS drift — STATUS claimed AWS credits
confirmed, PushT rolling out, and LIBERO task IDs identified, while every
corresponding checklist box was unchecked and none had actually been verified.

**Next:** Cost model on paper; repo; DP install.

## 2026-07-18 — Literature review and plan v2

**Did:** Ran an intensive literature review across adaptive horizon, failure
detection, conformal tooling, recovery, and assistive cost-asymmetry. Rewrote the
plan as v2 with six changes folded in.

**Broke / learned:** **The project's central novelty claim collapsed.** Adaptive
execution horizon is a populated 2025–26 subfield, and AutoHorizon already runs
the originally-proposed K-sample MC-variance signal as a dominated baseline.
Response: promoted the asymmetric-cost evaluation to headline, demoted adaptive
horizon to mechanism, switched the control signal to inter-chunk consistency, and
adopted AEGIS's two controls.

**Next:** Set up the document/workflow system; start Phase 0.

## 2026-07-17 — Project planning

**Did:** Worked through the four open decisions from the handoff — tasks,
disturbances, uncertainty signal, framing. Locked all four. Built the first full
plan: phase map, week-by-week schedule, experiment grid, logging schema, metrics,
figures, per-stage kill criteria, and the 5-minute talk structure.

**Next:** Background literature review before starting any build work.
