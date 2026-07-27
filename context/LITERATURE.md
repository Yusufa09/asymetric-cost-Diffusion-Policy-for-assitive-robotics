# LITERATURE

Adaptive execution horizons, runtime failure detection & recovery for generative
robot policies. Background for the M1+N4 assistive-manipulation project.

**Update trigger:** phase gates (~5× total, ~20 min each) — see `MAINTENANCE.md`.

> **Currency warning.** AEGIS, ActProbe, Rewind-IL, DVAC, DEHP and most of §2 are
> Feb–Jul 2026 and post-date standard model training cutoffs. **Verify details
> against arXiv directly rather than against a model's recall**, and re-check the
> adaptive-horizon space at each phase gate — it is moving fast.

---

## §0 — The headline finding (read this first)

**The original novelty claim — "M1 gates *when to think*, a control axis nobody
occupies" — is no longer defensible** against a knowledgeable mentor or judge as
of mid-2026. Adaptive execution horizon driven by the policy's own uncertainty
became a populated subfield in the last year: at least a dozen 2025–26 papers vary
the horizon based on entropy, sample variance, denoising variance, attention
weights, or inter-chunk consistency (§2).

**AutoHorizon runs your exact originally-proposed signal as a baseline** —
Monte-Carlo variance over K sampled chunks, execute up to the first step where
variance exceeds a threshold — and finds it hyperparameter-sensitive and
computationally heavy relative to cheaper alternatives.

### Why this is not fatal, and is actually clarifying

Novelty ranks last in the project criteria, deliberately. Local-fair judges don't
audit literature. The demo and clean results are what clear ScienceMontgomery.

More importantly, the finding **reallocates the project's intellectual weight onto
the two things the field genuinely has not converged on:**

1. **Systematic external-disturbance robustness for adaptive horizon.** Nearly all
   adaptive-horizon work optimizes *nominal-condition* efficiency (fewer replans
   in predictable free-space, more in contact-rich phases). Almost none inject
   controlled external disturbances and measure detection latency + recovery. That
   framing lives in the failure-detection community, not the adaptive-horizon one
   — **and nobody has cleanly married the two.**
2. **Asymmetric-cost evaluation (N4).** Every modern generative-policy failure
   detector evaluates with symmetric metrics — AUROC, F1, Pareto frontiers. None
   use a cost model where a missed failure ≫ a false alarm. Cost-asymmetry exists
   in classical assistive-robotics anomaly detection but has never been brought to
   this modern benchmark line. **This is the only genuinely underclaimed lens.**

**Honest reframed claim:** an integrated system that detects disturbance-induced
failures and responds by adapting its execution horizon, evaluated under an
assistive asymmetric-cost model that reveals the detector which looks best by
standard metrics is not the safest to deploy. **The contribution is the
integration + the evaluation lens, not the horizon mechanism.**

## §1 — How the field got here

Through-line: behavior cloning → the multimodality problem → generative
(diffusion/flow) policies → action chunking → the consistency↔reactivity tradeoff
this whole project sits on.

- **Diffusion Policy** (Chi et al., RSS 2023; IJRR 2024) — **2303.04137**. Visuomotor policy as a conditional denoising diffusion process over action sequences. Solves BC's multimodality collapse (averaging "left" and "right" into "straight into the obstacle") by modeling a *distribution* over trajectories. **Critical for rebuttal-proofing: it is receding-horizon / closed-loop, not open-loop** — it replans continuously while maintaining temporal consistency. The blindness is a property of *long execution horizons*, not of diffusion. Code + PushT at `diffusion-policy.cs.columbia.edu`.
- **ACT** (Zhao et al., RSS 2023) — the first action-chunking policy: predict H future actions, execute a prefix, temporal-ensemble to smooth. DP adopted chunking; nearly every modern VLA (π0, π0.5, Octo, RDT, GR00T) predicts chunks via diffusion or flow matching.
- **BID — Bidirectional Decoding** (Liu et al., Aug 2024) — **2408.17355**. **The theoretical spine.** Formalizes the consistency↔reactivity inequality: longer chunks capture temporal dependencies better (fewer compounding errors in deterministic settings) but reduce reactivity in stochastic ones, because the policy sees fewer recent observations. BID keeps a *fixed* horizon but samples multiple candidate chunks per step and selects via backward coherence (agree with the last decision) + forward contrast (agree with a stronger policy, disagree with a weaker one). Push-T, RoboMimic, Franka Kitchen. **Read this to state the tradeoff rigorously — it's the "why does this problem exist" slide.**

