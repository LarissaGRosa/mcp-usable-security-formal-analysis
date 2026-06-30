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

### 1. Make the response layer (masks) agnostic too  ·  *status: IN PROGRESS — compute cluster done*

> Design: [`AGNOSTIC_MASKS.md`](AGNOSTIC_MASKS.md). Finding: masks are **not** a mechanical mirror of the
> stressor migration — they produce ceremony-specific protocol facts, so the split is behaviour-policy in
> `core/` (`outcome_policy.spthy` + `<class>_behavior.spthy` → a generic `Respond` event) + thin per-output
> effect adapters in the ceremony. **Pilot landed (compute):** `Calc_*` + `Op_*` (6 files) collapsed into
> `core/masks/outcome_policy.spthy` + `core/masks/compute_behavior.spthy` + two 1-line adapters
> (`compute_keyresult` / `compute_opresult`); all 56 checks green. **Remaining:** roll to compare, confirm/
> approve, decide, authorize, and the `*_share` outcomes.

**Gap.** We migrated `f_U` (stressors) to read generic `!Step`, but `f_H` (masks) still pattern-match
task facts: there are three Busy masks (`busy_calc` / `busy_op` / `busy_share`), three Careless, etc.
A ceremony with a new action still needs **new mask files** — the heavy, expert part.

**Why it blocks the goal.** Adoption requires the human layer to be a single `#include` + `!Step`
annotations. Today it is not.

**Change.** Mirror the `!Step` migration on the masks: a mask keys on the **action category** and emits
a generic outcome (`busy` on `compute` → slip; on `confirm` → auto-handle; `naive` on `compare` →
mistake; …). Collapse the per-action mask files into per-mask × per-action-class rules. End state: the
whole human layer is one include; a new ceremony adds zero `core/` files.

### 2. First-class interfaces as demand-transformers  ·  *status: not started (germ exists in P6 / S1)*

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

### 3. A usability-security property library (lemma templates)  ·  *status: not started*

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

### 4. Calibrate the lexicon  ·  *status: not started*

Levels are binary `'hi'` and expert-asserted. For defensibility: tie levels to **published/empirical
TLX or SEQ data**, add **per-population profiles** (novice vs expert; the descoped "Elder" persona),
and a **sensitivity pass** (does the conclusion survive a one-notch-lower level?).

### 5. Mental-model / belief state  ·  *status: not started (toehold: P5 Pathway B)*

Masks model degraded *execution*; they do not model **wrong beliefs** (the human thinks they reached
the bank / that the key is verified). Most real usability-security failures — phishing, spoofed-origin
acceptance — live there. Add a belief-state layer; Pathway B (misleading terminology) is the toehold.

### 6. Adversary-induced stressors  ·  *status: not started (toehold: injected prompts)*

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

### 9. Proof-results → RFC-text generator  ·  *status: not started*

The end artifact: a report turning proven lemmas into normative language ("MUST display fingerprint
diff", "SHOULD require number-matching"). This is what makes the tool *for RFC authors*.

### 10. Validation against real incidents  ·  *status: not started*

Map modeled outcomes to real CVEs / incidents (MFA-fatigue attacks, TLS warning click-through, PGP
misuse) so the "usability problems arising from the ceremony" are grounded in reality.

---

## Recommended sequence

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
| 1 | Agnostic masks (response layer) | 1 | in progress — compute cluster done (compare/confirm/decide/authorize/share left) |
| 2 | First-class interfaces as demand-transformers | 1 | not started |
| 3 | Usability-security property library | 1 | not started |
| 4 | Calibrate the lexicon (empirical levels, populations) | 2 | not started |
| 5 | Mental-model / belief state | 2 | not started |
| 6 | Adversary-induced stressors | 2 | not started |
| 7 | Attach-to-real-protocol + termination playbook | 3 | not started |
| 8 | Static analyzer (propose `!Step` + lexicon) | 3 | not started |
| 9 | Proof-results → RFC-text generator | 3 | not started |
| 10 | Validation against real incidents | 3 | not started |
