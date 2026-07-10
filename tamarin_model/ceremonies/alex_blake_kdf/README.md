# Ceremony C0 — `alex_blake_kdf`

Mutual-nonce KDF ceremony (`SK = kdf(N_A, N_B)`) that hosts the Ceremony-Mask usability
analysis. Each **profile** is a self-contained Tamarin theory (a *profile* in the machinery §6.1
sense) that composes the shared spine plus the phase bundles / stressors it exercises. See
`../../../usability_extension_plan.md` (status in §0), `../../../mask_machinery_formalization.md`
(§6), and `../../../tamarin_model/MULTIPARTY_EXTENSIBILITY_PLAN.md` (the A–D consolidation) for design.

## Layout (V3 layered template — same as `secure_email`)

A profile entry reads as a short manifest — one `spine` line + one line per phase-kit + one line per
stressor. **To review an experiment, read its `P<N>_*.spthy`**: the includes ARE the story.

| Path | Role |
|---|---|
| `P<N>_<name>.spthy` | **Profile entry-point theories** (what you run). Each = `spine` + finish variant + human layer + phase kits + the stressors it arms + its lemmas. |
| `spine.spthy` | the universal "Alex derives the key" pipeline in ONE include: framework + `kdf` (nonce wire) + Alex's compute prompt + adapter + compute behaviour. |
| `phases/` | one **kit** per post-KDF control = its producer + behaviour + adapter (the parts that always co-occur): `approve`, `approve_shutout`, `verify`, `authorize`, `policy`. A profile adds the *stressor* separately (it's the experiment's variable). |
| `protocol/` | 🔵 `kdf`, `finish` / `finish_confirmed`, the prompt producers (`approval_ui`, `verify_ui`, …, `warning_ui`), `infer_harness` (P4), the compute adapters, `stress_alex` / `stress_blake`. |
| `interface/` | 🟠 one rule per control (`!Step`+`!StepData`+context): `sender` / `recipient` (compute), `nonce_ack` (σ2's second prompt). |
| `bundles/` | `human_manual` (mask_state + answered_once + outcome_policy + Alex enable) and `human_common` (= human_manual + `lexicon_tlx`). Swap-profiles (P7/P9/P10/P11) use `human_manual` + their own demand seed. |
| `experiments/` | Lemma-only files, one per profile. |
| `../../core/` | Reusable human layer: `masks/`, `stressors/`, `transitions/`, `mitigations`, `lexicon_tlx` / `interface_` / `population_` demand profiles. |

Each profile must be **closed** (every LHS fact has a producer) or Tamarin rejects it. Triggering is a
graded **dose-response**: the lexicon rates a step `'lo' < 'med' < 'hi'` and a detector fires on a BAND
(`!AtLeast(lvl, thr)`, order seeded in `core/types.spthy`). See
[`../../docs/V3_UNIFY_REALISM_PLAN.md`](../../docs/V3_UNIFY_REALISM_PLAN.md).

### Review map — what each profile composes

| Profile | finish | human | phases (+ stressor) | extra |
|---|---|---|---|---|
| P0 | plain | common | — | + recipient (Blake computes) |
| P1 | plain | common+blake | — (CALC: σ1+σ3+σ2) | + recipient + nonce_ack |
| P2 | plain | common | approve+σ8, verify+σ6, authorize+anxiety | + warning |
| P3 | plain | common+blake | CALC σ1σ3σ2 + approve+σ8 + verify+σ6 + authorize+anx | + recipient + nonce_ack + usability_properties |
| P4 | — | manual* | *(analyzer harness — bespoke, no spine)* | infer_harness |
| P5 | — | manual* | *(policy-only — bespoke, no spine)* | policy + both design seeds |
| P6 | **confirmed** | common | approve_shutout+σ8, verify+σ6 (σ1 on CALC) | + mitigations |
| P7 | plain | **manual** | verify+σ6, policy | + hardened_verify + clear_policy |
| P8 | plain | common | approve (+ induced σ3) | + adversary |
| P9 | plain | **manual** | — (CALC: σ1) | + population_expert |
| P10 | plain | **manual** | — (CALC: σ1 + additive) | + nonce_ack + moderate-demand seed |
| P11 | plain | **manual** | authorize (+ anxiety) | + moderate-arousal seed |

## Profile index

**12 profiles** (P0–P11). Each mask-mediated failure profile exercises ≥3 stressors; P10/P11 are
focused single-mechanism realism demonstrations.

| Profile (theory) | Scope | Stressors | Key lemmas |
|---|---|---|---|
| `P0_baseline` | layered pipeline, no stressor — the unperturbed baseline | — | `P0_completes`, `P0_agreement` |
| `P1_calc_pressure` | CALC under pressure, **both** parties | σ₁, σ₃-deadline, σ₂-concurrency | slip/timeout reachable, Blake slips, `P1_load_requires_enable`, `P1_busy_no_correct_key` (7) |
| `P2_postkdf_recovery` | APPROVE + VERIFY + AUTHORIZE, with recovery | σ₈, σ₆, SecurityAnxiety | auto-approve/mistake/abort reachable, `P2_recovery_requires_warning` (7) |
| `P3_worstcase` | maximal — all phases/masks/stressors, **both** parties (§6a) | all CALC + post-KDF | every failure reachable, Blake slips, composed safety (8) |
| `P4_inferred` | fully-inferred tier (analyzer direction), one merged poser | inferred σ₁, σ₆, σ₁₀, σ₉ | inferred slip/mistake/chaining/fatigue (6) |
| `P5_pathwayb` | **Pathway B** — task-mediated mistake, no mask change | σ₄ (presentation) | `P5_mistake_is_task_mediated_not_mask` (4) |
| `P6_mitigations` | three Poka-Yoke mitigations in one ceremony | σ₁, σ₈, σ₆ + fixes | `P6_no_slip_completion`, `P6_shutout_blocks_injected`, `P6_no_tampered_mistake` (6) |
| `P7_interface` | the interface lever: hardened verify (Effort 'lo') + clear policy | σ₆ (kept from firing) | `P7_no_abstraction`, `P7_no_mistake`, `P7_no_unsafe_policy` (6) |
| `P8_adversary` | adversary-INDUCED time pressure (no environmental stressor) | induced σ₃ | `P8_busy_requires_adv_urgency`, `P8_autoapprove_requires_adv` (3) |
| `P9_population` | expert population (low compute demand) via the band | σ₁ (cannot fire) | `P9_no_load`, `P9_no_slip` (3) |
| `P10_additive_load` | **§2c** two `'med'` steps sum past threshold (Sweller) | σ₁ + `additive_load` | `P10_no_solo_load`, `P10_additive_busy`, `P10_additive_slip` (4) |
| `P11_inverted_u` | **§2b** `'med'`-arousal facilitating zone (Yerkes-Dodson) | SecurityAnxiety (cannot fire) | `P11_no_anxiety_at_moderate`, `P11_authorize_granted`, `P11_no_abort` (3) |

All lemmas verify under Tamarin 1.12 / Maude 3.5.1; every profile proves in **≤ 5 min** (slowest
`P2_postkdf_recovery` ≈ 17 s).

## The four mechanisms behind the profiles

**One include per layer (readability / extensibility).** A profile reads top-to-bottom as its own
summary: crypto → `protocol/*` → `interface/*` → `bundles/human_common` → the stressor detectors it
arms → lemmas. **Adding a stressor to a profile is one include line**; adding a control is one
`interface/` rule. The stressor layer reads the **interface's** `!Step`, never the protocol.

**Per-participant targeting.** Every `core/stressors` rule reads `!StressEnable(P)`, so a stressor
fires only for an ENABLED party. `protocol/stress_alex.spthy` / `stress_blake.spthy` seed
`!StressEnable` off the persistent `!Party(p,id)` (from `protocol/kdf.spthy`). `human_common` enables
Alex by default; a multi-party profile adds `stress_blake` (P1, P3). An un-enabled party cannot be
stressed even when its trigger step is present — proven in P1 by `P1_load_requires_enable`.

**Every participant is mask-capable.** Both parties derive the key through the **interface**
(`interface/sender.spthy` for Alex, `interface/recipient.spthy` for Blake), so both are subject to
the mask machinery with no party-specific files — the KDF's old `blake_calc` special-case is gone.
The human layer keys on the party `P`, so Blake reuses it verbatim.

**Two failure pathways + mitigations.** Pathway A is mask-mediated (a stressor degrades the mask,
P1–P4); Pathway B is task-mediated (`P5`: an Attentive user errs from misleading terminology, no
mask change). `P6` carries the Poka-Yoke fixes: `shutdown` (key-confirmation, halts a slip),
`shutout` (number-matching MFA, blocks injected approval), and verify-shutout (device fingerprint
compare, blocks tampered acceptance) — each fix lemma proves the consequence is unreachable while
the degradation still arises.

## Design notes

**Persistent current mask (across action types).** The mask is not re-derived per action: each
stressor emits `SetMask(p,m)` at onset and the UI warning emits `SetMask(p,'Attentive')`; the gates
in `core/transitions/mask_state.spthy` make every f_H respond as the current mask, which carries
CALC_SK → APPROVE_REQ until a recovery (so a Busy user stays degraded at the approval prompt).
Encoded as "degrade active until recovery" — the tractable choice; strict latest-wins blows up once
several stressors interleave. `SetMask`-latching events are bounded once per party so the interval
reasoning terminates.

**P3 is the deliberate worst case (§6a/§6.5).** All stressors/masks/phases on both parties; if it
stops terminating, that is the §6a blow-up and the fix is to narrow the enabled set (drop a bundle
or stress one party). It currently proves in ≈2 s.

**Built:** masks Attentive, Busy, Careless, Habituated, Naive, Fearful (Elder out of scope — a
persona, not a stressor-induced mask); stressors σ₁ HighCognitiveLoad, σ₂ ExternalDistraction, σ₃
TimePressure, σ₄ MisleadingTerminology, σ₆ Abstraction, σ₈ Habituation, σ₉ AlertVolume,
SecurityAnxiety, σ₁₀ RepeatedFailure; phases CALC_SK, APPROVE_REQ, VERIFY_KEY, AUTHORIZE,
SET_POLICY; outcomes slip, auto_approve, timeout, mistake (Pathways A & B), abort; mitigations
`shutout`, `shutdown`, verify-shutout, and the recovery warning.

## Run

From the repo root (`stronger_usability_masks/`):

```bash
export PATH="$HOME/.local/bin:$PATH"
S=.claude/skills/model-tamarin
D=tamarin_model/ceremonies/alex_blake_kdf

# one profile
python3 $S/check.py --prove $D/P1_calc_pressure.spthy

# all profiles
for e in $D/P[0-9]_*.spthy; do python3 $S/check.py --prove "$e"; done

# interactive GUI — lists exactly the seven ToyCeremony_P* theories
tamarin-prover interactive $D/ --interface=127.0.0.1 --port=3001
```

## Adding a profile (or a stressor)

- **New stressor on an existing phase** → add `core/stressors/<sigma>.spthy` (read its trigger fact
  + `!StressEnable(P)`), then add one `#include` line to the relevant `bundles/<phase>_phase.spthy`.
  Every profile using that phase inherits it.
- **New mask f_H** → add `core/masks/<mask>_<action>.spthy` and include it in the phase bundle.
- **New profile** → write `experiments/P<N>_<name>.spthy` (lemmas only) and a `P<N>_<name>.spthy`
  entry = `ceremony.base.spthy` + `bundles/human_common.spthy` + the phase bundles it wants
  (+ `protocol/session.spthy` for any post-KDF phase) + the experiment. To stress Blake, skip
  `ceremony.base.spthy` and assemble `types` + `init` + `messages` +
  `protocol/blake_calc_stressable.spthy` + `stress_blake.spthy` directly (see P1 / P3).
- Keep the entry **closed**; re-run all profiles after touching any shared file (`ceremony.base`,
  a `bundles/*`, a `protocol/*`, or a reused `core/` fragment).