**Lineage:** DP (receding horizon) → BID (sample selection at fixed horizon) → the
adaptive-horizon family (vary the horizon itself, §2). **M1 sits in the third bucket.**

## §2 — Adaptive execution horizon (the crowded core)

The subfield that eats the novelty claim. Organized by the signal that sets the
horizon. Shared premise everywhere: a fixed execution horizon is suboptimal; the
horizon should depend on task state / uncertainty / confidence.

| Method | arXiv / venue | Signal that sets the horizon | Note |
|---|---|---|---|
| **DVAC** (Denoising-Variance Adaptive Chunking) | **2606.03847** (Jun 2026) | Variance of clean-action estimates across final denoising steps, from a **single inference**; rolling-window threshold | π0.5-based: LIBERO 94.75%→98.00%, −43% replanning. **Closest to a "better" version of your signal.** |
| **DEHP** (Dynamic Execution Horizon Prediction) | **2606.11408** (Jun 2026) | Lightweight horizon-prediction branch trained with online RL, policy frozen (black-box compatible) | Learns when to replan from task progress. Explicitly "adapting the execution horizon." |
| **HiPolicy** | **2604.06067** | Action entropy via parallel stochastic inference; low entropy → high-freq closed-loop, high entropy → low-freq planning | Nearly identical motivation to the original chunk-entropy idea. |
| **MoH** (Mixture of Horizons) | 2025/26 | Predicts at multiple horizons in parallel, fuses; executes the longest prefix whose disagreement stays below threshold | Training-time multi-horizon; strong baseline to cite. |
| **AutoHorizon** ("VLA Knows Its Limits") | **2602.21445** | Attention weights set the horizon online | **Its appendix runs your exact MC-variance-over-K-chunks method as "Uncertainty Proxy" and finds it hyperparameter-sensitive and slow.** |
| Adaptive Action Chunking at Inference (Liang et al.) | CVPR 2026 | Action entropy (continuous + discrete) → optimal chunk size h* | Another entropy-based selector. |
| **SGAC** (Self-Guidance Adaptive Chunking) | So et al., 2025 | Cosine similarity between consecutive predicted chunks | Cheap consistency signal. |
| **VLA-Corrector** | **2607.01804** | Detect-and-correct → event-triggered adaptive horizon (long when reliable, short corrective replans on drift) | **Basically the "detector + adaptive horizon" combination**, on VLAs. Your nearest neighbor. |
| RA-DP (Rapid Adaptive Diffusion Policy) | **2503.04051** | Training-free high-frequency replanning via guidance + action queue | Extreme end: replan every denoising step. |
| When to Trust Imagination (World Action Models) | **2605.06222** | Compare predicted vs. real future observations (WAM self-verification) | Different signal class; good related-work survey of the space. |
| AutoSpeed / Adaptive Action Chunking (MDPI) | **2607.01051** / MDPI 2026 | Stage-adaptive speed / visual-context-predicted chunk length | Rounds out the "it's crowded" picture. |

**Bottom line for M1:** the mechanism (uncertainty → horizon) is well-trodden, and
variance-of-K-samples is a known, somewhat-dominated baseline. DVAC-style
denoising variance from a single inference is both cheaper and more current.

## §3 — Runtime failure detection for generative policies

The community the disturbance-and-detection framing actually belongs to. Evolution
is legible as a taxonomy of *where the failure signal comes from*.

