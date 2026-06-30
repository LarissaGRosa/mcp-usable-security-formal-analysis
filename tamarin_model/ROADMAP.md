# Roadmap — from a usability-ceremony model to an RFC-grade tool

## The goal

Let a **protocol designer / prover** take their ceremony and obtain **machine-checked proofs over the
human nodes** — how a human, under usability problems *arising from the ceremony and its interfaces*,
deviates from the prescribed steps and what that does to the security goal — so the results become
**normative, user-aligned guidance for an RFC** ("implementations MUST present X", "MUST require an
engaged-user value", …).

This document grades the current model against that goal and lays out what is missing, what can be
improved, and what should change, in priority order. Companion docs: [`IMPLEMENTATION.md`](IMPLEMENTATION.md)
(what exists), [`STRESSORS.md`](STRESSORS.md) (the stressor layer), [`AGNOSTIC_STRESSOR_INTERFACE.md`](AGNOSTIC_STRESSOR_INTERFACE.md)
(the trigger seam).

## Where we are

**Foundations worth keeping** (do not re-litigate):

- **The agnostic `!Step` trigger seam.** Every stressor detector reads a generic `!Step(P,sid,action)`
  (+ a cited lexicon row); no detector names a ceremony task. This is the *one thing a designer
  annotates*, and it is the right primitive.
- **The mask / stressor / mitigation separation** (`f_H` / `f_U` / Poka-Yoke restrictions), the
  persistent current-mask model, and per-party `!StressEnable` targeting.
- **Usability grounding:** NASA-TLX dimensions + cited non-TLX constructs (Yerkes–Dodson, alarm
  fatigue, warning habituation, MRT), stated once in `core/lexicon_tlx.spthy`.
- **Two ceremonies, 9 profiles, 56 lemma checks** proving green — a working proof of concept.

**Honest gap:** the model is still a **hand-crafted artifact by an expert**, not a **framework a
non-author can apply with bounded effort**. The "designer → usability proof → RFC guidance" path is
roughly 40% built: the trigger seam is done; the response layer, the interface story, the property
library, and the RFC deliverable are not.

---

## Tier 1 — blocks a designer from using this at all

### 1. Make the response layer (masks) agnostic too  ·  *status: ✅ DONE*

> Design: [`AGNOSTIC_MASKS.md`](AGNOSTIC_MASKS.md). Finding: masks are **not** a mechanical mirror of the
> stressor migration — they produce ceremony-specific protocol facts, so the split is behaviour-policy in
> `core/` (`outcome_policy.spthy` + `<class>_behavior.spthy`) + thin per-output effect adapters in the
> ceremony. **All seven action classes migrated** (compute, compare, confirm, decide, authorize, share,
> set-policy). `core/masks/` went from **22 per-(mask×action) files to 10** (one behaviour file per class
> + `outcome_policy` + 3 compare/share effect adapters). Every mask reads the agnostic `!Step` interface;
> the full human behaviour matrix lives once in `outcome_policy.spthy`. Pathway-B (`policy_behavior`) reads
> `!Step` but is task-mediated (no `outcome_policy`). All 56 checks green. Commits a8de8f4 (compute),
> 5edc9ae (compare), a0d472c (confirm/decide/authorize), 2bc40a4 (share/policy).

**Gap.** We migrated `f_U` (stressors) to read generic `!Step`, but `f_H` (masks) still pattern-match
task facts: there are three Busy masks (`busy_calc` / `busy_op` / `busy_share`), three Careless, etc.
A ceremony with a new action still needs **new mask files** — the heavy, expert part.

**Why it blocks the goal.** Adoption requires the human layer to be a single `#include` + `!Step`
annotations. Today it is not.

**Change.** Mirror the `!Step` migration on the masks: a mask keys on the **action category** and emits
a generic outcome (`busy` on `compute` → slip; on `confirm` → auto-handle; `naive` on `compare` →
mistake; …). Collapse the per-action mask files into per-mask × per-action-class rules. End state: the
whole human layer is one include; a new ceremony adds zero `core/` files.

### 2. First-class interfaces as demand-transformers  ·  *status: ✅ DONE (worked example)*

> An interface = a named demand profile (the `!Demands` rows it induces). A hardened interface lowers a
> step's demand so the stressor's `'hi'` precondition is never produced → the stressor can't fire (fixes
> the *cause*, upstream of P6's outcome-blocking mitigations). `core/interface_hardened_verify.spthy` +
> profile `P7_interface` prove the tampered-key mistake UNREACHABLE under the hardened verify interface,
> vs `P2_mistake_reachable` under the baseline — the proof pair yields the RFC requirement. Commit 3292b42.

**Gap.** "Interface" is implicit (`approval_ui`, `compose_ui` are just step producers). There is no
object that represents *what the interface does to the human's workload*.

**Why it blocks the goal.** The RFC payload **is** the interface requirement. The model must be able to
state and prove interface-level claims, not just protocol-level ones.

**Change.** Model an interface as a **demand-transformer**: a spec that raises/lowers a step's TLX
dimensions or adds/removes an affordance (e.g. a fingerprint-diff view lowers `compare`'s Effort;
number-matching adds an engaged-user value). Then the RFC-shaped lemma is provable directly:

> *Interface V removes the Effort on the compare step ⇒ σ₆ unreachable ⇒ no Naive acceptance of a
> tampered key.* → **"Implementations MUST render a visual fingerprint comparison."**

This generalizes the bespoke P6 mitigations into a principled `interface ⇒ demand-delta ⇒ provable
consequence` mechanism, and lets designers **compare interface variants** in one theory.

### 3. A usability-security property library (lemma templates)  ·  *status: ✅ DONE*

> `core/usability_properties.spthy`: two ceremony-agnostic includable invariants proven cross-ceremony
> (P3 + S0) — `UP_degradation_is_attributable`, `UP_degradation_requires_targeting` — plus four
> parameterized templates (usability-robustness, outcome-requires-stressor, breach attribution, the
> interface/mitigation lever pair) each with a filled-example pointer. Commit 3aaf299.

**Gap.** Every lemma is hand-written per ceremony. There is no analogue of Tamarin's standard
`secrecy` / `agreement` goals for the human layer.

**Why it blocks the goal.** A designer should *instantiate* properties, not author proofs.

**Change.** Ship parameterized, reusable lemmas:

- **usability-robustness** — no reachable human action breaks the security goal under stressor set S.
- **mitigatability** — every catastrophic outcome requires a stressor that some named interface
  mitigation removes.
- **attribution** — every breach traces to a `(stressor, step, interface)` triple.

End state of Tier 1: *annotate `!Step`, include the human layer + an interface spec, instantiate the
property templates* → a usability-robustness verdict in a day.

---

## Tier 2 — makes the results credible enough for an RFC

### 4. Calibrate the lexicon  ·  *status: ✅ DONE*

> A population is a demand profile (like an interface, #2, but a property of the user). `core/population_expert.spthy`
> + `P9_population`: the CALC phase for an expert (low workload demand) proves no slip, vs P1 (novice/baseline)
> where the slip is reachable — "a ceremony safe for experts may be unsafe for novices; cover the least-skilled
> population." `CALIBRATION.md`: ordinal level buckets over NASA-TLX 0–100, level provenance, the exact-match
> `'hi'` threshold as the auditable bucket boundary, population-sensitivity of workload vs environmental stressors,
> and the sensitivity method (flip a `'hi'` row to `'med'` / vary the population, re-prove). Commit 8ac4b30.

Levels are binary `'hi'` and expert-asserted. For defensibility: tie levels to **published/empirical
TLX or SEQ data**, add **per-population profiles** (novice vs expert; the descoped "Elder" persona),
and a **sensitivity pass** (does the conclusion survive a one-notch-lower level?).

### 5. Mental-model / belief state  ·  *status: ✅ DONE (worked example)*

> Masks model degraded EXECUTION; this adds a belief-state layer for wrong BELIEFS (phishing/spoofing) --
> an ATTENTIVE human acting correctly on a false picture, a breach ORTHOGONAL to the mask layer.
> `ceremonies/phishing/`: `Belief(P,id,ch)`; weak identity interface (belief from displayed claim →
> spoofable) vs strong (belief requires a verified binding → anti-spoofing). `PhishWeak` proves the
> Attentive user is phished + attribution to spoofing; `PhishStrong` proves the secret never leaks. The
> pair = "MUST bind the displayed peer identity to a verified credential." Reuses the #2 interface idea
> for authentication. Commit 045d2e0.

Masks model degraded *execution*; they do not model **wrong beliefs** (the human thinks they reached
the bank / that the key is verified). Most real usability-security failures — phishing, spoofed-origin
acceptance — live there. Add a belief-state layer; Pathway B (misleading terminology) is the toehold.

### 6. Adversary-induced stressors  ·  *status: ✅ DONE (worked example)*

> The dual of #2: the adversary RAISES a step's demand to induce a stressor (vs a good interface lowering
> it). `core/adversary.spthy` (inject urgency → !Urgent) + `core/stressors/time_pressure_induced.spthy`
> (adversary-induced σ₃, fires on !Urgent not the lexicon) + profile `P8_adversary`: a calm approval prompt
> where the adversary's urgency injection is the ONLY route to Busy → auto-approves the injected prompt.
> Proves the attack reachable AND attribution (SetMask(Busy) and AutoApprove both trace to a prior
> InjectUrgency). Defence = number-matching/shutout (P6). Commit c4d5752.

Stressors are environmental today. MFA-fatigue and prompt-bombing are the attacker **driving** the
human into a degraded mask. Let the Dolev–Yao adversary *cause* selected stressors (bomb prompts →
habituation; inject urgency → time pressure). This closes the loop and directly answers *which human
weaknesses the RFC must defend against because an attacker can weaponize them*. **Highest novelty** if
a research contribution is wanted.

---

## Tier 3 — scale and the RFC deliverable

### 7. Attach-to-real-protocol + termination playbook  ·  *status: not started*

Toy ceremonies don't make RFCs; FIDO2 / TLS / OAuth do. `!Step` makes attachment cheap in principle,
but the §6a state-explosion at real scale needs a documented narrowing strategy (cap enabled stressors
per party; per-phase compositional proofs).

### 8. Static analyzer: propose `!Step` + lexicon from the protocol  ·  *status: not started*

Fully realize the "analyzer direction": infer stressful steps from protocol structure (a step comparing
two long opaque values is high-Effort; a step under a timeout is temporally demanding), proposing the
annotations the designer confirms.

### 9. Proof-results → RFC-text generator  ·  *status: ✅ DONE — the deliverable*

> `tools/rfc_requirements.json` (manifest: 7 requirements, each = risk lemma + removed_by lemma + lever)
> + `tools/rfc_gen.py` (re-runs Tamarin, confirms each risk REACHABLE and each fix HOLDS, emits the
> requirement backed by the verified lemmas; UNVERIFIED if proofs don't line up). Output: `RFC_GUIDANCE.md`,
> 7/7 proven — low-effort fingerprint compare, number-matching MFA, key-confirmation, device-side compare,
> out-of-band secret, verified identity binding, least-skilled population. Every MUST/SHOULD traces to named
> lemmas in named profiles. Commit 68160ef.

The end artifact: a report turning proven lemmas into normative language ("MUST display fingerprint
diff", "SHOULD require number-matching"). This is what makes the tool *for RFC authors*.

### 10. Validation against real incidents  ·  *status: not started*

Map modeled outcomes to real CVEs / incidents (MFA-fatigue attacks, TLS warning click-through, PGP
misuse) so the "usability problems arising from the ceremony" are grounded in reality.

---

## Recommended sequence

**Tiers 1 and 2 are COMPLETE.** Tier 1: ✅ #1 agnostic masks, ✅ #2 first-class interfaces, ✅ #3 property
library (+ dead facts retired). Tier 2: ✅ #4 lexicon calibration, ✅ #5 belief state, ✅ #6 adversary-induced
stressors. A unifying through-line emerged — #2 (interface), #4 (population), #5 (identity interface), #6
(adversary) are all the SAME lever: a demand/belief profile a good interface lowers, an adversary raises, and
a population shifts. **Next: Tier 3 (scale + the RFC-text deliverable).** A designer can now apply the framework to a ceremony by emitting `!Step`
(+ `!StepData`), picking an interface (demand profile), and instantiating the property templates. Next is
Tier 2 (credibility) — **#6 adversary-induced stressors** is the standout — then Tier 3 (scale + the
RFC-text deliverable). Original sequencing notes:

Do the **adoption-blocking trio (1 → 2 → 3)** first — they build directly on the trigger seam:

1. **Agnostic masks** (mechanical mirror of the stressor migration; turns the human layer into one
   include). *Clean, low-risk, high payoff — the natural next engineering step.*
2. **First-class interfaces** (the strategic bridge to RFC normative text; generalizes P6).
3. **Property-template library** (so a new ceremony's proof is instantiation, not authoring).

Then Tier 2 for credibility (**#6 adversary-induced stressors** is the standout research item), and
Tier 3 to scale and produce the RFC deliverable.

## Status table

| # | Item | Tier | Status |
|---|---|---|---|
| 1 | Agnostic masks (response layer) | 1 | ✅ done — all 7 action classes; core/masks 22→10 files |
| 2 | First-class interfaces as demand-transformers | 1 | ✅ done — interface_hardened_verify + P7_interface |
| 3 | Usability-security property library | 1 | ✅ done — core/usability_properties (2 generic + 4 templates) |
| 4 | Calibrate the lexicon (empirical levels, populations) | 2 | ✅ done — core/population_expert + P9_population + CALIBRATION.md |
| 5 | Mental-model / belief state | 2 | ✅ done — ceremonies/phishing (PhishWeak/PhishStrong) |
| 6 | Adversary-induced stressors | 2 | ✅ done — core/adversary + time_pressure_induced + P8_adversary |
| 7 | Attach-to-real-protocol + termination playbook | 3 | not started |
| 8 | Static analyzer (propose `!Step` + lexicon) | 3 | not started |
| 9 | Proof-results → RFC-text generator | 3 | ✅ done — tools/rfc_gen.py + RFC_GUIDANCE.md (7/7 proven) |
| 10 | Validation against real incidents | 3 | not started |
