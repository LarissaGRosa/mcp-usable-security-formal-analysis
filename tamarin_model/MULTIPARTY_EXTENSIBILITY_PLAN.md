# Iteration plan — multi-participant masks + multi-stressor profiles

> **Note (2026-06-29):** this plan is **complete** (P0–P6 profiles + phase bundles shipped). Since it was
> written, the stressor trigger interface was migrated to be ceremony-agnostic and two detector files were
> renamed (`*_inferred` suffix dropped): `repeated_failure_inferred`→`repeated_failure`,
> `alert_volume_inferred`→`alert_volume`; the detectors now read `!Step` + `core/lexicon_tlx.spthy`. See
> [`AGNOSTIC_STRESSOR_INTERFACE.md`](AGNOSTIC_STRESSOR_INTERFACE.md). The illustrative include blocks below
> keep their original detector names for historical fidelity.

This plan adds two capabilities to the `alex_blake_kdf` model:

1. **Every participant is subject to mask change**, Blake included. A stressor
   targets a named participant.
2. **Fewer experiments, each with ≥3 stressors**, assembled from reusable
   bundles so a new experiment or a new stressor is a one-line addition.

The plan is staged. Each stage ends with `check.py --prove` on every touched
entry, and each entry stays under 5 minutes.

## 0. Starting facts (what already supports this)

- The human layer is party-generic: `core/masks/*`, `core/stressors/*`, and
  `core/transitions/mask_state.spthy` all key on a party variable (`P` / `p`).
- `Trigger_HighCognitiveLoad` reads `!Req(P,…)` for any `P`; the per-party
  bounds (`OneStressPerParty`, `OneSetMaskPerMask`, `OnceHabituate`) are already
  `p`-keyed.
- The block is the protocol layer. It hardcodes `'Alex'`, the typed init facts
  `AlexInit` / `BlakeInit`, and the linear chain `AlexWait → AlexAwaitKey →
  AlexDone`. Blake's only human step (`B_recv_Na_send_Nb` in
  `protocol/messages.spthy`) computes `kdf(Na,~Nb)` inline and stays Attentive.

Consequence: no change to `core/masks/`, `core/stressors/`, or `mask_state.spthy`
is required for point 1. The work is in `protocol/` and the entry points.

## 1. Stage A — party-generic protocol layer

**Goal:** route every human step (for both parties) through `!Req` + an f_H
mask, so the same machinery that degrades Alex can degrade Blake.

### A1. Generic participant init

Replace the two typed init facts with one persistent participant fact.

```
// protocol/init.spthy  (new)
rule Init_Party:
    [ Fr(~id) ]
  --[ Start($P), Role($P) ]->
    [ !Party($P, ~id) ]
```

Seed the two roles in the entry (or a `protocol/parties.spthy` fragment):

```
rule Seed_Alex:  [] --[ Spawn('Alex') ]-> [ Begin('Alex') ]   // → Init_Party with $P='Alex'
rule Seed_Blake: [] --[ Spawn('Blake') ]-> [ Begin('Blake') ]
```

`OneInstancePerHuman` (`core/types.spthy`) already bounds `Start(p)` per party,
so two parties stay at one instance each. Keep the party set at exactly two.

### A2. Blake's CALC routes through a request

Split `B_recv_Na_send_Nb` into a nonce-send step and a CALC request, mirroring
`msg3_request.spthy`:

```
// protocol/messages.spthy  (revised)
rule B_recv_Na_send_Nb:
    [ !Party('Blake', idB), In(Na), Fr(~Nb) ]
  --[ Gen('Blake'), Send('Blake',~Nb) ]->
    [ BlakeAwaitKey(idB, <Na,~Nb>), Out(~Nb) ]

rule B_pose_calc:
    [ BlakeAwaitKey(idB, <Na,Nb>), Fr(~rid) ]
  --[ Request('Blake', ~rid, 'CALC_SK', $c) ]->
    [ BlakeAwaitKey2(idB, ~rid), !Req('Blake', ~rid, 'CALC_SK', <Na,Nb>, $c) ]
```

