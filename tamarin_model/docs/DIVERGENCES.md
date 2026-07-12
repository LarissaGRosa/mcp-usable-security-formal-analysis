# Divergences from `secure_email_full_interface_plan.md`, and the shortcomings of the refactor

An honest record of **where the implementation departed from the plan, why, and what is weaker as a
result**. Written at the end of step 10, reviewing the whole build. Nothing here is hidden in a commit
message; if a plan goal was not met, it is listed as NOT MET.

---

## A. Divergences forced by the tool (tamarin / the prover)

### A1. `#ifndef` does not exist; nested `#ifdef` cannot be SKIPPED
**Plan assumed** ordinary C-preprocessor semantics for gating the legacy rules.
**Reality.** Tamarin's preprocessor supports only `#ifdef` / `#else` / `#endif` / `#define` / `#include`.
Worse, when an `#ifdef` block is *skipped*, the skipper does **not** track nested `#ifdef`s — it matches
the first `#endif`, silently mis-nesting everything after it. This cost hours: the theory loaded, all
well-formedness checks passed, and every lemma was quietly **vacuous** because the rules had been
mis-included.
**Consequence for the design.** Any mutually-exclusive block that itself contains inner `#ifdef`s must be
a **separate file**, conditionally `#include`d — a skipped branch then contains only an `#include` line,
with no nested directive to trip over. This is why the flow is split across `sender_screens.spthy` +
`screens_pgp.spthy` + `screens_pw.spthy` rather than gated inline. It is a workaround for a tool bug, not
a modelling choice, and it makes the file layout less obvious than the plan's single-file-per-ceremony.

### A2. The plan's headline kdf lemma is **not provable as written**
**Plan (step 7)** specifies `H_sk_requires_both_nonces [reuse]`:
`K(kdf(Na,Nb)) => (K(Na) & K(Nb)) | key-transcribe-leak`.
**Reality.** This is **false in tamarin** and is falsified in 14 steps. `K(·)` is an *action fact* that
fires when the adversary *uses* a term; it does **not** fire on the sub-terms of a term the adversary
*derives*. The adversary holds `!KU(Na)` and `!KU(Nb)` without ever emitting `K(Na)` / `K(Nb)`.
**What was proved instead.** `H_sk_requires_both_leaks`: `Secret(kdf(na,nb)) & K(kdf(na,nb)) =>` **both
parties** performed a nonce-exporting mistake. This carries the same claim ("leaking ONE nonce is
insufficient") and is strictly more useful for attribution, but it is **not** the literal statement in the
plan, and it is stated over the ceremony's mistake vocabulary rather than over adversary knowledge.

---

## B. Divergences forced by the prover budget (the real cost of the full interface)

The plan assumed the full screens could carry the same profile shapes as the old ambient stubs. They
cannot. Three findings, each of which *changed the design*:

### B1. Density detectors of the form "any N of M prompts" explode
σ2 (`any two !Demand`) and σ9 (`any three 'decide' !Demand`) are O(M²) / O(M³) lookups in the source
saturation. Fine when a ceremony poses 2–3 prompts (the old stubs); **catastrophic** once a real screen
poses 8–12 co-present controls — even a trivially-true lemma (`H_sk_secret`) timed out.
**Divergence.** σ2 and σ9 were **rewritten in core** to read a *single marker* (`!Copresent`,
`!CopresentDecide`) emitted by a screen/surface that shows enough controls.
**Shortcoming (real).** The detector no longer *derives* concurrency from the posed prompts — the
**ceremony now asserts it**. A screen that poses 4 controls emits the marker because its author says so.
That is weaker: a mis-authored screen could claim concurrency it does not have, and the model would
believe it. The old form was self-evidencing; the new one is a declaration. (σ8 and σ_ADDITIVE still read
real prompt pairs — their M is small — so the model is *inconsistent* on this point.)

### B2. The whole matrix would not fit until the **pathway** was gated per profile
With both PGP and PW compiled into every theory, each profile hauled the entire two-pathway/two-party
surface and **only one stressor fitted in 3 minutes**. The plan's stressor *trios* (S1–S4) were
unprovable. Gating the pathway (`PATH_PGP` / `PATH_PW`) halved the surface and the trios came back
(σ6+σ2: >3 min → 13 s).
**Shortcoming.** A profile can no longer exercise **both pathways at once** except in the (stressor-free)
baseline. The plan's picture of one theory holding both methods with the human choosing between them is
now only true for `S0`. Every stressed profile sees a *one-pathway* world.

### B3. Busy + Careless together still do not fit; stories were SPLIT by mask
Even with the pathway split, arming a Busy-producing stressor **and** a Careless-producing one overruns
the budget (Busy is expensive: its slips mint fresh `Fr(~wrong)` terms).
**Divergence.** The plan's `S8_transcribe` ("pw-slip → !Failed → σ10 → Careless → subject leak") is a
*single* profile telling one causal story. It was split into **S8** (Careless → leak) and **S9** (Busy →
slip), and likewise the share story into **S2** (misdeliver) and **S10** (in-band leak).
**Shortcoming (the biggest one).** **The σ10 closure is NOT MODELLED.** The plan's chain
`slip → !Failed → σ10 RepeatedFailure → Careless → leak` requires Busy *and* Careless in one trace, which
is exactly what does not fit. So the model proves the two halves separately and **never proves the loop
that connects them** — the claim that repeated failure *drives* the subsequent careless leak is asserted
in prose and not in tamarin. `SIGMA10_REPEATFAIL` is consequently armed by **no secure_email profile**.

---

## C. Plan items NOT MET (or met only partially)

| Plan item | Status | Note |
|---|---|---|
| σ10 chain (`slip → !Failed → σ10 → Careless → leak`) | **NOT MET** | needs Busy+Careless in one trace (B3). σ10 unused in secure_email. |
| σ9 coverage in secure_email | **NOT MET** | Blake's Screen C emits `!CopresentDecide`, but no S-profile arms σ9 (it was in the plan's S2; S2 became a Busy-only pair). σ9 is exercised only in kdf (P4). |
| K2 "MITM" profile (credulous incoming-nonce compare) | **NOT MET** | The K2 *screen* (`IF_screen_k2`, the received-vs-readback compare) was never built. `K2_leak` is a *different* story (in-band leak). The messenger has **no MITM route**: nonces travel a private chat with no `In()`-mediated substitution. |
| K3 additive-load screen (key-entry transcribe) | **NOT MET** | The K3 screen poses `compute` only; the second `'med'` key-entry field was never added, so the kdf additive-load surface is the *old* `IF_NONCE_ACK` stub, not the invented one. |
| A13 sign·attach-key `confirm` + the reply-completion leg | **NOT MET** | Cut for tractability. `Sx_reply_completes` (the reciprocity property the guide calls out) is **not proved**. |
| A10 hint field + hint-leak (pw in the hint) | **NOT MET** | Cut for tractability. |
| A9/B2 show-password reveal lever (`IF_REVEAL`) | **NOT MET** | Never built; the corresponding RFC pair is absent. |
| A5 subject-reminder lever (`!ControlDesign`) | **NOT MET** | The subject *leak* is modelled; the *hardening* lever that blocks it is not, so there is no RFC pair for it. |
| A11 expiration, A4 Cc/Bcc, A12 attach, A16 discard | partial | present only as exposure `!Demand` or not at all. |
| To-field slip → misdirection | **changed** | The To transcribe is posed and its slip raises `!Failed`, but its committed value **drives nothing**: threading a second free-valued `!StepData` into the send opened source chains that never closed. Misdirection comes only from the fingerprint compare. So "wrong recipient in the To field" is *not* a leak route in the model, though the mock and the plan treat it as one. |
| `PlaintextAtProvider` as a named non-`Out` outcome | **MET** | and it is what keeps breach ⇔ mistake honest. |
| RFC pairs | 4 of 5 | `send-disabled-until-verify`, `no-plaintext-fallback`, `forward-guard`, `confirm-before-session` (kdf). The `show-password reveal` and `subject-reminder` pairs are absent (their levers were never built). |

