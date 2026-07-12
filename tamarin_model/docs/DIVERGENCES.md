# Divergences from `secure_email_full_interface_plan.md`, and the shortcomings of the refactor

An honest record of **where the implementation departed from the plan, why, and what is weaker as a
result**. Revised after the NOT-MET items were closed. Nothing here is hidden in a commit message; if a
plan goal is not met, it says so.

---

## A. Divergences forced by the tool (tamarin)

### A1. No `#ifndef`; skipping a nested `#ifdef` is dangerous (but NOT always fatal)
Tamarin's preprocessor supports only `#ifdef` / `#else` / `#endif` / `#define` / `#include`.

I originally recorded (MEMORY lesson 20) that *skipping* an `#ifdef` block containing a nested `#ifdef`
always mis-nests and silently makes lemmas vacuous. **That was over-stated.** The truth is narrower and I
was bitten by it once, live: nesting `#ifdef KDF_SPOOF` inside `#ifdef KDF_MESSENGER` (which every
P-profile skips) broke all twelve P-profiles — yet `#ifdef OUTCOME_PREMATURE`, nested in the *same* block,
does not. The failure is **pattern-dependent, not universal**, and I do not have a crisp characterisation
of when it bites.
**Working rule (conservative):** put a lever's `#ifdef` at the TOP LEVEL of a file that is always included,
or inside a file that is only `#include`d in the TAKEN branch (so its inner `#ifdef`s are always processed
in an *entered* context). That is why the flow is split across `sender_screens.spthy` + `screens_pgp.spthy`
+ `screens_pw.spthy`. It is a workaround for a tool quirk, and it makes the file layout less obvious than
the plan's one-file-per-ceremony.

### A2. The plan's headline kdf lemma is **not provable as written**
The plan (step 7) specifies `K(kdf(Na,Nb)) => (K(Na) & K(Nb)) | key-leak`. This is **false in tamarin** and
is falsified in 14 steps: `K(·)` is an *action* that fires when the adversary *uses* a term; it does not
fire on the sub-terms of a term the adversary *derives* (those are `!KU` facts).
**Proved instead:** `H_sk_requires_both_leaks` — `Secret(kdf(na,nb)) & K(kdf(na,nb)) =>` **both parties**
performed a nonce-exporting mistake. Same claim ("leaking ONE nonce is insufficient"), provable, and better
for attribution — but it is stated over the ceremony's mistake vocabulary, not over adversary knowledge.

---

## B. Divergences forced by the prover budget

### B1. Density detectors of the form "any N of M prompts" explode → single marker
σ2 (`any two !Demand`) and σ9 (`any three 'decide'`) are O(M²)/O(M³) lookups in the source saturation.
Fine for the 2–3 prompts an ambient stub posed; **catastrophic** once a real screen poses 8–12 co-present
controls (even the trivially-true `H_sk_secret` timed out). Both were rewritten in core to read a SINGLE
marker (`!Copresent`, `!CopresentDecide`).
**The derivation was RETRIED and it genuinely does not fit — now measured, not assumed.** Since the spine
work (D4) bought a lot of headroom, and since σ8 has always carried a two-`!Demand` product inside budget, I
rebuilt the marker as a *derived* fact in core: one once-bounded rule producing `!Copresent` from two
distinct real `!Demand` rows (and `!CopresentDecide` from three distinct `'decide'` rows), with every
ceremony-side emission deleted. Result: **every screen profile times out (>178 s — S1, S3, K2), while the
small-N legacy profiles pass in ~11 s.** That is the O(N²)/O(N³) product again; persistent premises are
lookups, but the *product* is still paid, and a real screen posing 8–12 controls cannot afford it. Reverted.

**Fixed instead, by a soundness GUARD (not a derivation).** The marker stays asserted, but the assertion is
now *checked*: a screen that emits a density marker must, in the SAME step, have POSED the distinct controls
it claims. Two ungated lemmas in `core/properties.spthy` — `UP_copresence_is_grounded` and
`UP_decide_density_is_grounded` — verify in all 35 profiles and cost nothing (action facts only, no `K()`).
A mis-authored screen claiming density it does not have is now **caught by a lemma** instead of believed.

**Residual (honest).** Two things are still true. (a) The guard proves the claim is *grounded in posed
controls*; it does not *derive* concurrency, so the model still takes "these controls are simultaneously on
screen" from the screen's own authorship. (b) The **legacy kdf wire surfaces**
(`IF_concurrency_surface` / `IF_alertvolume_surface`, used by the P-profiles) conjure the marker from
`!StressEnable` alone and pose nothing at all — they emit no claim, so the guards are **vacuous there**.
Those profiles model an abstract surface with no interface to ground density in, which is a reason, not an
excuse. σ8/σ_ADDITIVE still count real prompt pairs directly, so the inconsistency in *mechanism* remains —
but it is no longer an inconsistency in *soundness*.

