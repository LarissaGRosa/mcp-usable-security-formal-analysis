# Ceremony C0 — `alex_blake_kdf`

Mutual-nonce KDF ceremony (`SK = kdf(N_A, N_B)`) that hosts the Ceremony-Mask usability
analysis. Each **profile** is a self-contained Tamarin theory (a *profile* in the machinery §6.1
sense): a `#define FLAG` list (exactly what it arms) + `#include "base.spthy"` + its lemmas. See `../../MEMORY.md` for the build lessons (lessons 18–19 cover consolidation and prompt/perform).

## Layout (flat — one file per layer, `#ifdef`-gated)

**To review a profile, read its `#define` list**: the flags ARE the story. `base.spthy` `#define`s
the wire-profile constants (init + nonce wire + compute pipeline + Alex targeting) and assembles the
layers; every selectable rule is wrapped in `#ifdef FLAG` in a merged file, so a profile compiles in
exactly what it names. Preprocessed output is byte-identical to hand-including the old fragments.

**Prompt/perform seam.** The interface (`interface.spthy` + the `UI_*`/`INFER_HARNESS` producers in
`protocol.spthy`) only POSES prompts — `!Prompt(P,pid,action)` + `!Displayed(P,pid,shown)`. The
detectors read `!Prompt`; the user's mask (`core/masks.spthy`) reads `!Prompt`+`!Displayed`, PERFORMS
the step, and commits `!StepData` only where a rule needs the value. The `FINISH_CONFIRMED` shutdown
compares the human's produced key against the interface's `!Displayed` correct key `kdf(N_A,N_B)`.

| Path | Role |
|---|---|
| `P<N>_<name>.spthy` | **Profile theories** (what you run). Each = `#define` flags + `#include "base.spthy"` + its lemmas. (P4/P5 are custom: they assemble the merged files directly, no `base`.) |
| `base.spthy` | the "Alex derives the key" pipeline as `#define`s (`KDF_INIT`, `KDF_WIRE`, `COMPUTE_KEYRESULT`, `MASK_COMPUTE`, `IF_CALC_ALEX`, `STRESS_ALEX`) + the layer `#include`s. |
| `protocol.spthy` | 🔵 all protocol/UI producers, each `#ifdef`-gated: `KDF_INIT`, `KDF_WIRE`, `FINISH_PLAIN`/`FINISH_CONFIRMED`, `UI_APPROVE`/`UI_APPROVE_SHUTOUT`/`UI_VERIFY`/`UI_AUTHORIZE`/`UI_POLICY`/`UI_WARNING`, `STRESS_ALEX`/`STRESS_BLAKE`, `INFER_HARNESS`, the compute adapters. |
| `interface.spthy` | 🟠 `IF_CALC_ALEX` / `IF_CALC_BLAKE` (compute prompts) + `IF_NONCE_ACK` (σ2's second prompt). |
| `../../core/` | `framework.spthy` (types+transitions+outcome matrix, always on), `masks.spthy` (`#ifdef MASK_*`), `stressors.spthy` (`#ifdef SIGMA*`), `demands.spthy` (`#ifdef LEXICON_DEFAULT`/`IF_HARDENED`/`IF_CLEAR`/`IF_MISLEADING`/`POP_EXPERT`), `knobs.spthy` (`#ifdef ADVERSARY`/`MITIGATIONS`), `properties.spthy` (`#ifdef PROPERTIES`). |

A "phase" (a post-KDF control) is now two flags a profile names together: e.g. VERIFY = `UI_VERIFY`
(the producer in `protocol.spthy`) + `MASK_COMPARE` + `MASK_COMPARE_KEYCHECKED` (the behaviour in
`masks.spthy`). Each profile must be **closed** or Tamarin rejects it. Triggering is a graded
**dose-response**: the demand profile rates a step `'lo' < 'med' < 'hi'` and a detector fires on a BAND
(`!AtLeast(lvl, thr)`, order seeded in `core/framework.spthy`).

### Review map — what each profile arms (its `#define`s)

| Profile | finish | demand | phase flags (+ stressor) | extra |
|---|---|---|---|---|
| P0 | `FINISH_PLAIN` | `LEXICON_DEFAULT` | — | `IF_CALC_BLAKE` (Blake computes) |
| P1 | `FINISH_PLAIN` | `LEXICON_DEFAULT` | — (CALC: σ1+σ3+σ2) | `IF_CALC_BLAKE`, `IF_NONCE_ACK`, `STRESS_BLAKE` |
| P2 | `FINISH_PLAIN` | `LEXICON_DEFAULT` | `UI_APPROVE`+`MASK_CONFIRM`+σ8, `UI_VERIFY`+`MASK_COMPARE`+σ6, `UI_AUTHORIZE`+`MASK_AUTHORIZE`+anx | `UI_WARNING` |
| P3 | `FINISH_PLAIN` | `LEXICON_DEFAULT` | CALC σ1σ3σ2 + approve+σ8 + verify+σ6 + authorize+anx | `IF_CALC_BLAKE`, `IF_NONCE_ACK`, `STRESS_BLAKE`, `PROPERTIES` |
| P4 | *(custom)* | `LEXICON_DEFAULT` | *(analyzer harness — no base)* | `INFER_HARNESS`, `COMPUTE_OPRESULT`, σ1/σ6/σ10/σ9 |
| P5 | *(custom)* | `IF_CLEAR`+`IF_MISLEADING` | *(policy-only — no base)* | `UI_POLICY`, `MASK_POLICY` |
| P6 | `FINISH_CONFIRMED` | `LEXICON_DEFAULT` | `UI_APPROVE_SHUTOUT`+`MASK_CONFIRM`+σ8, verify+σ6 (σ1 on CALC) | `MITIGATIONS` |
| P7 | `FINISH_PLAIN` | `IF_HARDENED`+`IF_CLEAR` | verify+σ6, `UI_POLICY`+`MASK_POLICY` | — |
| P8 | `FINISH_PLAIN` | `LEXICON_DEFAULT` | `UI_APPROVE`+`MASK_CONFIRM` (+ induced σ3) | `ADVERSARY`, `SIGMA_INDUCED_TIME` |
| P9 | `FINISH_PLAIN` | `POP_EXPERT` | — (CALC: σ1) | — |
| P10 | `FINISH_PLAIN` | *(inline moderate seed)* | — (CALC: σ1 + additive) | `IF_NONCE_ACK` |
| P11 | `FINISH_PLAIN` | *(inline moderate seed)* | `UI_AUTHORIZE`+`MASK_AUTHORIZE` (+ anxiety) | — |

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
`P2_postkdf_recovery` ≈ 6 s; the whole 12-profile sweep ≈ 30 s).

