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

Lemma prefixes `L0_`…`L3_` track the `00`…`03` ordinal; the merged experiment uses `LM_`, the recovery one `L5_`.
All 29 lemmas verify under Tamarin 1.12 / Maude 3.5.1, each experiment in **≤2 s**.

**Persistent current mask (across action types).** The mask is not re-derived per action: each
stressor emits `SetMask(p,m)` at onset and the UI warning emits `SetMask(p,'Attentive')`; the gates in
`core/transitions/mask_state.spthy` make every f_H respond as the current mask, which carries CALC_SK →
APPROVE_REQ until a recovery. So a user driven **Busy** on the KDF stays degraded at the approval prompt
(Busy → `auto_approve` via `busy_approve`, Careless → `timeout` via `careless_approve`), proven by
`LM_mask_persists_across_actions`. Encoded as "degrade active until recovery" (the tractable choice;
strict latest-wins blows up on the merged experiment).

**Experiment 05 adds the first way BACK to Attentive** (plan §5/§7 recovery): the Habituated mask
persists across prompts (monotone `!Stressor`) until a good-usability UI warning (`Reengage`) re-engages
the user. Modelled as derived event-ordering in `core/transitions/recovery.spthy` (no stored mask). The
state-establishing events are bounded to once per party (`OnceHabituate`, `OnceReengage`) — without that
the warning/habituation rules re-fire unboundedly and the recovery gates' interval reasoning never
terminates; the bound keeps it at ≤2 s and is semantically a no-op (the persistent `!Stressor` already
makes re-emission redundant). Modelling repeated habituate↔recover *cycles* would relax those bounds.

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