### B2. The PATHWAY is gated per profile (`PATH_PGP` / `PATH_PW`)
With both pathways compiled into every theory, each profile hauled the whole two-pathway/two-party surface
and only ONE stressor fitted in 3 min — the plan's stressor *trios* were unprovable. Gating halved the
surface and the trios came back (σ6+σ2: >3 min → 13 s).
**Shortcoming.** No *stressed* profile exercises both pathways at once; only the (stressor-free) `S0` does.
The plan's picture of one theory holding both methods, with the human choosing between them under stress,
is not realised.

### B3. Levers are opt-in because the budget is nearly full
The reply leg + the adversary-mediated Screen-C compare (`PGP_REPLY`) could not be made unconditional:
`S3_trio_mixed` already burns ~82 s and compiling them into every PGP profile pushed it over the limit.
Same story for `IF_REVEAL`, `IF_FIELD_REMINDER`, `KDF_SPOOF`. Each is exercised by a dedicated profile,
which is honest, but it means **no single profile shows the whole interface at once**.

---

## C. Plan items: current status

| Plan item | Status | Note |
|---|---|---|
| σ10 closure (`slip → !Failed → σ10 → Careless → leak`) | **MET** | `S8_sigma10_closure` (secure_email) AND `K7_sigma10_closure` (kdf) — the same loop through two different interfaces, so it is a property of the ACTION CLASS. I had wrongly recorded this as impossible: I ruled it out *before* the pathway split and never retested. |
| σ9 coverage in secure_email | **MET** | armed in `S3` (Blake's three co-present decides). |
| kdf K2 MITM (incoming-code compare) | **MET** | `K6_mitm` + `K6_agreement_unless_mistake`. The chat can be SPOOFED (adversary posts a code it knows) but never READ — so (S) stays non-vacuous, and the OOB read-back is what catches the substitution. |
| kdf K3 key-entry field | **MET** | the second `'med'` field; makes `SIGMA_ADDITIVE` real on the invented screens. |
| A13 sign·attach-key + reply completion | **MET** | `S15_reply`: `reply_completes`, and `reply_needs_attach` (a dismissed confirm is a pure USABILITY failure — the reply silently never happens, nothing leaks). |
| A10 hint field + hint leak | **MET** | `IF_hint_leak` → `LeakPw` (already on the pw boundary list). |
| A9/B2 show-password reveal (`IF_REVEAL`) | **MET** | RFC pair `S2_slipped_pw_sent` (reachable) → `S13_no_slipped_pw_sent` (unreachable), non-vacuous (`S13_completes`). |
| A5 subject reminder (`IF_FIELD_REMINDER`) | **MET** | RFC pair `S8` → `S12_no_subject_leak`. **DERIVED, not axiomatic** — see D1. |
| To-field slip → misdirection | **MET** | `S8_to_field_misaddressed`. Core now emits a `TranscribeSlipped` token (the counterpart of `TranscribeLeaked`) so the ceremony gives it meaning WITHOUT threading a second free-valued `!StepData` into the send — which is what originally opened the non-terminating source chains. |
| Blake's compare/confirm adversary-mediated | **MET** | Screen B `In(claimedOrigin)`; Screen C `In(senderKey)` (under `PGP_REPLY`). |
| T5 completion-under-onset, strong (ordered) form | **MET** | was the biggest real gap; see D6. Every stressed S/K profile now carries one `_completes_under_<σ>` per ARMED stressor (28 lemmas), pinning the onset strictly before the STRESSED party's own completion step. |
| Onset coverage per armed stressor (lesson 16) | **MET** | the four legacy P-profiles that armed a stressor no lemma witnessed (`P1`,`P2`,`P3`,`P6`) now have one; all 10 verified, so no stressor was in fact dead. |
| A11 expiration, A4 Cc/Bcc, A12 attach, A16 discard, B3/B5/B8/B9 | **exposure only** | posed as `!Demand` for density; no answer drives anything. |
| RFC lever pairs | **MET, 12/12 proven** | incl. `REQ-CONFIRM-BEFORE-SESSION`, the SAME core lever as `REQ-VERIFY-BEFORE-SEND` proved necessary in a second, independent ceremony. |

---

## D. Shortcomings introduced or exposed while closing the above

### D1. A lever must CHANGE BEHAVIOUR, not be postulated (a bug I caught and fixed)
The first implementation of the subject-reminder proved `not (Ex SubjectLeak)` in **2 steps** — because it
used a *restriction* (`SubjectLeak ⇒ not ControlDesigned`) plus an axiom forcing the design to hold. That
is assuming the conclusion: the lever's *effect* was postulated rather than derived.
Rebuilt using the model's own `!ControlDesign` idiom (the one `MASK_POLICY` already uses): core's
`Transcribe_leak` now requires `!ControlDesign('transcribe','plain')`, and the reminder seeds `'clear'`
instead, so the leak rule **cannot fire**. The same lemma now takes **103 steps** — it is derived. And it
proves things the axiom could not: the human **still slips**, **still answers carelessly**
(`LeakAverted`), and **still reaches the TLS misroute**. A reminder fixes the field, not the person.
**Lesson:** if a hardened lemma closes in ~2 steps, suspect that a restriction has excluded the very traces
the lemma is about.

### D2. A named breach can be UNREACHABLE while looking modelled
`PwEnteredAtImpostor` (Blake types the passphrase into a phishing page) was **dormant in every shipped
profile**: no `PATH_PW` profile stressed Blake, and Screen B posed only ONE `confirm`, so σ8 could never
habituate him — he stayed Attentive and the route was unsatisfiable. The rule existed, the boundary-list
disjunct existed, and nothing ever fired it. `S10`'s comment claiming the route was "live" was aspirational.
Fixed by `S14_blake_phish`. **A leak route is not modelled until some profile proves it REACHABLE** —
otherwise the (S) boundary list is padded with disjuncts that cannot be satisfied, which makes the secrecy
lemma look stronger than it is. Every named route on `H_leak_routes` now has a profile that reaches it.

### D3. "A slip is a safe-fail" was FALSE once the To field drove an outcome
Wiring A2 correctly **falsified** the existing `S8_slip_alone_is_safe`, and rightly so: a slip is not
intrinsically safe. It depends on the FIELD — a wrong subject or passphrase is a safe-fail; a wrong
ADDRESS misaddresses the message. Restated as `S8_slip_is_not_itself_a_leak` (every K(m) still traces to a
NAMED route, of which the misaddressed send is now one), and both consequences of a slip are now proved:
DIRECT (misaddress) and INDIRECT (σ10 closure → the next entry leaks).

### D4. The two fragile profiles are fixed — and the causes were both *structural*, not "hard proofs"
`K7_additive` (172 s) and `S8_transcribe` (125 s) sat near the 180 s ceiling. Both are now comfortably
inside it — **K7 172 → 109 s, S8 125 → 21 s** — with no property weakened. Three findings, each of which
is a reusable rule rather than a one-off tuning hack:

1. **A long ordered `exists-trace` chain makes the search wander.** Both σ10 closures pinned the whole
   causal chain in one witness (`AdditiveLoad < Slip < RepeatedFailure < Leak`). Every extra event is
   another thing the search may interleave. **Decomposed** into an `exists-trace` for the half that
   genuinely needs a witness (`RepeatedFailure < Leak`) plus an **all-traces theorem** for the half that is
   forced anyway (`RepeatedFailure ⇒ Ex Slip before` — σ10 fires only on `!Failed`, and only a `Slip`
   raises `!Failed`). This is **strictly stronger** than the original: the second half is now a theorem, not
   one witness trace. Closure lemma: 126 s → 8 steps.
2. **`[reuse]` order matters, and it was wrong.** A `[reuse]` lemma is visible only to lemmas declared
   *after* it. `H_leak_routes` — the expensive `K(m)` boundary list — was declared **first**, so it could
   not consume the cheap, K-free structural helpers (`H_sk_secret`, `H_encto_shape`) and re-derived their
   content inside its own search. Reordering cheap-structural-first: 831 → 503 steps, free.
3. **The default goal-ranking heuristic was simply the wrong one for the boundary list.** `H_leak_routes`
   with `heuristic=I`: **117 s → 29 s**. This is the single biggest win and it changes nothing about what
   is proved. Note it is **not** a globally good setting — the *same* flag on the kdf spine
   (`H_nonce_leak_routes` / `H_sk_requires_both_leaks`) makes K7 **time out**, and `heuristic=S` makes
   `H_leak_routes` itself time out. The heuristic must be chosen per lemma, empirically.

**Residual shortcoming.** Point 3 means the budget is now partly held up by an empirically-chosen search
heuristic, not by structure alone. It is a real dependency: a future tamarin whose ranking changes could
push these back out, and there is no lemma-level test that would explain *why*. Points 1 and 2 are
structural and survive that; point 3 should be understood as tuning, and is commented as such in the file.

### D6. The (C) half of the (C)∧(S) pair was near-VACUOUS in 20 profiles (the plan's own G5)
The worst finding of the whole audit, and it was mine. Plan step 7 specifies T5 as
`Sx_completes_under_<σ>` — **onset ∧ finish**. It permits dropping the *negated-unsafe* conjunct as a
fallback; it does **not** permit dropping the **onset**, which is the entire "under σ". I dropped the onset
everywhere except `S8` and `K7`. What twenty profiles actually shipped was:

    lemma S1_completes: exists-trace "Ex m #s #r. Send('Alex','PGP',m)@s & Read('Blake',m)@r"

**That witness is satisfied by a trace in which the stressor never fired.** In a profile whose whole point
is σ6+σ2, it asserts only "the ceremony can complete" — which the *baseline* already proves. So the pair the
plan was built to deliver (G5: "no uniform per-stressor pair (C) ∧ (S)") had a real (S) side and a hollow
(C) side, in exactly the profiles where (C) was supposed to carry weight.

**Fixed:** every stressed S/K profile now carries one `_completes_under_<σ>` per ARMED stressor (28
lemmas). The onset is pinned strictly before **the stressed party's own** completion step — Alex's onsets
before `Send`, Blake's before `Read`/`SessionUp`. (Ordering a *Blake* onset before *Alex's* send is simply
false: Blake degrades when he reads, which is after Alex sent. The naive "onset < first event" form would
have been unprovable for `S3`/`S6`/`S14`/`K6` for an uninteresting reason.)

