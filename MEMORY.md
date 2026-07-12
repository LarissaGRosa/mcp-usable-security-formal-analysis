# MEMORY — modelling lessons for the Ceremony-Mask Tamarin model

> Read this before editing anything under `tamarin_model/`. These are hard-won lessons from
> building the model; most cost a wrong turn or a timeout to learn. Design rationale lives in
> `mask_machinery_formalization.md` (§6) and `usability_extension_plan.md` (§0, §6a, Appendix A);
> per-ceremony usage in `tamarin_model/ceremonies/alex_blake_kdf/README.md`.

## Project state (keep current)
- Tamarin **1.12.0** + Maude **3.5.1** at `~/.local/bin` (`export PATH="$HOME/.local/bin:$PATH"`).
- Harness: `.claude/skills/model-tamarin/check.py` — `--prove` proves, default lints (~0.2 s).
- **Second ceremony C1 `ceremonies/secure_email/`** (profile S0, 9 lemmas, ~2 s): models
  `secure-email-generic-guide.html` — sender (Alex) + recipient (Blake) in one theory, with the
  PGP pathway (keyed recipient, `aenc(m, pk(skB))`) and the password pathway (keyless recipient,
  `senc(m, pw)`) BOTH reachable, both parties mask-capable. Reuses `core/` verbatim; adds
  `protocol/crypto.spthy` (asym+sym builtins, kept out of `core/types.spthy`), share masks
  `core/masks/{attentive,careless,busy}_share.spthy`, and `core/stressors/time_pressure_share.spthy`.
  Out-of-band channel = private `Oob(...)` fact the DY adversary can't read; "leak" = put the
  secret on `Out`. The reused VERIFY_KEY machinery (`*_verify` + σ6 Abstraction + `Tampered`) IS the
  PGP key-substitution model. Headline lemmas: `S0_attentive_keeps_secret` (no degrade ⇒ no leak) +
  `S0_message_secrecy_attribution` (adversary access ⇒ `Mistake` | `LeakPw` | `MisdeliveredPw`).
  Re-confirmed lesson 2: `/*` in a comment (`core/masks/*_share`) killed the parser.
- **Compare-class observables refactor (2026-07-01, lesson 14):** `!StepData` for a `compare` step
  now carries the OBSERVABLES `<offered, reference>` (displayed artifact vs trusted reference),
  never a `'genuine'`/`'tampered'` oracle tag — `Compare_attentive` PERFORMS the comparison by
  matching `<k,k>`; `Tampered(vid)` stays as the producer's provenance action for lemmas only.
  Producers updated: verify_ui, infer_harness (tampered fp now genuinely from `In`), pgp_pathway,
  compose_ui. Also: `set_passphrase`/`A_compose_pw` split into `'compute'` + `'share'` !Steps; all
  composer/read steps now emit !Step (`send`/`attach_public_key`→'confirm', `set_hint`/`B_read_pw`
  →'transcribe'); σ1 added to S0's pw bundle; S0+S1 carry stressor-ONSET exists-trace coverage
  lemmas (a never-firing detector = FAIL). Sweep P0–P9+S0+S1 green.
- **Secure_email lemma restructure (2026-07-02):** three sections per experiment file — (A) happy
  paths, (B) SECURITY PROPERTIES under masks/stressors (all-traces; new:
  `S0_pgp_leak_requires_degraded_verify`, `S0_pw_secrecy_rests_on_share_only`,
  `S0_misdelivery_locks_out_recipient`), (C) FAILURE CHAINS (exists-trace) each naming the full
  interface-step → stressor → mask → outcome → K(m) cascade in ONE formula. The chains subsume the
  per-stressor onset canaries (kept per-ceremony coverage: σ3+σ2 chains in S0, σ1+σ9+σ3-recipient in
  S1, σ8 in S2 — σ1/σ3 can't both fire for one party, OneSetMaskPerMask on 'Busy'). Now S0 13 (+2
  UP), S1 9, S2 6 — 30 checks, all ≤4 s.
