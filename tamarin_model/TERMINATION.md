# Termination & scale playbook (ROADMAP #7)

Attaching the human layer to a real protocol is cheap by design — the ceremony's **interface** poses
`!Prompt(P, pid, action)` (+ `!Displayed` where observables matter); the mask performs and commits
`!StepData` where a downstream rule needs the value; a profile `#define`s the human layer and
`#include`s the consolidated `core/` files. The risk at scale is **state-space explosion** in
Tamarin's backward search (the machinery's §6a blow-up: masks × stressors × phases × parties). This
is the checklist that keeps proofs terminating — each lever is already used somewhere in this model,
so it doubles as a worked reference.

## The attachment recipe (minimal intrusion)

1. On each rule where a human is **shown** a step, add `!Prompt(P, pid, action)` with `action` from
   the fixed taxonomy (`compute | compare | confirm | decide | authorize | share | set-policy`). Add
   `!Displayed(P, pid, …)` only when the mask needs the UI's *observables* (the correct value for
   `compute`; `<offered, reference>` for `compare`; `<claimed, own>` for `confirm` — never a
   pre-computed verdict; see repo `MEMORY.md` lesson 14). The mask in `core/masks.spthy` performs the
   step and commits `!StepData` where an advance/effect adapter reads it.
2. Include the human layer via the flat template: `#include core/framework.spthy` (always on) +
   `#define` the `MASK_*` classes, `SIGMA*` detectors, and one demand profile (`LEXICON_DEFAULT` /
   `POP_EXPERT` / `IF_*`) + `#include core/{demands,masks,stressors,knobs,properties}.spthy`.
   Seed `!StressEnable(P)` for each party you intend to stress.
3. If a human outcome **gates** a downstream protocol step, consume the mask's output in a thin
   advance/effect adapter — see `COMPUTE_KEYRESULT`, `MASK_COMPARE_KEYCHECKED`, and the
   `Share_*_effect` rules in `secure_email/interface.spthy`.
4. Instantiate the property templates from `core/properties.spthy`; run `check.py --prove`; feed the
   pairs to `tools/rfc_gen.py`.

The retired `fido_auth` ceremony (git 2c56573, removed 2026-07-09) was the worked example: a signature
protocol (`builtins: signing`) with the human layer attached this way, proving a crypto property (auth
requires the human's approval) **and** a human-factors property (habituation → injected-login takeover),
reusing the masks/σ₈/shutout verbatim. The recipe above is what it demonstrated.

## Termination levers (each used in this model)

| Lever | Why | Where |
|---|---|---|
| **One instance per human** (`Start(p)` once) | stops concurrent sessions mixing facts | `core/framework.spthy` `OneInstancePerHuman` |
| **One onset per stressor per party** (`Once*`/`One*`) | a detector reads a *persistent* trigger and would re-fire forever | each `#ifdef` block in `core/stressors.spthy` |
| **One `SetMask` per mask per party** | bounds the event set the interval reasoning walks | `OneSetMaskPerMask` in `core/framework.spthy` |
| **"Active until recovery", not latest-wins** | strict latest-mask-wins needs a "no `SetMask` between" clause whose all-traces search blows up once ≥3 stressors interleave | `core/framework.spthy` mask-state design note |
| **Bounded token harness** | a fixed number of `OpToken`/`DecToken` makes the counting detectors (σ₈/σ₉) terminate | `INFER_HARNESS` in `alex_blake_kdf/protocol.spthy` |
| **Band thresholds (`!AtLeast`)** | lookup detectors fire on a graded band `'lo'<'med'<'hi'`, not unbounded order search | `Seed_levels` + lookup rules in `core/framework.spthy` / `core/stressors.spthy` |
| **Persistent, read-only `!Prompt`/`!Displayed`/`!StepData`/`!Demands`** | no consume-and-reproduce → no sources loop (the stored-`St_H` style provably loops the sources solver) | interface producers + detectors + masks |
| **No vestigial persistent facts** | facts that nothing consumes multiply the state space (the old mask `!Step` commit was removed for this reason) | see `MEMORY.md` lesson 19 §5c |
| **One demand profile / lexicon seed per theory** | duplicate seed rules = duplicate-fact / sources noise | `#define LEXICON_DEFAULT` or one alternative in `core/demands.spthy` |
| **Keep `Inequality`-named restrictions apart** | σ₈ and σ₉ both define `Inequality`; composing them double-defines it | σ₈ in P2/P6, σ₉ in P4/S1 |

## When P3 / S4 (the worst case) stops terminating

`P3_worstcase` / `S4_worstcase` are the deliberate §6a canaries — all phases/masks/stressors on both
parties (S4: all 7 detectors). If a change makes either non-terminating, that **is** the blow-up;
narrow the enabled set rather than fight the prover:

- **Stress one party**, not both (drop `#define STRESS_BLAKE` or the recipient targeting).
- **Drop a phase flag** the property under test doesn't need (`#define UI_VERIFY`, …).
- **Cap the enabled stressors per party** (a profile need not `#define` every `SIGMA*`).
- **Split into per-phase profiles** and prove the phase properties separately (each `#ifdef` block is
  designed for this — closedness is flag-driven).
- Add a **`sources` lemma** if a new `!Prompt`/`!StepData` read introduces partial deconstructions;
  budget a re-prove of P3/S4 after any shared-file change.

## What does NOT scale (be honest in the writeup)

- **Possibilistic, not probabilistic.** Proofs say a bad outcome is *reachable*, not *likely*.
  Reachability under realistic stressors is the RFC-useful claim; severity/likelihood ranking is out
  of scope.
- **Unbounded prompt/decision flooding** must be bounded (the token harness) — an unbounded count
  detector does not terminate. Model "≥ k" with a fixed small k; log/document the cap.
- **Big real protocols** (full TLS/OAuth state machines) will need per-phase compositional proofs; the
  `!Prompt`/`!Displayed` seam makes attachment cheap, but the protocol's own state space is the
  dominant cost.
