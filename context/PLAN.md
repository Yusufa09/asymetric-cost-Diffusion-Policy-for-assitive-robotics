# Project Plan v2

**Disturbance-Robust Adaptive Execution Horizon, Evaluated Under Assistive
Asymmetric Cost.** Revision v2, post-literature-review. Changelog vs. v1 in §11.

> **Update trigger:** phase gates only (~5× total) — see `MAINTENANCE.md`. One
> caveat flagged inline: §6 is superseded by `SPEC.md`.
>
> **Off-cycle edit 2026-08-02**, made because §0 row 1 and §7's Phase-0 row were
> **factually false**, not merely stale: they named two LIBERO tasks that do not
> exist and a gate that cannot be evaluated. §3 Wk 5, §9 and §10 updated in the
> same pass. Sections touched: §0, §3, §7, §9, §10. **Schedule (§2) unchanged** —
> see `STATUS.md` for the Week-3 slippage read.

Target: ScienceMontgomery (Computer Science) → ISEF qualification. Bar to clear:
ScoutCane (ROBO042). Window: ~28 weeks. Start mid-July 2026 → experiments frozen
end of January 2027 → hard stop mid-February → fair ~March 2027. Capacity:
10–12 hrs/week (~220–290 effective hrs after holidays/exams). Compute: cloud for
training/rollouts. MacBook Air (dev + PushT demo) + GPU laptop (demo-capable, not
training).

---

## 0. Locked decisions

| # | Decision | Locked choice |
|---|---|---|
| 1 | Tasks (LIBERO) | **Revised 2026-08-02.** ~~3 assistive-flavored tasks: object handover, retrieve-dropped-object, container/drawer opening.~~ **Handover and retrieve-dropped-object do not exist in LIBERO** — verified against the BDDL files. Platform is the **`libero_object` suite**, per-suite training, one run; the 3 tasks are picked from *measured* per-task success rates at the Phase-0 gate, not named in advance. `DECISIONS.md` 2026-08-02. |
| 2 | Disturbances | object shift (headline + live demo), occlusion, delayed observation. Object-swap dropped. |
| 3 | Control signal | Inter-chunk consistency (STAC/TIDE-style: compare the newly generated chunk against the previously committed one over their temporal overlap). Single-inference, near-free. Conformal-calibrated threshold. |
| 3b | Demo signal | K-sample dispersion — used only for the live PushT confidence meter, where compute is irrelevant and intuitive explanation matters. Not the control signal. |
| 4 | Framing | Assistive committed. Asymmetric-cost evaluation is the headline contribution. |

**One-sentence claim (memorize):** A robot that detects disturbance-induced
failures and responds by adapting how far ahead it commits — and, evaluated under
an assistive cost model where a missed failure hurts someone but a false alarm is
a harmless pause, the detector that looks best by standard metrics turns out not
to be the safest to deploy.

## 1. What you are claiming (judge-safe, post-review)

**The thesis: prediction ≠ prevention.** Detection accuracy (AUROC) is a
precondition you report in passing, not a result. Every results claim leads with
downstream recovery utility and detection latency. This is the same argument as
the asymmetric-cost finding, so the whole project collapses into one coherent
point rather than two.

**Headline (N4 — the finding):** under an asymmetric cost model, the ranking of
detectors/thresholds flips relative to symmetric metrics. Nobody in the modern
generative-policy detector literature (Sentinel, FAIL-Detect, SAFE, ActProbe,
AEGIS, FIPER, Foresight) evaluates this way. Pure post-processing on logged data.

**Mechanism (M1 — the system):** horizon adaptation as the recovery response to
detected disturbance.

- **Guaranteed result:** matches always-replan's success at fewer denoising passes.
- **Proven-not-assumed:** the win comes from *when* it replans, not *how much* —
  established by the two controls in §4.
- **Own this caveat first:** benefit is conditional on signal quality. Say it
  before a judge does.

Prior-work distinction and never-claim list: see `CLAUDE.md`.

## 2. Phase map (28 weeks)

