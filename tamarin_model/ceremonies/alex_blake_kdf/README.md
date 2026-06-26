# Ceremony C0 — `alex_blake_kdf`

Mutual-nonce KDF ceremony (`SK = kdf(N_A, N_B)`) that hosts the Ceremony-Mask usability
experiments. Each **experiment** is a self-contained Tamarin theory — a *profile* in the
machinery §6.1 sense — that `#include`s the shared spine plus the one mask / stressor /
transition it exercises. See `../../../usability_extension_plan.md` (status in §0) and
`../../../mask_machinery_formalization.md` (§6) for the design.

## Layout

| Path | Role |
|---|---|
| `ceremony.base.spthy` | **Shared spine** (`#include`-d, not a standalone theory): core types + `protocol/init` + `protocol/messages` (Msg1/Msg2). |
| `NN_<name>.spthy` (e.g. `01_busy_under_load.spthy`) | **Entry-point theories** — each = `base` + its deltas + one experiment. *These are what you run.* The `NN` prefix gives build order. |
| `protocol/` | Protocol-layer fragments: `init`, `messages`, the Msg3 variants `msg3_inline` / `msg3_request`, and the `approval_ui` phase. |
| `experiments/` | Lemma-only files, one per experiment (same `NN_<name>` as its entry). |
| `../../core/` | The reusable human layer: `masks/`, `stressors/`, `transitions/`. |

Each entry reads as a manifest: `base` + exactly the constructs that experiment adds. An
entry must be **closed** (every LHS fact has a producer) or Tamarin rejects it — see the
wellformedness note in the plan's Appendix A.

## Experiment index

| Entry (theory) | Stressor → mask → outcome | Msg3 variant | Failure semantics | Lemmas |
|---|---|---|---|---|
| `00_baseline.spthy` (`ToyCeremony_Baseline`) | — (Attentive only) | inline | baseline: Agreement + Liveness | `L0_completes`, `L0_agreement` |
| `01_busy_under_load.spthy` (`ToyCeremony_BusyUnderLoad`) | σ₁ HighCognitiveLoad → **Busy** → `slip` | request/ack | **unsafe-success** (wrong key, completes) | `L1_*` (5) |
| `02_habituated_mfa.spthy` (`ToyCeremony_HabituatedMFA`) | σ₈ Habituation → **Habituated** → `auto_approve` | inline + approval UI | **unsafe-success** (approves injected prompt) | `L2_*` (5) |
| `03_careless_distraction.spthy` (`ToyCeremony_CarelessDistraction`) | σ₂ ExternalDistraction → **Careless** → `timeout` | request/ack | **safe-fail** (ceremony stalls) | `L3_*` (5) |
| `04_multi_stressor.spthy` (`ToyCeremony_MultiStressor`) | **σ₁ + σ₂ + σ₈** together → {Busy, Careless, Habituated} | request/ack + approval UI | **interaction + persistence** (mask carries across steps) | `LM_*` (7) |
| `05_warning_recovery.spthy` (`ToyCeremony_WarningRecovery`) | σ₈ Habituation → **Habituated**, then **UI warning → back to Attentive** | inline + approval UI + warning | **recovery** (mask persists, then re-engages) | `L5_*` (5) |
| `06_abstraction_naive.spthy` (`ToyCeremony_AbstractionNaive`) | σ₆ Abstraction → **Naive** → `mistake` | inline + **VERIFY_KEY** phase | **unsafe-success** (accepts a tampered fingerprint) | `L6_*` (4) |
| `07_anxiety_fearful.spthy` (`ToyCeremony_AnxietyFearful`) | SecurityAnxiety → **Fearful** → `abort` | inline + **AUTHORIZE** phase | **safe-fail** (active refusal / withdrawal) | `L7_*` (4) |
| `08_timepressure_busy.spthy` (`ToyCeremony_TimePressureBusy`) | σ₃ TimePressure → **Busy** → `slip` | request/ack | **unsafe-success** (2nd route into Busy) | `L8_*` (4) |
| `09_all_stressors.spthy` (`ToyCeremony_AllStressors`) | **all 6 stressors → all masks**, all phases + recovery | request/ack + approval + VERIFY + AUTHORIZE + warning | **maximal**: every failure still reachable; safety composes | `L9_*` (7) |
| `10_inferred_load.spthy` (`ToyCeremony_InferredLoad`) | σ₁ **inferred** from `op='kdf'` → Busy → slip | `!Op` compute (operation-inference) | inference is sound (load only from a posed kdf) | `L10_*` (4) |
| `11_inferred_abstraction.spthy` (`ToyCeremony_InferredAbstraction`) | σ₆ **inferred** from `op='verify'` → Naive → mistake | `!Op` verify (operation-inference) | accepts a tampered fingerprint | `L11_*` (4) |
| `12_inferred_repeated_failure.spthy` (`ToyCeremony_InferredRepeatedFailure`) | σ₁₀ **inferred** from a prior `!Failed` → Careless | token-bounded ops (trace-inference) | **chaining** σ₁→σ₁₀ | `L12_*` (3) |