## The four mechanisms behind the profiles

**One flag per selectable rule (readability / extensibility).** A profile reads top-to-bottom as its
own summary: its `#define` list names the finish variant, demand profile, phases and stressors it
arms; `#include "base.spthy"` pulls in every layer, and the `#ifdef` guards compile in exactly the
named rules. **Adding a stressor to a profile is one `#define` line**; adding a control is one
`#ifdef`-guarded rule in `protocol.spthy`/`interface.spthy`. The stressor layer reads the
**interface's** `!Prompt`, never the protocol.

**Per-participant targeting.** Every stressor rule (`core/stressors.spthy`) reads `!StressEnable(P)`,
so a stressor fires only for an ENABLED party. `protocol.spthy`'s `STRESS_ALEX` / `STRESS_BLAKE`
blocks seed `!StressEnable` off the persistent `!Party(p,id)`. `base.spthy` enables Alex by default;
a multi-party profile adds `#define STRESS_BLAKE` (P1, P3). An un-enabled party cannot be stressed
even when its trigger step is present — proven in P1 by `P1_load_requires_enable`.

**Every participant is mask-capable.** Both parties derive the key through the **interface**
(`IF_CALC_ALEX` for Alex, `IF_CALC_BLAKE` for Blake, both in `interface.spthy`), so both are subject
to the mask machinery with no party-specific files. The human layer keys on the party `P`, so Blake
reuses it verbatim.

**Two failure pathways + mitigations.** Pathway A is mask-mediated (a stressor degrades the mask,
P1–P4); Pathway B is task-mediated (`P5`: an Attentive user errs from misleading terminology, no
mask change). `P6` carries the Poka-Yoke fixes: `shutdown` (key-confirmation, halts a slip),
`shutout` (number-matching MFA, blocks injected approval), and verify-shutout (device fingerprint
compare, blocks tampered acceptance) — each fix lemma proves the consequence is unreachable while
the degradation still arises.

## Design notes