| Phase | Weeks | Dates | Output |
|---|---|---|---|
| 0 — Setup & baseline | 1–4 | Jul 17 – Aug 13 | DP reproduced on PushT + LIBERO tasks; logging schema live |
| 1 — Disturbances + detector | 5–10 | Aug 14 – Sep 24 | Disturbance injector; inter-chunk signal + conformal threshold; detector evaluated offline |
| 2 — Adaptive horizon + controls | 11–17 | Sep 25 – Nov 12 | 5-condition grid incl. budget-matched + placebo controls |
| 3 — Asymmetric cost (headline) | 18–22 | Nov 13 – Dec 17 | Cost post-processor; ranking-flip figure; sensitivity analysis |
| 4 — Stretch / buffer | 23–24 | Dec 18 – Dec 31 | If ahead: recoverability analysis from checkpoints. Else: catch-up. |
| 5 — Freeze, figures, demo, talk | 25–28 | Jan 1 – Jan 28 | Experiments frozen; figures; live demo; board; 5-min talk |
| Buffer | — | Feb → mid-Feb | Spillover only; nothing new started |

Capacity dips: Thanksgiving (Wk 19), winter break (Wk 23–24), January assessments
(Wk 27–28). **Front-load risk before Thanksgiving.**

## 3. Week-by-week

### Phase 0 — Setup & baseline (Wk 1–4)

- **Wk 1:** Check AWS Educate / student credits first (may zero the budget). Stand up cloud env. Install Diffusion Policy. Get PushT running on CPU end-to-end. Lock the asymmetric cost model on paper.
- **Wk 2:** Reproduce DP on one LIBERO task; confirm success rate near published. Identify the 3 task IDs. **Audit LIBERO-Plus / LIBERO-Pro for existing perturbation harnesses** — if either implements object shift or occlusion, adopt it and save ~2 weeks of Phase 1; if not, you've confirmed your injector is worth building. Budget 90 minutes.
- **Wk 3:** Stand up the logging schema before any real run. Prototype rollout+log loop on PushT.
- **Wk 4:** Train/verify DP on all 3 tasks. **Phase-0 gate.** Snapshot reproducible baseline. (Parallel: draft sponsor pitch — you now have a result to show.)

### Phase 1 — Disturbances + detector (Wk 5–10)

- **Wk 5:** Object-shift injector (headline), parameterized by magnitude × onset step. PushT first, then LIBERO. **The Wk-2 audit ran 2026-08-02 and found no adoptable harness** — LIBERO-Plus and LIBERO-PRO both perturb at episode initialization only, so this is a full build, not integration. Budget accordingly. Build on LIBERO's `set_state()` / `regenerate_obs_from_state()`; LIBERO-Plus's O2 target-pose code is reusable for computing the displacement.
- **Wk 6:** Add occlusion and delayed observation. Confirm each degrades success monotonically with magnitude — this sanity check is itself a result.
- **Wk 7:** Implement the inter-chunk consistency signal. One extra forward pass at decision points only. Log raw signal every step. (Also implement K-sample dispersion for the demo meter — PushT only.) **Normalize action dimensions using the policy's own action normalization before measuring any spread or chunk-to-chunk distance** — raw action dims have different scales (gripper bit vs. large translation), so an unnormalized signal is dominated by whichever dimension has the biggest raw units and the number means nothing. Cheap to get right now, invisible and expensive later.
- **Wk 8:** Split-conformal calibration on nominal rollouts for a target false-alarm rate. Evaluate detector offline: AUROC (gate) + detection latency (result).
- **Wk 9:** Optional second signal (chunk magnitude, ActProbe-style) only if separation is weak. Otherwise bank the time.
- **Wk 10:** **Phase-1 gate.** Freeze detector config.

### Phase 2 — Adaptive horizon + controls (Wk 11–17)