Lemma prefixes `L0_`…`L3_` track the `00`…`03` ordinal; the merged experiment uses `LM_`, recovery `L5_`,
the new ones `L6_`/`L7_`/`L8_`, and the maximal one `L9_`.
All 59 lemmas verify under Tamarin 1.12 / Maude 3.5.1, each experiment in **≤2 s**.

**Two families.** Experiments 00–09 *declare* the stressor (a trigger wired to a named request).
Experiments **10–12** *infer* it from the ceremony itself (the usability-analyzer goal): the step
records the **objective operation** `!Op(P,rid,optag,…)` or the **trace** (`!Failed`), and a `core/`
detector infers the stressor — operation-inference (10: σ₁ from `'kdf'`, 11: σ₆ from `'verify'`) and
trace-inference (12: σ₁₀ from a prior failure, with chaining σ₁→σ₁₀). Detectors key on the operation
**tag**, never by destructuring the term (MEMORY.md #11).

**Built:** masks Attentive, Busy, Careless, Habituated, Naive, Fearful (Elder ✂️ out of scope — a persona, not a stressor-induced mask); stressors σ₁
HighCognitiveLoad, σ₂ ExternalDistraction, σ₃ TimePressure, σ₆ Abstraction, σ₈ Habituation, SecurityAnxiety;
phases CALC_SK, APPROVE_REQ, VERIFY_KEY, AUTHORIZE; outcomes slip, auto_approve, timeout, mistake, abort.

**Persistent current mask (across action types).** The mask is not re-derived per action: each
stressor emits `SetMask(p,m)` at onset and the UI warning emits `SetMask(p,'Attentive')`; the gates in
`core/transitions/mask_state.spthy` make every f_H respond as the current mask, which carries CALC_SK →
APPROVE_REQ until a recovery. So a user driven **Busy** on the KDF stays degraded at the approval prompt
(Busy → `auto_approve` via `busy_approve`, Careless → `timeout` via `careless_approve`), proven by
`LM_mask_persists_across_actions`. Encoded as "degrade active until recovery" (the tractable choice;
strict latest-wins blows up on the merged experiment).

**Experiment 05 adds the first way BACK to Attentive** (plan §5/§7 recovery): the Habituated mask
persists across prompts until a good-usability UI warning (`protocol/warning_ui.spthy`) emits a recovery
`SetMask('Alex','Attentive')` that supersedes the degrade — read by the current-mask gates in
`core/transitions/mask_state.spthy` (no stored mask, no separate recovery file). The `SetMask`-latching
events are bounded once per party (`OnceHabituate`, `OneSetMaskPerMask`) — without that the
warning/habituation rules re-fire unboundedly and the gates' interval reasoning never terminates; the
bound keeps it ≤2 s and is semantically a no-op. Modelling repeated habituate↔recover *cycles* would
relax those bounds.

**Experiment 04 is the deliberate multi-stressor "worst-case" profile** (machinery §6a/§6.5):
it enables all three stressors and four masks on one human to study how they *interact* —
e.g. `LM_compound_failure` shows a single run in which Alex both slips on the KDF (Busy) and
later auto-approves an injected prompt (Habituated). It stays tractable only because the
model is single-human + monotone + single-active-per-stressor; if it stops terminating, that
is the §6a blow-up and the fix is to narrow the enabled set.

## Run

From the repo root (`stronger_usability_masks/`):

```bash
export PATH="$HOME/.local/bin:$PATH"
S=.claude/skills/model-tamarin
D=tamarin_model/ceremonies/alex_blake_kdf

# one experiment
python3 $S/check.py --prove $D/01_busy_under_load.spthy

# all four
for e in 00_baseline 01_busy_under_load 02_habituated_mfa 03_careless_distraction; do
  python3 $S/check.py --prove $D/$e.spthy
done

# interactive GUI — lists exactly the four ToyCeremony_* theories
tamarin-prover interactive $D/ --interface=127.0.0.1 --port=3001
```

## Adding an experiment

1. **New behaviour** → add core fragments: `core/masks/<mask>_<action>.spthy`,
   `core/stressors/<sigma>.spthy`, `core/transitions/from_<src>_<sigma>.spthy`.
2. **New Msg3 shape** → add `protocol/msg3_<variant>.spthy`.
3. Add `experiments/NN_<name>.spthy` (lemmas only).
4. Add `NN_<name>.spthy` = `#include "ceremony.base.spthy"` + the core deltas + the Msg3
   variant + the experiment.
5. Keep the entry **closed**; re-run all `L*` lemmas after touching any shared file
   (`ceremony.base`, `protocol/*`, or a reused `core/` fragment).
