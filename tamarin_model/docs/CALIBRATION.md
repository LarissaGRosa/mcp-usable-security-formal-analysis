# Lexicon calibration — levels, populations, sensitivity (ROADMAP #4)

The lexicon ([`core/demands.spthy`](../core/demands.spthy)) is where the HCI judgment lives: it maps
an action to a usability dimension + **level**. For the analysis to be credible enough to back an RFC,
the levels must be defensible, population-aware, and their influence on the conclusions must be
checked. This document is the calibration methodology.

> **V3 (2026-07-10).** Levels are a live model input: lookup detectors fire on a BAND
> (`!Demands(...,lvl) & !AtLeast(lvl, thr)`, order seeded in `core/framework.spthy`). Two consequences
> here: **(1) Population = threshold-shift.** An expert experiences a step at a lower level; the SAME
> detector then can't cross its threshold. `alex_blake_kdf/P9` proves it — `POP_EXPERT` rates compute
> `'lo'`, so σ₁ (threshold `'hi'`) never fires and the expert never slips (contrast P1). This is the
> §2d lever: recalibrate the level, re-prove, read whether the outcome flips. **(2) Additivity.** Two
> `'med'`-rated steps that are each individually safe can still sum to overload (`SIGMA_ADDITIVE` in
> `core/stressors.spthy`, P10) — so calibrating a step to `'med'` is NOT a proof of safety under
> co-occurring moderate demands. **Out of symbolic scope (deferred):** a per-individual PROBABILITY of
> degrading; the model bounds the *reachable* responses and the population lever scopes *whose*
> threshold, but a genuine nondeterministic mask-SET per stressor is future work.

## 1. Levels are ordinal buckets of a measured construct

Each `!Demands(action, dimension, level)` row is one claim. The `dimension` is a NASA-TLX subscale
(Mental/Temporal Demand, Effort, Performance, Frustration; Hart & Staveland 1988) or a cited non-TLX
construct (Arousal → Yerkes–Dodson 1908). NASA-TLX scores each subscale **0–100**; the model buckets
that continuum into ordinal levels:

| level | TLX band (guide) | meaning |
|---|---|---|
| `'lo'` | ~0–33 | within easy capacity |
| `'med'` | ~34–66 | noticeable load |
| `'hi'` | ~67–100 | overwhelming — crosses a `'hi'`-threshold detector |

**Provenance.** Each baseline row should cite its basis (a measured/median TLX for that operation, or a
documented expert estimate). The current rows are expert estimates grounded in the cited literature
(e.g. a key-fingerprint *compare* is high Effort — Whitten & Tygar 1999); replace with measured TLX/SEQ
values where available. Calibration = swapping a level for a data-backed one and re-proving.

## 2. Detectors fire on a band — the threshold is the knob

The lookup detectors (σ₁/σ₃/σ₆/anxiety) read `!Demands(action, dim, lvl) & !AtLeast(lvl, thr)`.
The order `'lo' < 'med' < 'hi'` is seeded once in `core/framework.spthy`. So:

- A step rated `'lo'` does **not** trip a detector whose threshold is `'hi'` (expert population, hardened UI).
- A step at `'med'` does **not** trip a `'hi'`-threshold detector by itself — but two `'med'` steps can
  still trigger `SIGMA_ADDITIVE` (P10).
- Recalibrating a step from `'hi'` to `'med'` **silently disables** single-step σ₁/σ₃/σ₆/anxiety for
  that action — the auditable knob.

This is the terminating, auditable choice documented in
[`AGNOSTIC_STRESSOR_INTERFACE.md`](AGNOSTIC_STRESSOR_INTERFACE.md) §5 and implemented in
[`STRESSORS.md`](../STRESSORS.md) §1.

## 3. Per-population profiles

A **population is a demand profile** — like an interface (ROADMAP #2), but a property of the *user*, not
the system. For the same step, an expert experiences lower demand than a novice. The baseline lexicon is
the **novice/default**; alternative populations are selected by `#define` in the profile, which arms one
block in `core/demands.spthy`:

| population | flag | compute Mental/Temporal | slip on CALC? |
|---|---|---|---|
| novice (baseline) | `LEXICON_DEFAULT` | `'hi'` | **reachable** — `P1_slip_reachable` |
| expert | `POP_EXPERT` | `'lo'` | **unreachable** — `P9_no_slip` |

`P1` (novice) and `P9_population` (expert) are the worked pair. **The workload stressors (σ₁ Mental, σ₃
Temporal, σ₆ Effort) are population-sensitive**; the environmental ones (σ₂ distraction, σ₈ habituation,
σ₉ alert-volume) are not (a population does not change how often the system bombs you with prompts), so a
population file only shifts the workload rows. RFC consequence: **a ceremony safe for experts may be
unsafe for novices → the analysis MUST cover the least-skilled intended population**, or the interface
must lower the demand for everyone (cf. `P7_interface`). (The descoped "Elder" persona is just another
`#define` block in `demands.spthy` — higher demand across more dimensions.)

## 4. Sensitivity method

A conclusion may hinge on one level choice. To check:

1. **Vary the level.** For each row a conclusion depends on, re-prove with the level lowered (e.g.
   `'hi'` → `'med'`). If the stressor stops firing (and the bad outcome becomes unreachable), the
   conclusion is *sensitive* to that boundary — flag it and tighten the underlying measurement.
2. **Vary the population.** Re-prove under each intended population profile (novice / expert / …). A
   reachability that holds only for novices is a population-scoped finding, not a universal one.
3. **Report what was assumed.** State, per conclusion, which `(action, dimension, level)` rows it relied
   on. A reachability lemma that needs `compute = MentalDemand 'hi'` is only as strong as that bucket.

The band design (§2) makes this mechanical: change a `!Demands` row or swap the demand-profile flag,
re-run `check.py --prove`.
