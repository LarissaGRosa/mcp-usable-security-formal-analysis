# MEMORY — modelling lessons for the Ceremony-Mask Tamarin model

> Read this before editing anything under `tamarin_model/`. These are hard-won lessons from
> building the model; most cost a wrong turn or a timeout to learn. Design rationale lives in
> `mask_machinery_formalization.md` (§6) and `usability_extension_plan.md` (§0, §6a, Appendix A);
> per-ceremony usage in `tamarin_model/ceremonies/alex_blake_kdf/README.md`.

## Project state (keep current)
- Tamarin **1.12.0** + Maude **3.5.1** at `~/.local/bin` (`export PATH="$HOME/.local/bin:$PATH"`).
- Harness: `.claude/skills/model-tamarin/check.py` — `--prove` proves, default lints (~0.2 s).
- **6 experiments, 29 lemmas, all verify ≤2 s.** Entry points: `ceremonies/alex_blake_kdf/NN_*.spthy`
  (00 baseline, 01 busy_under_load, 02 habituated_mfa, 03 careless_distraction,
  04 multi_stressor, 05 warning_recovery).
- Masks built: Attentive, Busy, Habituated, Careless. Stressors: σ1 HighCognitiveLoad,
  σ2 ExternalDistraction, σ8 Habituation. One recovery edge (Habituated→Attentive via UI warning).

## Modelling lessons (Tamarin)

1. **Derived mask, never stored.** Do NOT carry the mask as a linear fact that f_H consumes and
   reproduces — Tamarin's sources solver then loops (it can "source" the mask from the very rule
   that consumes it). Represent the mask as an **action-fact label** (`RespMask(p,m)`) and derive
   the current mask from the ordered history of `SetMask(p,m)` events. (machinery §6.2)

2. **`/*` inside a comment = parse death.** Writing a path like `core/masks/*` or `stressors/*`
   inside a `/* … */` block creates the literal `/*`, which Tamarin reads as a *nested* comment
   opener → `unexpected end of input … expecting end of comment`. **Never put `/` immediately
   followed by `*` in a comment.** (Hit this 3+ times — always scan new files:
   `grep -oE '/\*|\*/' file` should show exactly `/* */`.)

3. **Unproduced LHS fact = HARD wellformedness failure** (`check.py` exits 1), not a warning. So
   every assembled theory must be **closed**: a slice may include a fragment only if it also
   provides that fragment's premises. This forces mask f_H files to be **action-scoped**
   (`<mask>_<action>.spthy`, e.g. `busy_calc.spthy` vs `busy_approve.spthy`).

4. **`#include` works** (relative to the including file; **nested includes work**). Use a base
   spine (`ceremony.base.spthy`) + per-experiment delta entries. Interactive directory-mode lists
   only real `theory…begin…end` files; include-fragments are pulled in, not listed.

5. **Bound state-latching events to once per party.** A rule that reads only persistent facts can
   re-fire unboundedly; each firing emits a fresh event. If any gate does *interval* reasoning over
   that event ("no X between …"), the proof **never terminates**. Cap with `Once*` restrictions
   (`OneStressPerParty`, `OnceHabituate`, `OneSetMaskPerMask`, …). Semantically free — re-latching a
   state you're already in changes nothing.

6. **Two different "loops" — diagnose before fixing.** Run `tamarin-prover FILE --precompute-only`:
   - "Raw/Refined sources: N cases, **deconstructions complete**" ⇒ no open-chain/sources loop.
   - If sources are clean but a proof still hangs, the cause is (5) unbounded repetition or (7) a
     heavy gate — NOT a sources lemma. Don't reach for `[sources]` in that case.

7. **Nested-negation gates are expensive; scan for ONE fact, not ANY.** "Latest-event-wins over all
   masks" (`not Ex mm. SetMask(p,mm) between`) blows up the all-traces search once ≥3 stressors
   interleave (timed out >290 s on Experiment 04). We use **"degrade active until recovery"**:
   `not Ex r. SetMask(p,'Attentive') between` — scans for one bounded recovery fact. Cheaper, still
   forbids the spurious revert; trade-off is a new stressor *adds* an active mask rather than
   strictly replacing the old (safe over-approximation). (machinery §6.8)

8. **Persistent current mask across action types.** Emit `SetMask(p,m)` at the **stressor's onset
   (inside the trigger rule)** so its timepoint is pinned — NOT from a separate rule reading the
   persistent `!Stressor` (that fires at an arbitrary later time and a stale mask can re-assert).
   Recovery is a positive `SetMask(p,'Attentive')` event (never remove the stressor → monotone).
   The mask persists CALC_SK → APPROVE_REQ until recovery (proven: `LM_mask_persists_across_actions`).

9. **Per-experiment profiles (state-space discipline, §6a).** One ceremony + a small mask/stressor
   subset per experiment; single honest human (`OneInstancePerHuman`); monotone. The merged
   multi-stressor experiment is the deliberate worst case — keep it single-human + bounded or it
   blows up.

10. **Workflow.** Lint after every edit. To find a slow lemma:
    `check.py --prove --lemma <name> --timeout N FILE` (note: `--lemma` matches by prefix, and a
    naive grep can grab the wrong "skip" line). **Every experiment must prove in ≤5 min** (currently
    all ≤2 s) — if one drifts past that, it's lesson (5) or (7), not a reason to raise the timeout.

11. **Don't pattern-match into a function term on a rule LHS.** A premise like `!Op(P,rid,kdf(x,y))`
    trips Tamarin's **message-derivation check** ("variables x,y not derivable / unintended pattern
    matching") — `check.py` reports FAIL even though every lemma verifies. To *infer a stressor from
    the operation*, key the detector on an **objective operation TAG** (a public constant, e.g.
    `!Op(P,rid,'kdf',m)`) and carry the result term `m` as an opaque variable. Run
    `--precompute-only` first to clear sources/open-chains; the derivation check shows up under
    `--prove`/lint, so check both. (This is how Experiment 10 infers σ1 with no `Hard` flag.)

12. **Inferring stressors from the ceremony (the analyzer direction, Exp 10–12).** Record the
    *objective* operation on a persistent fact `!Op(P,rid,optag,result)` and let a `core/` detector
    key on the **optag** (`'kdf'`→load, `'verify'`→abstraction) — the HCI judgment lives in the
    detector, not in a designer flag. For **trace-inference** (repetition / prior failure), read a
    persistent marker (`!Did`, `!Failed`) and **bound the operation count with linear tokens**
    (`protocol/op_tokens.spthy` seeds N `OpToken`s) so counting stays finite. The op f_H must
    produce a *state* fact to advance (e.g. `OpResult`/`VerifyDone`) — emitting the finish token as
    an *action* fact is an unproduced-LHS hard failure (caught at lint in Exp 11). Bound every
    inferred onset once/party.

13. **Outcome semantics proven so far** — three failure modes, keep them distinct:
    unsafe-success (Busy `slip` wrong key; Habituated/Busy `auto_approve`) vs safe-fail
    (Careless `timeout` / stall). Auto-approve requires a degraded mask, not specifically habituation
    (a persisted Busy user also auto-approves).