- **Sentinel** (Agia et al., CoRL 2024) — **2410.04640**. The detector starting line. Splits failures into **erratic** (caught by **STAC** — Statistical Temporal Action Consistency, comparing overlapping action-chunk distributions across timesteps) and **task-progression** (caught by a VLM). Combining beats either alone by 18%. Code + released rollout datasets at `github.com/agiachris/sentinel` (built on EquiBot; **it does not train policies for you**). Use its datasets for **detector evaluation only** — they can't test recovery, which needs sim-in-the-loop.
- **FAIL-Detect** (Xu et al., TRI, RSS 2025) — **2503.08558**. "Can we detect failures without failure data?" Modular two-stage, uncertainty-aware, trained only on *successful* rollouts. robomimic (square, transport, tool_hang, can); diffusion or flow backbone. Code at `github.com/CXU-TRI/FAIL-Detect`.
- **SAFE** (Gu et al., 2025) — **2506.09937**. Multitask failure detection for VLAs from internal features; evaluates alert behavior on unseen tasks. ActProbe's strongest baseline.
- **FIPER** (Römer, Kobras, Worbis, Schoellig, NeurIPS 2025). Failure prediction at runtime for generative robot policies, from action chunks / policy features. (Rewind-IL reports beating it.)
- **ActProbe** (Jun 2026) — **2606.08508**. Pure action-space detector from a **single forward pass**: Temporal Consistency Error (TCE) between consecutive chunks + Action Chunk Magnitude (ACM), mapped to per-step failure probability by a task-conditioned LSTM-MLP. **Raises alarms before failures are visually recognizable**; improves the F1-vs-timeliness Pareto frontier. Cheapest credible detector; needs no internals.
- **AEGIS** (Jun 2026) — **2606.06660**. Activation-probe early warning: a lightweight probe on a *weak* policy's frozen activations flags high-risk steps; control escalates to a *stronger* policy only on flagged steps. On LIBERO-Spatial, recovers **10.1%** of otherwise-lost trajectories vs **4.6%** budget-matched blind escalation vs **5.1%** random-trigger placebo. **Its methodology is the single most important thing in this document (§8):** pre-registered contrasts, McNemar tests, and the two controls that prove gains come from *where* it acts, not from extra compute. States plainly that **accurate prediction does not imply effective prevention** (probe AUROC 0.764 is a precondition, not the headline).
- **Foresight** (Jun 2026) — **2606.23085**. Failure detection for long-horizon manipulation via action-conditioned world-model latents.
- **Adjacent:** UNISafe (world-model epistemic uncertainty + conformal + reachability latent safety filter, CoRL 2025, **2505.00779**); TAIL-Safe (task-agnostic safety watchdog, Lipschitz Q-function safe set, **2605.01195**); Farid et al. (failure prediction with conformal statistical guarantees for vision-based control, RSS 2022); AHA (VLM reasoning over failures, ICLR 2025); AED (adaptable error detection, NeurIPS 2024); PATCH, RC-NF, Code-as-Monitor (constraint/latent monitors, 2025–26); **an OpenVLA diagnostic study of activation warning signals under controlled visual shift (2606.29699) — directly relevant to your occlusion/shift disturbances.**

**Signal taxonomy to internalize:** action-space (ActProbe, STAC/TIDE) →
policy-internal/activation (AEGIS, SAFE) → world-model latent (Foresight, UNISafe)
→ VLM/semantic (Sentinel stage 2, AHA). **Cheaper single-forward-pass signals are
winning on the timeliness frontier.**

## §4 — Recovery: what to do after detection

Detection is only half the system. Your "adapt the horizon" response is a fourth,
underexplored axis.

- **Rewind-IL** (Zheng et al., Apr 2026) — **2604.16683**. **The closest full-stack analog.** Training-free. Detector = **TIDE** (Temporal Inter-chunk Discrepancy Estimate), calibrated with split conformal. Recovery = **state respawning**: a VLM selects semantically meaningful recovery checkpoints offline; on alarm the robot physically rewinds to the latest verified safe state and restarts inference from a clean policy state. On ACT; transfers to flow policies. **Already evaluates under adversarial disturbances — so "test under disturbances" is not itself novel.** Recovery axis = *where to reset to*.
- **AEGIS** (above). Recovery axis = *which policy runs* (escalate weak → strong).
- **TAIL-Safe** (**2605.01195**). Recovery = gradient-based correction toward an empirical safe set (Nagumo-inspired). Flow policies at 20–25% success under perturbations reach ~100% when guided. Recovery axis = *nudge the action*.
- **Classical assistive recovery** (the cost heritage): Park & Kemp, multimodal anomaly detection / execution monitoring for robot-assisted feeding (IROS 2016; Autonomous Robots 2018); grounded anomaly classification and recovery from external disturbances (**1809.03979**); human-in-the-loop failure recovery (**2602.03603**); Elly (haptic-intervention recovery + data collection, **2208.11845**). **These use cost-aware / safety-critical framing — the lineage N4 draws on.**

