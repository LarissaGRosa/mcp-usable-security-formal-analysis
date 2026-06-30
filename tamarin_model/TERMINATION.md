# Termination & scale playbook (ROADMAP #7)

Attaching the human layer to a real protocol is cheap by design — the protocol's human-action rules emit
`!Step(P, sid, action)` (+ `!StepData` where an outcome needs ground truth), include the core human layer,
and instantiate the property templates ([`usability_properties.spthy`](core/usability_properties.spthy)).
The risk at scale is **state-space explosion** in Tamarin's backward search (the machinery's §6a blow-up:
masks × stressors × phases × parties). This is the checklist that keeps proofs terminating — each lever is
already used somewhere in this model, so it doubles as a worked reference.

## The attachment recipe (minimal intrusion)

1. On each rule where a human acts, add `!Step(P, sid, action)` with `action` from the fixed taxonomy
   (`compute | compare | confirm | decide | authorize | set-policy`). Add `!StepData(P, sid, …)` only if
   the response needs ground truth (the correct value for `compute`; `genuine|tampered` for `compare`;
   `self|injected` for `confirm`).
2. Include the core human layer: `transitions/mask_state` + `transitions/answered_once`, `masks/outcome_policy`
   + the `<class>_behavior` files for the actions you use, the `stressors/*` you want, a stress-enable, and
   `lexicon_tlx` (or a population/interface profile) for the lookup detectors.
3. If an approval/verification **gates** a downstream protocol step, consume the behavior's output fact
   (`Respond` / `Checked` / `Confirmed`) in a thin per-ceremony adapter — see `fido_auth` (the device
   signature is gated on `Confirmed`).
4. Instantiate the property templates; run `check.py --prove`; feed the pairs to `tools/rfc_gen.py`.

`fido_auth` is the worked example: a signature protocol (`builtins: signing`) with the human layer attached
this way, proving a crypto property (auth requires the human's approval) **and** a human-factors property
(habituation → injected-login takeover), reusing the masks/σ₈/shutout verbatim.

## Termination levers (each used in this model)

| Lever | Why | Where |
|---|---|---|
| **One instance per human** (`Start(p)` once) | stops concurrent sessions mixing facts | `core/types.spthy` `OneInstancePerHuman` |
| **One onset per stressor per party** (`Once*`/`One*`) | a detector reads a *persistent* trigger and would re-fire forever | every `core/stressors/*` |
| **One `SetMask` per mask per party** | bounds the event set the interval reasoning in `mask_state` walks | `OneSetMaskPerMask` |
| **"Active until recovery", not latest-wins** | strict latest-mask-wins needs a "no `SetMask` between" clause whose all-traces search blows up once ≥3 stressors interleave | `mask_state.spthy` design note |
| **Bounded token harness** | a fixed number of `OpToken`/`DecToken` makes the counting detectors (σ₈/σ₉) terminate | `infer_harness.spthy` |
| **Exact-match levels (no `≥`)** | an ordinal `≥` relation over level atoms adds a transitive search; exact-match `'hi'` is flat | `AGNOSTIC_STRESSOR_INTERFACE.md` §5, `CALIBRATION.md` §2 |
| **Persistent, read-only `!Step`/`!StepData`/`!Demands`** | no consume-and-reproduce → no sources loop (the stored-`St_H` style provably loops the sources solver) | all producers/detectors |
| **One `outcome_policy` / lexicon per theory** | duplicate seed rules = duplicate-fact / sources noise | entries seed once (P2/S0/S1) |
| **Keep `Inequality`-named restrictions apart** | σ₈ and σ₉ both define `Inequality`; composing them double-defines it | σ₈ in P2/P6, σ₉ in P4/S1 |

## When P3 (the worst case) stops terminating

`P3_worstcase` is the deliberate §6a canary — all phases/masks/stressors on both parties. If a change makes
it non-terminating, that **is** the blow-up; narrow the enabled set rather than fight the prover:

- **Stress one party**, not both (drop a `stress_*` include).
- **Drop a phase bundle** the property under test doesn't need.
- **Cap the enabled stressors per party** (a profile need not host every detector).
- **Split into per-phase profiles** and prove the phase properties separately (the phase bundles are
  designed for this — closedness is phase-driven).
- Add a **`sources` lemma** if a new `!Step`/`!StepData` read introduces partial deconstructions; budget a
  re-prove of P3 after any shared-file change.

## What does NOT scale (be honest in the writeup)

- **Possibilistic, not probabilistic.** Proofs say a bad outcome is *reachable*, not *likely*. Reachability
  under realistic stressors is the RFC-useful claim; severity/likelihood ranking is out of scope.
- **Unbounded prompt/decision flooding** must be bounded (the token harness) — an unbounded count detector
  does not terminate. Model "≥ k" with a fixed small k; `log`/document the cap.
- **Big real protocols** (full TLS/OAuth state machines) will need per-phase compositional proofs; the
  `!Step` seam makes attachment cheap, but the protocol's own state space is the dominant cost.