`$c` (complexity) is `'Easy'` by default; an experiment that stresses Blake
seeds it `'Hard'` (or uses the inferred detector). Blake's key now comes from a
mask answering `!Req('Blake',…)` — `Calc_Attentive` when unstressed,
`Calc_Busy_slip` when σ₁ targets Blake. The masks need no change; they bind `P`.

### A3. Generic linear chain for the requesting party

The Alex-specific state facts (`AlexWait`, `AlexAwaitKey`, `AlexDone`) become
party-parametric so one rule set serves both requesters:

```
[ Wait($P, idP, Na) ] … [ AwaitKey($P, idP, rid) ] … [ Done($P, idP, sk) ]
```

`session.spthy` and the UI phases (`approval_ui`, `verify_ui`, `authorize_ui`,
`warning_ui`) read `!Session($P,…)` instead of `!Session('Alex',…)`. The prompt
sources keep their `Fr(~pid)` (self) vs `In(pid)` (injected) split.

### A4. Verification for Stage A

- Re-run **all existing entries** unchanged in behaviour: with Blake seeded
  `'Easy'` and no stressor enabled on Blake, every current `L*` lemma must still
  hold. This proves the refactor is behaviour-preserving for Alex.
- Watch termination: two requesters + the interval reasoning in
  `mask_state.spthy` is the §6a risk. The per-party `Once*` bounds should hold it;
  if an entry stops terminating, it is the documented blow-up — narrow that
  entry's enabled stressor set.

## 2. Stage B — target a stressor at a specific participant

**Goal:** make "stress Blake" / "stress Alex" / "stress both" an explicit,
one-line choice, and keep "Blake stays Attentive" reachable.

Add a per-party enable token that a stressor must consume-by-reading:

```
// protocol/stress_enable.spthy
rule Enable_Stress:
    [ !Party($P, id) ] --[ StressOn($P) ]-> [ !StressEnable($P) ]
```

Each stressor adds `!StressEnable(P)` to its left side:

```
// core/stressors/cognitive_load.spthy  (revised)
rule Trigger_HighCognitiveLoad:
    [ !Req(P, rid, 'CALC_SK', m, 'Hard'), !StressEnable(P) ]
  --[ Load(P), SetMask(P,'Busy') ]->
    [ ]
```

An experiment then seeds `!StressEnable('Alex')`, `!StressEnable('Blake')`, or
both. Without a seed for a party, no stressor fires for them and that party stays
Attentive — so the "one stressed human" convention becomes a configuration, not a
hardcoded assumption.

New lemma forms this unlocks:

```
// a slip is attributable to whichever party was enabled
lemma B_blake_can_slip:
  exists-trace "Ex k #i. Calc('Blake','Busy')@i & Key('Blake',k)@i & not(Ex a b. k=kdf(a,b))"

// disagreement when EITHER party is degraded
lemma B_disagreement_either_party:
  exists-trace
  "Ex ka kb #i #j. Key('Alex',ka)@i & Key('Blake',kb)@j & not(ka=kb)"
```

## 3. Stage C — phase bundles (extensibility)

**Goal:** stop hand-listing masks/stressors per entry. Bundle by ceremony
**phase**, because closedness is phase-driven — a mask f_H for a phase the
ceremony lacks leaves its `!Req`/`!Prompt` unproduced and fails wellformedness.

One bundle per phase pulls its protocol fragment + every mask answering it +
every stressor targeting it:

```
// bundles/calc_phase.spthy
#include "../protocol/msg3_request.spthy"
#include "../../../core/masks/attentive_calc.spthy"
#include "../../../core/masks/busy_calc.spthy"
#include "../../../core/masks/careless_calc.spthy"
#include "../../../core/stressors/cognitive_load.spthy"
#include "../../../core/stressors/time_pressure.spthy"
#include "../../../core/stressors/repeated_failure_inferred.spthy"
```