- **Wk 11:** Implement five conditions behind one interface: (a) fixed-long, (b) always-replan, (c) adaptive, (d) budget-matched blind trigger, (e) random-trigger placebo. (d) and (e) are the same rollout loop with a different trigger function — trivial code, but write the hooks now. Log replans-per-episode for all.
- **Wk 12:** Debug adaptive on PushT interactively — doubles as demo development.
- **Wk 13:** Pilot grid (1 task, conditions a–c, object-shift, few seeds). Confirm the mechanism before spending on the full grid.
- **Wk 14:** Headline grid: conditions a–c × 3 tasks × 3 disturbances × ≥5 seeds. Managed spot + checkpointing. Extract adaptive's mean replans/episode — this is the budget the controls must match.
- **Wk 15:** Run controls (d) and (e) at the matched budget, on the headline configuration only (object-shift × 3 tasks × seeds ≈ 30 extra cells, <20% added rollouts). Plus magnitude sweep on object-shift.
- **Wk 16:** **Phase-2 gate.** Draft figures. Verify the compute-savings arithmetic.
- **Wk 17:** Buffer / re-run. **Lock results before Thanksgiving.**

### Phase 3 — Asymmetric cost, the headline (Wk 18–22)

- **Wk 18:** Build the cost post-processor: read logged per-event detection times + outcomes, compute expected cost across a swept miss:false-alarm ratio. Offline; no new rollouts.
- **Wk 19 (Thanksgiving — light):** Generate the ranking-flip figure.
- **Wk 20:** Sensitivity analysis — over what cost-ratio range does the flip hold? A robust flip is much stronger than a single-point flip.
- **Wk 21:** Draft figures + the narration beat ("that fumble isn't a lost game — it's hot food on someone's lap").
- **Wk 22:** **Phase-3 gate.** All results exist in draft.

### Phase 4 — Stretch / buffer (Wk 23–24)

If ahead: recoverability analysis from the intermediate-state checkpoints — were
detected failures still recoverable at detection time? No re-running the grid.
If behind: pure catch-up. No new scope.

### Phase 5 — Freeze, figures, demo, talk (Wk 25–28)

- **Wk 25:** Experiment freeze. Finalize figures.
- **Wk 26:** Build the live PushT demo to fair quality (K-sample dispersion meter). Record the LIBERO video.
- **Wk 27:** Board + 5-min talk. Rehearse the prior-work rebuttals (§9).
- **Wk 28:** Dry-run the demo on the actual GPU laptop, offline, under fair conditions. Fix fragility.

## 4. The two controls (why they exist)

Your headline comparison invites one devastating objection: *"adaptive didn't win
because it replanned at the right moments — it won because it replanned more."*
Three conditions can't separate those. Two more can.

| Condition | Replan count | Timing | What it rules out |
|---|---|---|---|
| (d) Budget-matched blind | = adaptive's mean | Fixed even schedule, ignores signal | "Any extra replanning would have helped" |
| (e) Random-trigger placebo | = adaptive's mean | Uniformly random timesteps | "Even spacing was structurally lucky" |

Beat both at matched budget and exactly one explanation survives: the signal
identifies moments where replanning matters. This converts an assertion into a
demonstration, and it's the cheapest credibility in the whole project (~30 cells).

It also protects you. If adaptive ties the controls, that's a real, honest,
interesting finding — "replan frequency matters more than replan timing" — and a
far better talk than an unexplained null. **The controls yield a result either
way**, which matters because Phase 2 is the load-bearing risk.

**Sequencing:** these cannot run before Wk 14 (you must know adaptive's budget to
match it). Write the trigger hooks in Wk 11, run in Wk 15. **Earmark the compute
now** — the failure mode is spending the last of the budget on extra seeds in
January.

## 5. Experiment grid & figures

| Dimension | Levels |
|---|---|
| Condition | fixed-long, always-replan, adaptive, budget-matched blind, random placebo |
| Task | handover, retrieve-dropped, drawer/container |
| Disturbance | object-shift, occlusion, delayed-obs |
| Magnitude | sweep on object-shift only (3–4 levels); single representative level for the other two |
| Seeds | ≥5 per cell |

Conditions (d) and (e) run on the headline configuration only (object-shift), not
the full cross.

**Figures, ordered as they appear in the talk:**

