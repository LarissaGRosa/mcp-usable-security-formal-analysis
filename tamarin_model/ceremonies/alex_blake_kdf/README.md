# Ceremony C0 — `alex_blake_kdf`

Mutual-nonce KDF ceremony (`SK = kdf(N_A, N_B)`) that hosts the Ceremony-Mask usability
analysis. Each **profile** is a self-contained Tamarin theory (a *profile* in the machinery §6.1
sense) that composes the shared spine plus the phase bundles / stressors it exercises. See
`../../../usability_extension_plan.md` (status in §0), `../../../mask_machinery_formalization.md`
(§6), and `../../../tamarin_model/MULTIPARTY_EXTENSIBILITY_PLAN.md` (the A–D consolidation) for design.

## Layout

| Path | Role |
|---|---|
| `ceremony.base.spthy` | **Shared spine** (`#include`-d, not standalone): core types + `protocol/init` + `protocol/messages` (Msg1/Msg2) + `protocol/blake_calc` (Blake's default Attentive CALC_SK). |
| `P<N>_<name>.spthy` (e.g. `P1_calc_pressure.spthy`) | **Profile entry-point theories** — each composes the spine + bundles + its lemmas. *These are what you run.* |
| `bundles/` | **Phase bundles**: one include per ceremony phase = its producer + every mask for it + every stressor targeting it (`calc_phase`, `approve_phase`, `verify_phase`, `authorize_phase`), plus `human_common` (the gates + Alex enable). |
| `protocol/` | Protocol-layer fragments: `init`, `messages`, Blake's CALC_SK (`blake_calc` default / `blake_calc_stressable` opt-in), the Msg3 variants (`msg3_inline` / `msg3_request` / `msg3_request_confirmed`), the UI phases, `infer_harness` (the inferred-tier poser), and the `stress_alex` / `stress_blake` enables. |
| `experiments/` | Lemma-only files, one per profile (same `P<N>_<name>`). |
| `../../core/` | The reusable, party-generic human layer: `masks/`, `stressors/`, `transitions/`, `mitigations`. |

Each profile must be **closed** (every LHS fact has a producer) or Tamarin rejects it — see the
wellformedness note in the plan's Appendix A.

## Profile index

The model is **7 profiles** (consolidated from the original 21 single-construct experiments; Stage D
of the multi-party plan). Each mask-mediated profile exercises **≥3 stressors**.

| Profile (theory) | Scope | Stressors | Key lemmas |
|---|---|---|---|
| `P0_baseline` (`ToyCeremony_P0_Baseline`) | Attentive inline KDF — the unperturbed baseline | — | `P0_completes`, `P0_agreement` |
| `P1_calc_pressure` (`ToyCeremony_P1_CalcPressure`) | CALC_SK under pressure, on **both** Alex and Blake | σ₁, σ₃, σ₂ | slip/timeout reachable, Blake slips, `P1_load_requires_enable`, `P1_busy_no_correct_key` (7) |
| `P2_postkdf_recovery` (`ToyCeremony_P2_PostKdfRecovery`) | APPROVE + VERIFY + AUTHORIZE under stress, with recovery | σ₈, σ₆, SecurityAnxiety | auto-approve/mistake/abort reachable, `P2_recovery_requires_warning`, `P2_mistake_requires_abstraction` (7) |
| `P3_worstcase` (`ToyCeremony_P3_WorstCase`) | the maximal profile — all phases/masks/stressors on **both** parties (§6a) | all CALC + post-KDF | every failure reachable, Blake slips, composed safety (8) |
| `P4_inferred` (`ToyCeremony_P4_Inferred`) | the fully-inferred tier (analyzer direction), one merged poser | inferred σ₁, σ₆, σ₁₀, σ₉ | inferred slip/mistake/chaining/fatigue, `P4_escalation_requires_failure` (6) |
| `P5_pathwayb` (`ToyCeremony_P5_PathwayB`) | **Pathway B** — task-mediated mistake, no mask change | σ₄ (presentation) | `P5_mistake_is_task_mediated_not_mask`, `P5_mistake_requires_misleading` (4) |
| `P6_mitigations` (`ToyCeremony_P6_Mitigations`) | three Poka-Yoke mitigations in one ceremony | σ₁, σ₈, σ₆ + fixes | `P6_no_slip_completion`, `P6_shutout_blocks_injected`, `P6_no_tampered_mistake` (6) |

All **40 lemmas** verify under Tamarin 1.12 / Maude 3.5.1; each profile proves in **≤4 s** (slowest:
P4 ≈ 3.8 s).

## The four mechanisms behind the profiles

**Phase bundles (extensibility / Stage C).** `bundles/` groups each ceremony phase into one include:
its producer + every mask for it + every stressor targeting it. So **adding a stressor is one
include line in a bundle** (every profile using that phase inherits it), and **a new profile is the
spine + `human_common` + the phase bundles it wants + lemmas**. Post-KDF bundles need
`protocol/session.spthy` and a CALC producer. The recovery warning and σ₉/σ₁₀ inference stay out of
the basic bundles (special posers; `Inequality` would clash if the σ₈ and σ₉ bundles were combined).

**Per-participant targeting (Stage B).** Every `core/stressors` rule reads `!StressEnable(P)`, so a
stressor fires only for an ENABLED party. `protocol/stress_alex.spthy` / `stress_blake.spthy` each
seed `!StressEnable` for one party off the persistent `!Party(p,id)` (from `protocol/init.spthy`). A
profile includes the enable for whoever it stresses; an un-enabled party cannot be stressed even
when its trigger fact is present — proven in P1 by `P1_load_requires_enable` (a stressor onset
implies the party was enabled first).

**Every participant is mask-capable (Stage A).** Blake no longer computes the key inline:
`protocol/messages.spthy` leaves him at `BlakeWait`, and his CALC_SK is answered by a separate
fragment. The spine default (`protocol/blake_calc.spthy`) answers Attentive and posts **no** `!Req`,
so Blake is inert to the detectors unless a profile opts in. A profile that stresses Blake skips
`ceremony.base.spthy` and pulls `protocol/blake_calc_stressable.spthy` (a `'Hard'` `!Req` the SHARED
σ₁/σ₃/σ₂ + core masks degrade) — P1 and P3 do this. The human layer keys on the party `P`, so Blake
reuses it with no Blake-specific files.

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