```
// bundles/approve_phase.spthy   → approval_ui + {attentive,busy,careless,habituated}_approve
//                                 + habituation + external_distraction + alert_volume_inferred
// bundles/verify_phase.spthy    → verify_ui   + {attentive,naive}_verify + abstraction
// bundles/authorize_phase.spthy → authorize_ui + {attentive,fearful}_authorize + security_anxiety
```

Shared once per entry: `core/transitions/mask_state.spthy`,
`core/transitions/answered_once.spthy`, `protocol/session.spthy`,
`protocol/stress_enable.spthy`.

**Adding a new stressor** becomes: write `core/stressors/<new>.spthy`, add its
one `#include` line to the relevant phase bundle. Every experiment using that
phase gains it with no entry edit.

**Adding a new experiment** becomes: pick phase bundles + seed which parties are
stressed + write lemmas.

## 4. Stage D — consolidate into multi-stressor profiles

**Goal:** replace the 18 single-stressor entries with a smaller set, each
exercising ≥3 stressors, plus mitigation toggles.

Proposed entries:

| Entry | Bundles | Stressed parties | Stressors (≥3) | Replaces |
|---|---|---|---|---|
| `P0_baseline` | calc (inline) | none | — | 00 |
| `P1_calc_pressure` | calc | Alex + Blake | σ₁ load, σ₃ time-pressure, σ₁₀ repeated-failure | 01, 08, 12 |
| `P2_ui_fatigue` | approve | Alex | σ₈ habituation, σ₂ distraction, σ₉ alert-volume | 02, 03, 15 |
| `P3_verify_authorize` | verify + authorize | Alex | σ₆ abstraction, anxiety, + one calc stressor | 06, 07 |
| `P4_worstcase` | all four | Alex + Blake | all stressors + recovery | 04, 05, 09 |
| `P5_pathway_b` | policy | Alex | σ₄ misleading-terminology (no mask change) | 13 |

**Mitigations stay as toggles.** A profile yields its failure variant by default
and its fix variant by adding one include:

- add `core/mitigations.spthy` → `shutout` / verify-shutout active (replaces 14, 17)
- swap `msg3_request` → `msg3_request_confirmed` → `shutdown` active (replaces 16)

Each profile carries both the failure lemmas (`exists-trace`, outcome reachable)
and, when the mitigation include is present, the fix lemma (`all-traces`, bad
consequence unreachable while the mask shift still arises).

Migrate lemmas verbatim where possible; rename prefixes to the profile (`P1_*`,
…). Keep the per-stressor causality and "no correct key under Busy" invariants —
they now quantify over `p` so they cover both parties.

## 5. Stage E — prove, measure, guard

- Run `check.py --prove` on each `P*` entry. Record per-entry wall-clock; keep
  each ≤5 min (target ≤2 s as today).
- `P4_worstcase` with both parties stressed across four phases is the §6a
  termination risk. If it does not terminate: keep both parties but cap enabled
  stressors per party, or keep all stressors but stress one party — document the
  narrowing in the entry header, as Exp 04/09 already do.
- Update `README.md` (experiment index → profile index; "Adding an experiment"
  → "pick bundles + seed stressed parties") and `IMPLEMENTATION.md` (§5 assembly,
  §7 families).

## 6. Order and risk

```
A (generic protocol) ─► B (per-party targeting) ─► C (bundles) ─► D (profiles) ─► E (prove)
   behaviour-preserving    additive                 refactor only    consolidation
   highest risk (§6a)      low risk                 low risk         medium (termination)
```

Stage A is the load-bearing change and the one that can regress every existing
lemma; gate it on a full re-prove before starting B. Stages B–D are additive or
mechanical. Stage E is the recurring guard.