1. **Ranking flip** — detector/threshold ranking under symmetric (AUROC) vs. asymmetric expected cost. *This is the headline.*
2. **Cost-ratio sensitivity** — the range over which the flip holds.
3. **Controls bar** — adaptive vs. budget-matched blind vs. random placebo at equal replan budget. The "timing, not spending" figure.
4. **Success + compute pair** — adaptive ≈ always-replan on success, at X% fewer denoising passes; both > fixed-long.
5. **Magnitude curve** — success vs. object-shift magnitude across conditions.
6. **Confidence trace** — one PushT episode: signal over time, disturbance onset marked, replan trigger firing. The demo, frozen.

## 6. Logging schema

> **Superseded.** The v1 schema that lived here has been replaced by the
> `[live]`/`[derived]` superset in **`SPEC.md`** (2026-07-26). The v1 version
> lacked provenance fields (`git_commit`, `config_hash`),
> `time_to_failure_at_detection`, `signal_value_demo`, and the live/derived
> distinction. Use `SPEC.md`.

Principles unchanged and still binding: raw per-event records, never aggregates —
any cost model must be recomputable retroactively, even the night before the fair.
`intermediate_state_ref` keeps the recoverability analysis addable without
re-running the grid. `total_replans` is what the controls match against.

## 7. Kill / decision criteria