- **Demo ceremonies RETIRED (2026-07-09):** `ceremonies/fido_auth/` (ROADMAP #7 attach-to-real-protocol
  worked example, git 2c56573) and `ceremonies/phishing/` (ROADMAP #5 belief-state worked example, git
  045d2e0) were DELETED per user decision — the repo now maintains exactly two ceremonies
  (alex_blake_kdf P0–P9, secure_email S0–S2 = 13 theories). Their contributions that remain:
  `confirm_behavior`'s `Confirmed` output+adapter pattern, `TERMINATION.md` (recipe from fido),
  the belief-state design (ROADMAP #5 notes). rfc_requirements.json dropped
  REQ-PUSH-MFA-NUMBER-MATCH + REQ-VERIFIED-IDENTITY (RFC_GUIDANCE now 6/6 proven); ROADMAP/INCIDENTS/
  TERMINATION/AUTHORING_GUIDE annotated. NB: rfc_gen.py caught that the lemma restructure had renamed
  `S0_leak_pw_inband_reachable` → manifest re-pointed to `S0_distraction_careless_silent_compromise`.
- **C1 LAYERED v2 (2026-07-09, REPLACED all old S-profiles):**
  five strict layers (protocol/ ↔ interface/ ↔ stressors ↔ user), one directory per layer.
  Highlights: PK sub-ceremony modeled (keygen→publish: key on the PUBLIC channel, fingerprint on
  OOB); tampering = DY's choice (ONE `P_fetch: In(k)` rule — no genuine/tampered producer branch,
  no Tampered action; "tampered" derived via H_encto_shape); phishing EMERGES (open
  `<'pwreq',to,replyTo>` mail channel + first-class malicious participant Eve with `!Corrupt` →
  her OOB inbox leaks to DY; share class got triple observables `<recip, correspondent, pw>` —
  Attentive matches recip=correspondent and DEFEATS the phish, proven `S2_attentive_defeats_phish`);
  v2 detectors: σ3 = `!UnderDeadline(pid)` interface CONTEXT (time_pressure_deadline.spthy,
  situational per Maule & Svenson), σ2 = k=2 prompt CONCURRENCY (distraction_concurrent.spthy,
  Wickens MRT); new opt-in row `outcome_careless_skipcheck` (Careless+compare→credulous, Whitten
  & Tygar). Profiles: S0_baseline (9s, `S0_secrecy_absolute`), trios S1_pgp{σ6,σ8,σ2} 130s /
  S2_pw{σ1,σ3,σ9} 50s (incl. emergent-phish chain) / S3_mixed{σ6,σ3,anxiety} 13s, S4_worstcase
  (all 7, 174s) — every experiment ≤5 min. New tricks recorded in lesson 15: per-lemma
  `[heuristic=C]` attribute (fixed H_sk_secret 90s→8s) and DON'T prove both attribution AND
  attentive-keeps-secret (exact contrapositives — one proof, ~100s saved per profile).
- **C1 profile S3 `S3_mock_interface.spthy` (2026-07-09, 17 checks ~2.5 min):** the LAYERED
  mock-interface profile matching `secure-email-mock.html`. Three strict layers, color-coded via
  the `rule Name [color=#hex]:` attribute (works in Tamarin 1.12; whole core+secure_email now
  colored): #1f6fd0 protocol (`mock_protocol.spthy`) ↔ #f2994a interface (`mock_iface.spthy`, one
  rule per mock control; poses !Step up, PReq_* down) ↔ #27ae60 masks / #eb5757 stressors /
  #9b51e0 seeds. ALL 6 masks + 7 detectors (σ8+σ9 coexist — habituation's restriction renamed
  `InequalityHabituation`); send = 'authorize' (Fearful freezes; opt-in
  `outcome_degraded_click.spthy` lets Busy/Habituated/Naive/Careless still click); compare checks
  fetched key against the OOB-delivered fingerprint (`OobFp` from publish); `Authorize_grant` now
  outputs `Granted(P,aid)` (gates the send). One exists-trace chain per stressor + secrecy pair
  via 3 [reuse] helpers. See lessons 15-16.