**Your recovery axis — adapt the execution horizon — is genuinely less occupied
than respawn, escalate, or nudge.** VLA-Corrector (§2) is the nearest, but on VLAs
and without the asymmetric-cost lens. **This is where the integration story lives.**

## §5 — Uncertainty estimation & conformal calibration (tooling)

- **Diff-DAgger** (Lee, Kang, Kuo, ICRA 2025). Uncertainty estimation with a diffusion policy, used to decide when to query an expert. The canonical "diffusion-policy uncertainty" reference — read it for *how to extract and use* a diffusion policy's own uncertainty.
- **Ensemble-based replanning** (Jutras-Dubé et al.; Punyamoorty et al.; RDM). Predictive uncertainty from an ensemble of inverse-dynamics models, or trajectory likelihood, triggers replanning. Impractical for real-time visual control (requires generating future states) but conceptually parallel to your trigger.
- **Conformal prediction** — Angelopoulos & Bates, *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification* — **2107.07511**. Split conformal converts a raw score into a threshold with a finite-sample, distribution-free false-alarm guarantee. **It is now table stakes** — Rewind-IL, FAIL-Detect, and UNISafe all use it. **Your plan to conformal-calibrate is well-aligned but is not a differentiator: treat it as hygiene, not contribution.**
- **TD calibration for VLAs** (Francis-Meretzki et al., **2604.20472**, 2026) — temporal-difference calibration in sequential tasks; relevant if you want something more sequential-aware than vanilla split conformal.

**The one honest subtlety to own:** sample dispersion / entropy **conflates
epistemic uncertainty (OOD — what you want) with legitimate task multimodality
(two valid ways to do the task).** This is why you calibrate empirically on
nominal-vs-disturbed rollouts rather than asserting "spread = danger." DVAC
sidesteps some of this by reading *denoising* variance rather than output-sample
spread — understand the distinction.

## §6 — Assistive robotics & the cost-asymmetry gap (where N4 lives)

A separate, older, more HRI-flavored community from the diffusion-policy
failure-detection one. Its relevance is specific and narrow: **it is where
cost-asymmetric, safety-critical evaluation actually appears.**

- Robot-assisted feeding surveys and safety work (e.g. Liu, Li, Hu 2025 systematic review; "Towards safety in physically assistive robots") frame the problem around unavoidable collisions, user safety, and the asymmetric stakes of getting it wrong — a missed anomaly can injure a person.
- Park & Kemp's assistive-feeding anomaly detection (§4) is the concrete methodological ancestor: multimodal execution monitoring where **false negatives are dangerous**.

**The gap you exploit:** none of the modern generative-policy detectors (Sentinel,
FAIL-Detect, SAFE, ActProbe, AEGIS, FIPER, Foresight) evaluate under an asymmetric
cost model. They report AUROC / F1 / timeliness Pareto — all symmetric. Bringing
the assistive community's cost-asymmetric lens to this modern benchmark line and
showing the **ranking flips** when a missed failure is priced far above a false
alarm is the project's most defensible intellectual move. **It is also cheap —
pure post-processing on logged detection times + outcomes.**

## §7 — Benchmarks & simulators

- **LIBERO** (Liu et al., NeurIPS 2023 D&B) — **2306.03310**. Four suites: LIBERO-Spatial, LIBERO-Object, LIBERO-Goal (10 tasks each), LIBERO-100/-90/-Long. Procedurally generated, human-teleoperated demos provided. **Task mapping is clean:** LIBERO-Object is "pick-place a unique object" (→ handover / retrieve framings); **LIBERO-Goal literally contains "open the middle drawer of the cabinet," "open the top drawer and put the bowl in," "turn on the stove,"** and several bowl-placement goals (→ drawer/container opening and assistive-flavored placements). **Confirm exact task IDs in Phase 0.**
- **LIBERO-Plus / LIBERO-Pro** (2025–26 extensions). Robustness/perturbation and anti-memorization variants. **Check these before building the disturbance injector** — someone may have already built perturbation harnesses you can borrow or must position against. (This is the Week 2 audit.)
- **PushT** — the 2D T-block pushing task from Diffusion Policy / Implicit BC (Florence et al.). CPU-cheap, interactive, ideal for the live demo. Used as an eval task in BID and many others.
- **RoboMimic** (square, transport, tool_hang, can) — standard IL benchmark, used by FAIL-Detect. **CALVIN, RoboTwin, ManiSkill3, Franka Kitchen** — other suites you'll see cited (DVAC uses LIBERO + RoboTwin + CALVIN).