---

## D. Shortcomings of the refactor itself (things that are simply weaker now)

1. **The density story is now half-declared, half-derived** (see B1). σ2/σ9 trust a marker; σ8/σ_ADDITIVE
   still count real prompts. This inconsistency is not principled — it is where the budget bit.
2. **Exposure-only controls are counted but never performed.** This is sound (and is what makes them free),
   but it means the model proves nothing about what a user *does* with the Reply button, the badges, or the
   overflow menu. They exist only to make the density detectors fire.
3. **Blake's compare/confirm are not adversary-mediated.** Alex's fingerprint compare reads `In(offered)`;
   Blake's trusted-key compare and link-confirm read *fixed constants*. Dropping the `In()` was necessary
   for the budget, but it means Blake cannot be shown a *substituted* key or a *genuinely different*
   phishing origin — his mistakes are mask-driven only. `PwEnteredAtImpostor` fires because Blake
   auto-approved, not because an impostor page was actually presented to him.
4. **One-party stress.** Each stressed profile stresses Alex *or* Blake, never both (except `K4`). Real
   ceremonies degrade both ends at once; the model cannot see interactions between two degraded humans.
5. **T5 lost its teeth.** The plan's completion-under-onset lemma pins `onset < finish` and conjoins
   "no unsafe outcome". Both made the exists-trace search wander, so most profiles use the fallback form:
   an *unordered* conjunction with the unsafe conjunct dropped. The lemma now says "the onset happens and
   the ceremony completes", not "the ceremony completes *despite* the onset".
6. **`--auto-sources` is unusable here** (heap-exhausts), so the model depends entirely on hand-kept
   structural discipline (shallow sources, single-source joins). There is no automated safety net: a future
   edit that deepens a source will simply stop terminating, with no diagnostic pointing at the cause.
7. **The kdf messenger's K3 is the one deep poser left** (`IF_k3_*` poses off `AlexBoth`, three hops from
   init). It proves fast today; it is the first thing that will break if the K-profiles grow.
8. **`MEMORY.md` lesson 10's "≤5 min" is now wrong** (the budget is 3 min) and the repo's older prose still
   describes the ambient-surface world. Docs were refreshed in step 10, but older design notes
   (`mask_machinery_formalization.md`, `usability_extension_plan.md`) were **not** revisited.

---

## E. What the refactor did deliver (for balance)

- The **prompt/perform seam** is real: `Prompt` is linear and consumed by the mask; `!Demand` is the
  persistent signal the stressors read. Density and performance are now *different facts*, which is what
  makes "counted but never performed" expressible at all.
- **Order violation is a first-class, proved property in two ceremonies** (`SendPremature`,
  `SessionUnconfirmed`) from **one** ceremony-blind core lever — the strongest generality claim in the
  build, and the thing the old model could not express at all.
- The **(S) boundary list is proved once** (`H_leak_routes`) and consumed by every profile: per-profile T6
  costs 8 steps instead of 261.
- The private-wire kdf makes **"only Alex and Blake know sk" statable and non-vacuous**, with the
  compositional payoff (one leaked nonce is provably insufficient) actually proved.
- `core/` contains **no ceremony vocabulary** (grep-audited), and both new core blocks
  (`MASK_TRANSCRIBE`, `OUTCOME_PREMATURE`) are armed by **both** ceremonies.