Two of the 28 came back **falsified**, and both were worth having:
- **`S11_hardened` under σ6 is IMPOSSIBLE — and that is the correct outcome.** `IF_HARDENED` seeds the full
  lexicon, so the abstraction onset cannot fire at all; `S11_no_abstraction` already proved it. The lever
  **removes** the stressor rather than surviving it, which is *stronger* than completing under it. The
  profile deliberately has no σ6 witness now, with a comment saying why, and its σ2 witness shows it is not
  merely stressor-free.
- **`K6_mitm` was asking about the wrong human** (`Abstraction('Alex')` in a `STRESS_BLAKE` profile — Alex
  has no `!StressEnable`, so the onset was unsatisfiable). Corrected to Blake. It now proves something
  pointed: Blake abstracted, the MITM active, and **both parties still reach `SessionUp`** — i.e.
  *completion does not imply security*, which is the whole thesis of the ceremony.

**Residual shortcoming.** The unsafe-conjunct is still dropped (the plan's sanctioned fallback), so T5 says
"completes despite the onset", not "completes despite the onset *and cleanly*". Cleanliness is derived
separately from T6 rather than inside the same witness.

### D5. Still true from the first pass
- **`--auto-sources` is unusable here** (heap-exhausts), so the model relies entirely on hand-kept
  structural discipline (shallow sources, single free-valued `!StepData` joins, single-marker density).
  There is no automated safety net: an edit that deepens a source simply stops terminating, with no
  diagnostic pointing at the cause.
- **One-party stress.** Each stressed profile stresses Alex *or* Blake, never both (except `K4`). The model
  cannot see interactions between two simultaneously degraded humans.
- **Exposure-only controls prove nothing about behaviour.** They exist to make density fire; the model says
  nothing about what a user *does* with the Reply button or the badges.
- Older design notes (`mask_machinery_formalization.md`, `usability_extension_plan.md`) were **not**
  revisited and still describe the ambient-surface world.

---

## E. What the refactor delivers

- **Order violation is a first-class, proved property in two ceremonies** (`SendPremature`,
  `SessionUnconfirmed`) from ONE ceremony-blind core lever — the strongest generality claim here, and
  something the old model could not express at all.
- **The σ10 closure holds in both ceremonies** — the slip→degrade→leak loop is a property of the action
  class, not of one interface.
- **The (S) boundary list is proved once** (`H_leak_routes`) and consumed by every profile: per-profile T6
  costs ~8 steps instead of 261. Every route on it is now reachable in some profile (D2).
- **12/12 RFC requirements proof-backed**, each a T4 pair (bad outcome reachable in the baseline,
  unreachable under the lever, ceremony still completes).
- `core/` contains **no ceremony vocabulary** (grep-audited), and the new core blocks
  (`MASK_TRANSCRIBE`, `OUTCOME_PREMATURE`) are armed by **both** ceremonies.