| Gate | Pass condition | If it fails |
|---|---|---|
| Phase 0 (Wk 4) | **Revised 2026-08-02:** `libero_object` **suite average** (10 tasks × 50 eps) within **±5 points of the published 92.5%**, band declared before looking. ~~DP reproduces published success on 3 tasks~~ — not checkable: published numbers are per-suite averages, no per-task numbers exist, and **no released DP-on-LIBERO checkpoint was found**, so "reproduce" means train first | Drop to 2 tasks; ~~use released checkpoints~~ **that rung is broken — no DP-LIBERO checkpoint exists.** Nearest substitute is a released flow-matching VLA with LIBERO weights (`lerobot/pi0_libero_base`), which preserves the chunked-horizon mechanism at zero training cost but changes the policy from DP to π0 — unverified, investigate only if the gate is failing. Worst case PushT becomes the quantitative platform and LIBERO becomes video-only |
| Phase 1 (Wk 10) | Signal separates disturbed vs. nominal (AUROC clearly > chance); detection latency < time-to-failure on most episodes | Add chunk-magnitude second signal; if still weak, own it as the headline caveat and lean on the compute-savings floor (which doesn't need a great detector) |
| Phase 2 (Wk 16) | Adaptive matches always-replan at fewer passes and beats both controls at matched budget | If it ties the controls, report that honestly — it's a real finding. If the floor itself breaks, pivot framing to the measurement result (best detector ≠ best trigger) or the disturbance benchmark; the logged data supports both |
| Phase 3 (Wk 22) | Ranking flips across a plausible cost-ratio range | Report honestly that asymmetric cost preserves the ranking here — still a real measurement. Low risk: it's post-processing |

**Because you logged everything and picked assistive tasks, you are never one bad
result away from having no project.**

## 8. Five-minute talk

- **Hook (30s)** — the chunk-length dilemma: long chunks are smooth and cheap but blind mid-burst; short chunks are reactive but jittery and expensive.
- **Thesis (30s)** — prediction isn't prevention. Everyone scores failure detectors on whether they eventually notice. What matters is whether the robot does something useful in time.
- **System (45s)** — one diagram: inter-chunk consistency → conformal threshold → coast or replan.
- **Headline result (75s)** — Figures 1+2: under an assistive cost model, the best-by-AUROC detector is not the safest to deploy. The ranking flips.
- **Mechanism validated (30s)** — Figure 3: the win is timing, not compute. Budget-matched control and random placebo.
- **Live demo (90s)** — hand the judge the mouse. They drag the block, the meter spikes, the arm recovers, the baseline fumbles. Judge-caused = no cherry-pick suspicion.
- **Stakes (30s)** — a dropped object isn't a lost game; it's hot food on someone's lap. Symmetric metrics hide that.

## 9. Prior work — rebuttal answers

- **"Isn't this DVAC / DEHP / AutoHorizon / HiPolicy?"** → "Those optimize nominal-condition efficiency across task phases. I inject controlled external disturbances and evaluate detection latency plus downstream recovery under an asymmetric cost model. The horizon mechanism is shared; the disturbance framing and the cost lens are the contribution."
- **"Isn't this Rewind-IL?"** → "Rewind-IL recovers by respawning to a VLM-verified safe state. I recover by adapting the horizon, and I evaluate under asymmetric cost, which it doesn't."
- **"Isn't this AEGIS?"** → "AEGIS escalates to a stronger policy. I don't add a second policy — I change how far ahead the same policy commits."
- **"Why believe the win isn't just compute?"** → Figure 3. Budget-matched control and random placebo. *(Have the numbers memorized.)*
- **"Why is your detector better than Sentinel/ActProbe?"** → "It isn't necessarily — that's the point. I'm not claiming a better detector; I'm claiming the evaluation everyone uses ranks them wrong for deployment."
- **"Isn't this LIBERO-Plus / LIBERO-PRO?"** *(added 2026-08-02, from the audit)* → "Those perturb the **initial condition** and ask whether the policy still succeeds from a perturbed start. I perturb **during execution** and ask whether the policy notices in time to change what it commits to. Theirs is a robustness benchmark; mine is a detection-and-recovery experiment." Verified: all seven LIBERO-Plus axes and all four LIBERO-PRO axes are applied at scene setup, before rollout.
- **"Only three tasks, and they're all pick-and-place?"** *(own this first)* → "Correct — all three are `libero_object` grocery items, and task variety is not my generality axis. My generality axis is **PushT vs. LIBERO**: 2D planar pushing with keypoint observations and a 2-dim action space, versus 7-DoF manipulation from 128×128 RGB, two independently trained policies. The ranking flip holding across both is a stronger claim than three LIBERO tasks would be."

Papers to know cold: see `LITERATURE.md`.

## 10. Parallel tracks & budget

- **Sponsor/mentor:** start outreach Wk 4+, once you have a reproduced baseline. Pitch idea + preliminary result, not a cold ask. Target postdocs / senior PhD students.
- **Compute:** training light (~150–250 GPU-hrs); rollouts are the sink (~200–400 GPU-hrs), now including ~20% for the controls. Likely near the low end of $400–600, possibly $0. Prototype on PushT (CPU) before touching LIBERO GPUs. Spot + checkpointing is the ~70% lever.
  > **Provider — resolved for Phases 0–1 on 2026-07-31.** EC2 `g5.2xlarge` in `us-east-1`, account `051388699393`, $200 credit. **Still open for the Phase-2 grid.** The "no compute provider has been chosen" wording that stood here was v1 drafting and is stale.
  > **The GPU-hr numbers in this section are estimates and have never been measured.** ~$1.5/hr and the 350–650 GPU-hr range are both load-bearing — they are what says one account is not enough. First GPU session must time one rollout and one training epoch before anything else.
- **Registration:** confirm ScienceMontgomery 2027 dates and the abstract/registration deadline early — paperwork lands weeks before the fair.

## 11. Changelog vs. v1

1. Control signal switched from K-sample dispersion to inter-chunk consistency (single-inference; K-sampling costs 8× passes and undercuts the compute-savings headline). K-sample dispersion retained for the demo meter only.
2. Two controls added to Phase 2: budget-matched blind trigger and random-trigger placebo. Compute earmarked now, run Wk 15.
3. Asymmetric cost promoted to headline; adaptive horizon demoted to mechanism. Figure and talk order restructured.
4. Week-2 audit added for LIBERO-Plus / LIBERO-Pro perturbation harnesses.
5. Prior-work distinction rewritten — the "novel control axis" claim was false against the 2025–26 literature and is removed everywhere.
6. "Prediction ≠ prevention" made the explicit thesis; AUROC demoted to a reported gate.

Unchanged: tasks, disturbances, two-track LIBERO/PushT infra, assistive framing,
phase timeline, logging schema.