- **C1 profile S2 `S2_habituation.spthy` (2026-07-02, 7 lemmas ~2 s):** σ8 finally triggerable in
  secure_email. `protocol/trustkey_ui.spthy` = Proton Trust-key BUTTON + CONFIRM MODAL as two
  `'confirm'` steps (the σ8 k=2 density count); paired with the OPT-IN outcome row
  `core/masks/outcome_habituated_clickthrough.spthy` (`Habituated+compare→credulous` — generalized
  warning habituation, Anderson & Vance CHI 2015). Opt-in, NOT global: P2/P3 prove
  `mistake_requires_abstraction` under the default calibration; a profile chooses the stronger
  hypothesis by one include (same pattern as `interface_hardened_verify` for !Demands rows).
  Headlines: `S2_habituated_clickthrough_leaks` (double modal → Habituate → click-through accepts
  substituted key → K(m)) + `S2_mistake_requires_habituation` (no other cause in this profile).
- **C1 profile S1 `S1_interface.spthy`** (7 lemmas, ~3 s): the sending INTERFACE generates the
  stressors (analyzer/inferred direction, lesson 12). `protocol/compose_ui.spthy` poses each
  composer step's OBJECTIVE op + the S0 trigger fact: choose_method→`!Decision`×3→σ9 (Careless),
  confirm_key→`!Op('verify')`→σ6 (Naive), set_passphrase→`!Op('kdf')`→σ1 (Busy), send→`!Req SHARE_PW`→σ3.
  Reuses core inferred detectors + S0 masks verbatim. S0's send/decrypt OUTCOMES were extracted to
  `protocol/deliver.spthy` (shared by S0+S1). Headline `S1_degrade_from_interface_step`: every
  `SetMask(p,m≠Attentive)` is preceded by a `UIStep(p,_)` — required labelling the recipient
  phishing prompt `UIStep('Blake','phish_confirm')` to cover Blake's recipient-side σ3.
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

