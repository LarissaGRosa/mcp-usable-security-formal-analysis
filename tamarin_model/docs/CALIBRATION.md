# Lexicon calibration — levels, populations, sensitivity (ROADMAP #4)

The lexicon ([`core/lexicon_tlx.spthy`](../core/lexicon_tlx.spthy)) is where the HCI judgment lives: it
maps an action to a usability dimension + **level**. For the analysis to be credible enough to back an
RFC, the levels must be defensible, population-aware, and their influence on the conclusions must be
checked. This document is the calibration methodology.

> **V3 (2026-07-10).** Levels are now a live model input, not a fixed `'hi'`: detectors fire on a BAND
> (`!Demands(...,lvl) & !AtLeast(lvl, thr)`, order in `core/types.spthy`). Two consequences here:
> **(1) Population = threshold-shift.** An expert experiences a step at a lower level; the SAME
> detector then can't cross its threshold. `alex_blake_kdf/P9` proves it — `population_expert` rates
> compute `'lo'`, so σ₁ (threshold `'hi'`) never fires and the expert never slips (contrast P1). This
> is the §2d lever: recalibrate the level, re-prove, read whether the outcome flips. **(2) Additivity.**
> Two `'med'`-rated steps that are each individually safe can still sum to overload
> (`core/stressors/additive_load.spthy`, P10) — so calibrating a step to `'med'` is NOT a proof of
> safety under co-occurring moderate demands. **Out of symbolic scope (deferred):** a per-individual
> PROBABILITY of degrading; the model bounds the *reachable* responses and the population lever scopes
> *whose* threshold, but a genuine nondeterministic mask-SET per stressor is future work.

## 1. Levels are ordinal buckets of a measured construct

Each `!Demands(action, dimension, level)` row is one claim. The `dimension` is a NASA-TLX subscale
(Mental/Temporal Demand, Effort, Performance, Frustration; Hart & Staveland 1988) or a cited non-TLX
construct (Arousal → Yerkes–Dodson 1908). NASA-TLX scores each subscale **0–100**; the model buckets
that continuum into ordinal levels:

| level | TLX band (guide) | meaning |
|---|---|---|
| `'lo'` | ~0–33 | within easy capacity |
| `'med'` | ~34–66 | noticeable load |
| `'hi'` | ~67–100 | overwhelming — the stressor fires |

**Provenance.** Each baseline row should cite its basis (a measured/median TLX for that operation, or a
documented expert estimate). The current rows are expert estimates grounded in the cited literature
(e.g. a key-fingerprint *compare* is high Effort — Whitten & Tygar 1999); replace with measured TLX/SEQ
values where available. Calibration = swapping a level for a data-backed one and re-proving.

## 2. Detectors exact-match `'hi'` — the threshold is the bucket boundary

The lookup detectors (σ₁/σ₃/σ₆/anxiety) fire on `!Demands(_, dim, 'hi')` **exactly**. So:

- A step at `'lo'` or `'med'` does **not** trip the stressor (the user is within capacity).
- Recalibrating a step from `'hi'` to `'med'` **silently disables** that stressor for that step.

This is the simple, terminating choice (no order relation on the level atoms; see
[`AGNOSTIC_STRESSOR_INTERFACE.md`](AGNOSTIC_STRESSOR_INTERFACE.md) §5). A "fires at ≥ med" semantics is
possible but needs an explicit order encoding — deferred, because exact-match makes the bucket boundary
the auditable knob.

## 3. Per-population profiles

A **population is a demand profile** — like an interface (ROADMAP #2), but a property of the *user*, not
the system. For the same step, an expert experiences lower demand than a novice. The baseline lexicon is
the **novice/default**; alternative populations are seeded by a population file included *instead of* the
baseline:

| population | file | compute Mental/Temporal | slip on CALC? |
|---|---|---|---|
| novice (baseline) | `core/lexicon_tlx.spthy` | `'hi'` | **reachable** — `P1_slip_reachable` |
| expert | `core/population_expert.spthy` | `'lo'` | **unreachable** — `P9_no_slip` |

`P1` (novice) and `P9_population` (expert) are the worked pair. **The workload stressors (σ₁ Mental, σ₃
Temporal, σ₆ Effort) are population-sensitive**; the environmental ones (σ₂ distraction, σ₈ habituation,
σ₉ alert-volume) are not (a population does not change how often the system bombs you with prompts), so a
population file only shifts the workload rows. RFC consequence: **a ceremony safe for experts may be
unsafe for novices → the analysis MUST cover the least-skilled intended population**, or the interface
must lower the demand for everyone (cf. `P7_interface`). (The descoped "Elder" persona is just another
population file — higher demand across more dimensions.)

## 4. Sensitivity method

A conclusion may hinge on one level choice. To check:

1. **Vary the level.** For each `'hi'` row a conclusion depends on, re-prove with it set to `'med'`. If
   the stressor stops firing (and the bad outcome becomes unreachable), the conclusion is *sensitive* to
   that boundary — flag it and tighten the underlying measurement.
2. **Vary the population.** Re-prove under each intended population profile (novice / expert / …). A
   reachability that holds only for novices is a population-scoped finding, not a universal one.
3. **Report what was assumed.** State, per conclusion, which `(action, dimension, level)` rows it relied
   on. A reachability lemma that needs `compute = MentalDemand 'hi'` is only as strong as that bucket.

The exact-match design (§2) makes this mechanical: the only knob is which rows are `'hi'`, so a
sensitivity pass is "flip a row to `'med'`, re-run `check.py --prove`."