## §8 — What this means for the project (strategic synthesis)

1. **Drop the "novel control axis" framing entirely.** If a mentor or strong judge hears "adaptive horizon is new," you lose credibility instantly. Reframe around integration + evaluation lens (§0).
2. **Steal AEGIS's control design — non-negotiable for legibility.** The headline M1 comparison is "adaptive vs. always-replan," and a skeptic's first objection is "you just spent more/less compute." AEGIS solves exactly this with a **budget-matched control** (same compute, dumb trigger) and a **random-trigger placebo**. Adopt both. It converts "our method wins" into "our method wins *because of where it decides to think*, not how much."
3. **Make "prediction ≠ prevention" the explicit thesis, not a caveat.** Detection AUROC is a precondition; what matters is downstream recovery utility. Lead with recovered-task-rate and detection latency; keep AUROC as a gate. This sets up N4 perfectly — it's the same argument.
4. **Consider a signal-design update.** The field has moved off MC-variance-over-K-chunks toward single-inference signals: DVAC's denoising variance, ActProbe's TCE + ACM, STAC/TIDE inter-chunk consistency. For both compute and defensibility these are stronger primaries. Keep K-sample dispersion as the demo meter if it visualizes better. *(Acted on — see `DECISIONS.md`, 2026-07-18.)*
5. **Conformal calibration is hygiene, not contribution.** Everyone does split conformal now. Include it, don't sell it.
6. **The two real contributions, stated for a mentor:**
   - **(a)** A controlled external-disturbance benchmark (object shift / occlusion / delayed observation, parameterized by magnitude × timing) evaluated by detection latency and downstream recovery, with the recovery mechanism being **execution-horizon adaptation** rather than respawn/escalate/nudge — a combination the disturbance-robustness and adaptive-horizon literatures haven't joined.
   - **(b)** An **asymmetric-cost evaluation** importing the assistive community's safety-critical framing into the modern generative-policy detector benchmark, demonstrating a **ranking flip** — a lens no paper in §3 uses.
7. **What a mentor will ask** — full rebuttal set in `PLAN.md` §9.

## §9 — Reading roadmap

**Tier 1 — know cold** (the spine + your direct neighbors):

1. Diffusion Policy (**2303.04137**) — foundation; the receding-horizon correction.
2. BID (**2408.17355**) — the consistency↔reactivity tradeoff, stated rigorously.
3. Sentinel (**2410.04640**) — STAC, the detector starting line; get the datasets.
4. AEGIS (**2606.06660**) — **for the methodology above all** (controls, placebo, prediction ≠ prevention).
5. Rewind-IL (**2604.16683**) — closest full-stack analog; conformal + recovery.
6. DVAC (**2606.03847**) — the strongest "better version" of your signal; single-inference variance.

**Tier 2 — know the idea and the one-line distinction:**

7. FAIL-Detect (**2503.08558**) — detection without failure data.
8. ActProbe (**2606.08508**) — cheapest action-space detector; TCE + ACM.
9. DEHP (**2606.11408**) — RL-learned adaptive horizon.
10. HiPolicy (**2604.06067**) — entropy-guided execution.
11. AutoHorizon (**2602.21445**) — **read the appendix** where your MC-variance signal is a baseline.
12. Diff-DAgger (ICRA 2025) — diffusion-policy uncertainty extraction.
13. Angelopoulos & Bates conformal primer (**2107.07511**) — the calibration tool.

**Tier 3 — reference as needed:**

14. SAFE (**2506.09937**), FIPER (NeurIPS 2025), Foresight (**2606.23085**), UNISafe (**2505.00779**), TAIL-Safe (**2605.01195**), Farid et al. (RSS 2022) — the rest of the detector/recovery landscape.
15. MoH, SGAC, VLA-Corrector (**2607.01804**), RA-DP (**2503.04051**), When to Trust Imagination (**2605.06222**) — the rest of the adaptive-horizon landscape.
16. LIBERO (**2306.03310**) + LIBERO-Plus/Pro — benchmark internals; check the perturbation variants before building yours.
17. Park & Kemp assistive-feeding anomaly detection + a robot-assisted-feeding survey — the cost-asymmetry heritage for N4.