14. **Verdicts live in the response layer; ceremonies emit observables.** A producer rule must not
    pre-compute a security judgment as a constant the mask reads (`!StepData(...,'genuine')` was the
    response-layer twin of the `'Hard'` designer flag the stressor migration removed — worst case
    was P4's "tampered" fingerprint: a FRESH value whose only tamperedness was the label). Give the
    mask the observables (`<offered, reference>`) and let the Attentive rule PERFORM the check by
    matching `<k, k>` — matching a pair of equal variables on a fact LHS is safe (pairs are
    transparent constructors; no lesson-11 derivation-check trip; the whole sweep stayed green first
    try). Ground-truth actions (`Tampered`) stay on the producer as LEMMA vocabulary only. Bonus
    honesty: an adversary re-offering the genuine artifact is now correctly *accepted* by Attentive
    instead of stalling. **Confirm class migrated too (2026-07-02):** `!StepData(P,pid,<claimed,own>)`
    — the prompt's claimed intent vs the user's own pending intent (fresh `~own` when they initiated
    nothing); `Confirm_attentive_verify` matches `<k,k>`; `Injected` stays producer provenance.
    Producers: approval_ui, approval_shutout_ui, fido_auth/protocol. All green first pass.
    **set-policy migrated too (2026-07-02):** the `'clear'/'misleading'` !StepData tag is gone —
    design quality is an INTERFACE-level `!ControlDesign('set-policy', q)` row seeded by
    `core/interface_{clear,misleading}_policy.spthy` (same mechanism as !Demands rows), read by
    policy_behavior; producers (policy_ui — now off `!Party`, one rule; expiry_ui — one rule) emit
    a bare `!Step`. P5/S0/S1 include BOTH seeds (per-trace commitment via answered_once); P7
    includes ONLY clear + proves `P7_no_unsafe_policy` (the Pathway-B RFC pair with
    `P5_misleading_attentive_mistake`). NO !StepData anywhere carries a verdict/quality tag now —
    payloads are values or observable pairs only.

15. **Deep layered pipelines need [reuse] helpers + exposure/gate discipline (S3).** A protocol↔
    interface↔human layering multiplies all-traces search: every human-GATED crossing adds a
    RespMask interval gate, and with 7 once-bounded stressors the K(m) lemmas explode (S3's
    attentive/attribution hung >8 min; heuristics C/I did not help). Three fixes, in order:
    (a) gate ONLY the crossings that drive outcomes (compare/share/authorize); every other button
    poses an EXPOSURE-ONLY !Step — density detectors count POSED steps, so σ8/σ9/σ2 still fire;
    (b) do NOT include behavior files whose answers drive nothing (confirm/decide in S3) — each
    optional answer is pure branching; (c) prove K-facts once as [reuse] helpers the big lemmas
    consume: `PwCreated & K(pw) ⇒ leak-outcomes` (6 steps), `OwnSkGen & K(sk) ⇒ F`, and a
    STRUCTURAL no-K shape lemma `EncTo(m,k) ⇒ k=pk(own-sk) | Mistake` — after which the 432-step
    secrecy lemmas verify. Keep exists-trace chains K-free on the DEEP pathway (state the chain
    to Mistake+Send; the attribution lemma carries the K story). Also: `rule Name [color=#hex]:`
    renders layer colors in the interactive graphs — protocol #1f6fd0, interface #f2994a, masks
    #27ae60, stressors #eb5757, seeds #9b51e0. Two more levers (v2): a PER-LEMMA
    `lemma X [reuse, heuristic=C]:` attribute parses in 1.12 and can rescue one wandering lemma
    without changing the global heuristic (H_sk_secret: timeout→8s); and never prove BOTH
    `attribution` and `attentive_keeps_secret` — they are exact contrapositives, one proof
    suffices (~100s saved per profile).

16. **A detector that never fires is invisible unless a lemma demands it.** Lookup detectors fail
    silently in three ways: the ceremony never emits the action (`UIStep` with no `!Step`), the
    lexicon has no row for the action, or the profile never includes the detector (σ1 was absent
    from S0 while its lexicon row sat unused). Pair every included stressor with a one-line
    `exists-trace "Ex #i. <Onset>(p)@i"` coverage lemma — proof cost is ~5 steps and it turns all
    three drift modes into a visible FAIL.

17. **V3 layered template + graded dose-response (both ceremonies).** Every ceremony is now
    `protocol/` (🔵 crypto+wire+finish; a `finish_confirmed.spthy` variant adds the key-confirmation
    shutdown) → `interface/` (🟠 one rule per control, emits `!Step`+`!StepData`+context — SUPERSEDED by
    lesson 19: the interface now poses `!Prompt`+`!Displayed` and the mask commits `!StepData`) →
    stressor layer (🔴) → `masks/` (🟢) → `bundles/human_common.spthy`. The stressor layer reads the
    INTERFACE's prompt (lesson 19: `!Prompt`), never the protocol. Triggering is a BAND, not exact-`'hi'`: a lookup
    detector matches `!Demands(action,dim,lvl) & !AtLeast(lvl, thr)`. **Put the `!AtLeast` level
    order (`'lo'<'med'<'hi'`) in `core/types.spthy`, NOT in `lexicon_tlx.spthy`** — profiles swap the
    lexicon for an `interface_*`/`population_*` demand profile (P7/P9), and the order must survive the
    swap; types is included exactly once by every profile. A swap-profile composes the human layer
    MANUALLY (mask_state+answered_once+outcome_policy+stress_alex+the demand seed), NOT via
    `human_common` (which bundles the lexicon → double-seed). Realism beyond single-step lookups:
    `additive_load` (two `'med'` steps → Busy, Sweller's additive load, density-style so no
    arithmetic; P10), inverted-U (`'med'` arousal facilitates, `'hi'` freezes; P11), population =
    threshold-shift (expert `'lo'` < `'hi'` ⇒ σ1 can't fire; P9). To show a stressor doesn't fire,
    an `all-traces "not (Ex … Onset)"` lemma is the proof (P9_no_load, P11_no_anxiety_at_moderate).
    Migration kept the tree green by building layered files with parallel names, then deleting the
    dead old spine (`ceremony.base`, `msg3_*`, `blake_calc*`, phase bundles, v1 `external_distraction`
    /`time_pressure`) only after every profile was re-ported. Watch the lesson-3 comment trap: a
    `*/` inside a `/* */` block (e.g. `interface_*/population_*`) closes it early and tamarin then
    SILENTLY DROPS the file (facts-unseeded WF failure downstream) — write `interface_* / population_*`.

18. **Flat one-file-per-layer with `#ifdef` selection (V3.1, 2026-07-10).** The ~105 tiny fragment
    files were consolidated to ONE file per model layer: `core/` → 6 (`framework`/`masks`/`stressors`/
    `demands`/`knobs`/`properties`), each ceremony → `base`+`protocol`+`interface`(+`lemmas`) + one
    self-contained file per profile. **Selective *inclusion* was load-bearing** — a profile used to arm
    a rule by including its file (in secure_email `!StressEnable` is always on, so "which σ fire" ==
    "which stressor files were included"; likewise the opt-in outcome rows and the mask behaviours the
    ceremony deliberately omits). So a blanket merge would arm everything and break `S0_secrecy_absolute`.
    Fix: merge to one file but wrap each selectable rule-block in `#ifdef FLAG … #endif`; a profile
    `#define`s exactly what it arms BEFORE `#include "base.spthy"`. Tamarin 1.12.0's preprocessor makes
    the result byte-identical to the old selective-include theory (defined flag ⇒ rule present; undefined
    ⇒ absent), so proofs/timings are unchanged. Keep include order stable (framework → protocol →
    interface → demands → masks → stressors → knobs → properties) to avoid "fact used before defined".
    To review a profile now, read its `#define` list — that IS the story.

19. **Prompt/perform seam — the interface prompts, the user performs (RELAYER, 2026-07-10).** The old
    seam had the INTERFACE emit `!Step`+`!StepData` — i.e. the UI *declared the human's objective step*,
    conflating two agents. The re-layer splits them: the interface only POSES `!Prompt(P,pid,action)` +
    DISPLAYS `!Displayed(P,pid,shown)`; the stressor detectors read `!Prompt` (fatigue is from being
    *shown* prompts, not from what the user commits; σ₁₀ alone still reads the human `!Failed`); the
    mask (`core/masks.spthy`) reads `!Prompt`+`!Displayed`, PERFORMS the step, and commits
    `!StepData(P,pid,committed)` — the mask-dependent value the human stands behind (Attentive commits
    the reference-checked key at `compare`, the correspondent at `share`; a degraded mask commits the
    displayed/attacker value). The interface's *advance* rules + the share→channel effect adapters
    consume that committed `!StepData`. **The one trap:** a key-confirmation shutdown must compare the
    human's produced key against the interface's `!Displayed` correct value (`kdf(N_A,N_B)`), NOT the
    human's own committed `!StepData` — reading the commit makes `KeyEq(sk,sk)` trivially true and the
    shutdown can never catch a slip (kdf `P_confirm_ok`/`P_confirm_abort`). Build order that stays
    green: (1) core read-rename only — nothing proves yet; (2) rewire one ceremony's interface, prove;
    (3) the other; (4) sweep + docs. **State-explosion note (§5c):** the mask's committed `!Step` fact
    turned out vestigial (stressors read `!Prompt`, adapters read `!StepData`/outcomes, lemmas read
    action labels like `Verify`/`Slip`) — dropping it took S4 solo 340s → 204s with no proof change.
    Keep only the committed `!StepData` where a consumer actually reads it.

20. **Tamarin's preprocessor: no `#ifndef`, and skipping a nested `#ifdef` is DANGEROUS (but not always fatal) (RELAYER, 2026-07-11; CORRECTED 2026-07-12).** It supports only
    `#ifdef` / `#else` / `#endif` / `#define` / `#include` — there is **no `#ifndef`**. And when it skips a
    false `#ifdef`, it does **not** track nested `#ifdef`s: it matches the FIRST `#endif` and silently
    mis-nests everything after. The theory still loads, well-formedness still passes, and every lemma goes
    quietly **vacuous**. Symptom: a trivially-reachable `exists-trace` is "falsified — no trace found" in 2
    steps. **CORRECTION:** I first wrote that this ALWAYS happens. It does not — it is *pattern-dependent*.
    Nesting `#ifdef KDF_SPOOF` inside `#ifdef KDF_MESSENGER` (skipped by every P-profile) broke all twelve
    of them, yet `#ifdef OUTCOME_PREMATURE` nested in the SAME block does not. I have no crisp
    characterisation of when it bites. **Conservative rule:** put a lever's `#ifdef` at the TOP LEVEL of an
    always-included file, or inside a file that is only `#include`d in the TAKEN branch (its inner `#ifdef`s
    are then always processed in an ENTERED context). This is why the secure_email flow is
    `sender_screens.spthy` + `screens_pgp.spthy` + `screens_pw.spthy`.

21. **Density detectors of the form "any N of M prompts" explode; use a single marker.** σ2 (`any two
    !Demand`) and σ9 (`any three 'decide'`) are O(M²)/O(M³) lookups in the SOURCE SATURATION. Harmless with
    the 2–3 prompts an ambient stub poses; **catastrophic** once a real screen poses 8–12 co-present
    controls — even the trivially-true `H_sk_secret` timed out. Rewrote σ2/σ9 in core to read ONE marker
    (`!Copresent` / `!CopresentDecide`) emitted by a screen that shows enough controls. Cost: the detector
    no longer *derives* concurrency, the ceremony *asserts* it (see docs/DIVERGENCES.md B1).

22. **Density COUNTS `!Demand`; the mask ANSWERS `Prompt` — so exposure-only controls emit `!Demand` with
    NO `Prompt`.** That makes them free: counted by the detectors, never performed, zero branching. Posing a
    `Prompt` for a control that drives no outcome is pure branching (lesson 15b) and with MASK_DECIDE +
    MASK_CONFIRM armed the exposure controls ALONE timed the proof out.

23. **Gate the PATHWAY per profile.** With both the PGP and password pathways compiled into every theory,
    each profile hauled the whole two-pathway/two-party surface and only ONE stressor fitted in budget —
    the stressor TRIOS were unprovable. Gating (`PATH_PGP`/`PATH_PW`) halves the surface: σ6+σ2 went from
    >3 min to **13 s**. Also: **Busy is the expensive mask** (its slips mint fresh terms); `SIGMA_ADDITIVE`
    is the cheap route to it (93 s under σ1 → 5 s). A story needing Busy AND Careless must be SPLIT by mask.

24. **`K(f(a,b))` does NOT imply `K(a) & K(b)` in a lemma.** `K(·)` is an ACTION that fires when the
    adversary *uses* a term; it does not fire on the sub-terms of a term the adversary *derives* (those are
    `!KU` facts). The plan's `H_sk_requires_both_nonces` is falsifiable as written. State the equivalent
    over the ceremony's MISTAKE vocabulary instead ("both parties exported a nonce") — same claim, provable,
    and better for attribution.

25. **The prover budget is 3 minutes per theorem, and it is a MODELLING gate, not a timeout knob.** Run
    capped — the box has no swap, so a runaway proof OOM-freezes it:
    `MAUDE_LIB=/usr/share/maude check.py --prove --timeout 178 FILE -- +RTS -M6G -RTS`
    (without `MAUDE_LIB` tamarin cannot find `prelude.maude` and every profile FAILs spuriously).

26. **A hardened lemma that closes in ~2 steps is a RED FLAG — you have probably assumed the conclusion.**
    A design lever must CHANGE WHAT THE DEGRADED HUMAN DOES, not be postulated to have worked. The first
    subject-reminder implementation proved `not (Ex SubjectLeak)` in 2 steps via a *restriction*
    (`SubjectLeak ⇒ not ControlDesigned`) plus an axiom forcing the design — i.e. it excluded the very
    traces the lemma was about. Rebuilt with the model's own `!ControlDesign` idiom (the one `MASK_POLICY`
    already uses): core's `Transcribe_leak` requires `!ControlDesign('transcribe','plain')`, the lever seeds
    `'clear'` instead, so the leak rule CANNOT FIRE. Same lemma: **103 steps** — derived. And it then proves
    what the axiom could not: the human still slips, still answers carelessly, and still reaches the other
    careless routes. **A reminder fixes the field, not the person.**

27. **A leak route is NOT modelled until a profile proves it REACHABLE (exists-trace).** `PwEnteredAtImpostor`
    sat on the `H_leak_routes` boundary list, had a rule, had a disjunct — and was UNSATISFIABLE in every
    shipped profile (no PATH_PW profile stressed Blake; Screen B posed one confirm so σ8 could not habituate
    him). A boundary list padded with unsatisfiable disjuncts makes the (S) lemma look STRONGER than it is.
    Pair every named route with an exists-trace in some profile.

28. **Give the ceremony a TOKEN, not a second `!StepData` join.** Core's `transcribe` emits
    `TranscribeLeaked` (Careless) and `TranscribeSlipped` (Busy); the ceremony consumes the token and decides
    what it MEANS (a mistyped recipient misaddresses; a mistyped passphrase just fails). Re-joining the
    committed `!StepData` in the send effect — a SECOND free-valued lookup — is exactly what opened the
    source chains that never closed. One free-valued `!StepData` per effect rule, always.