**Persistent current mask (across action types).** The mask is not re-derived per action: each
stressor emits `SetMask(p,m)` at onset and the UI warning emits `SetMask(p,'Attentive')`; the gates
in `core/framework.spthy` (the mask-state section) make every f_H respond as the current mask, which carries
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
for e in $D/P*.spthy; do python3 $S/check.py --prove "$e"; done

# interactive GUI — lists exactly the twelve ToyCeremony_P* theories
tamarin-prover interactive $D/ --interface=127.0.0.1 --port=3001
```

## Adding a profile (or a stressor)

- **New stressor** → add one `#ifdef SIGMA_NEW … #endif` block to `core/stressors.spthy` (read its
  trigger fact + `!StressEnable(P)`); a profile arms it with `#define SIGMA_NEW`. Shared across both
  ceremonies automatically.
- **New mask f_H** → add an `#ifdef MASK_NEW`-guarded rule to `core/masks.spthy`; arm with `#define MASK_NEW`.
- **New control (phase)** → add its producer as an `#ifdef UI_NEW` block in `protocol.spthy` (or
  `interface.spthy`); a profile arms `UI_NEW` alongside the `MASK_*` its behaviour needs.
- **New profile** → write `P<N>_<name>.spthy` = `theory … begin`, a `#define` list, `#include "base.spthy"`,
  the lemmas, `end`. To stress Blake add `#define STRESS_BLAKE` (+ `IF_CALC_BLAKE` if he computes).
  For a demand-profile swap (expert / hardened / inline seed), name the demand flag instead of `LEXICON_DEFAULT`.
- Keep the theory **closed**; re-run all profiles after touching any shared file (`base.spthy`,
  `protocol.spthy`, `interface.spthy`, or a `core/*.spthy`).

---

## Prover budget & timings

**Hard requirement: every theorem proves in under 3 minutes**, run capped (the box has no swap):

```bash
export MAUDE_LIB=/usr/share/maude
python3 .claude/skills/model-tamarin/check.py --prove --timeout 178 \
        ceremonies/alex_blake_kdf/K4_worstcase.spthy -- +RTS -M6G -RTS
```

### P-profiles — the PUBLIC-wire testbed (`KDF_WIRE`)

| P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | P11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1s | 1s | 25s | 11s | 2s | 0s | 2s | 1s | 1s | 0s | 1s | 0s |

### K-profiles — the invented PRIVATE messenger (`KDF_MESSENGER`)

The nonces cross a private `Chat()`, so the adversary learns one **only** on a human mistake. That is
what makes the (S) goal statable at all here: `sk = kdf(Na,Nb)` and `kdf/2` is FREE, so **K(sk) requires
BOTH nonces** — leaking one is provably insufficient (`H_sk_requires_both_leaks`). The public-wire
P-profiles cannot state this: their nonces are already on the DY channel.

| Profile | stressor | headline | time |
|---|---|---|---|
| `K0_baseline` | — | both parties complete, keys agree, secrecy ABSOLUTE | 1s |
| `K1_send_code` | σ1 (Busy) | nonce TYPO caught by the key-confirmation shutdown (safe-fail) vs WRONG CHAT → `Out(nonce)` | 5s |
| `K2_leak` | σ2 (Careless) | in-band leak — the partner still receives it, so nothing looks wrong (SILENT) | 3s |
| `K3_premature` | `OUTCOME_PREMATURE` | "start session" pressed BEFORE the key read-back → `SessionUnconfirmed` | 4s |
| `K4_worstcase` | both parties | the breach is REACHABLE — and only by BOTH of them leaking | 28s |

`K3` is the same core order-violation lever proved in `secure_email` (`SendPremature`): **one lever, two
ceremonies** — the RFC-grade generality claim.

## What keeps it in budget

Same discipline as `secure_email` (see its README): density detectors read a SINGLE marker (σ2 →
`!Copresent`, σ9 → `!CopresentDecide` via the dedicated surfaces), every `Prompt` is posed off a shallow
source, and the boundary list is proven once as `[reuse]` so each profile's T6 costs ~12 steps. The
P4 harness stays **token-bounded** (a fixed budget of `OpToken`/`DecToken` consumed by the posers) rather
than restriction-bounded.

## See also

- [`INTERFACE_MAP.md`](INTERFACE_MAP.md) — the invented messenger's screens (design), with an as-built caveat.
- [`../../docs/DIVERGENCES.md`](../../docs/DIVERGENCES.md) — **what was not built and why** (the K2 MITM
  compare and the K3 key-entry field are NOT modelled).
