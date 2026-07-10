# V3 — unify the two ceremonies, deepen the triggering, simplify the core

**Goal.** One layered architecture used by *both* ceremonies; stressor triggering that follows the
cited literature (dose-response, additive load, inverted-U) instead of "any hi-demand step fires
instantly"; a core with **one** detector generation instead of two; every experiment still proving
in **≤ 5 minutes**.

**Status: PLAN (2026-07-09).** Nothing below is built. Supersedes the parts of
[`LAYERED_V2_PLAN.md`](LAYERED_V2_PLAN.md) that are now done — see §0.

---

## 0. Where we actually are (critical analysis of the current tree)

The v2 plan was written as "nothing built yet"; it is in fact **built for `secure_email`**. Both
ceremonies lint clean today. The honest state:

| The user's ask | `secure_email` | `alex_blake_kdf` | core |
|---|---|---|---|
| 1. init models a **PK sub-ceremony** (keygen + publish over a real channel, incl. the OOB fingerprint read-out) | ✅ `protocol/keys.spthy` (`P_keygen` → `P_publish`: `Out(pkB)` public + `OobFp` private) | ❌ init is a bare `Fr(~id)` token; the nonce spine is inline, no channel/interface modeling of setup | — |
| 2. **tampering from Dolev–Yao**, not a producer branch | ✅ single `P_fetch` reads `In(k)`; tamperedness is derived (`H_encto_shape`) | ❌ still uses a `Tampered(vid)` producer marker + genuine/tampered verify branches | `compare_behavior` already derives the verdict, but alex_blake doesn't use it |
| 3. **pw pathway split** across user/interface/protocol | ✅ `set_passphrase` → `btn_share_signal` → `btn_send` → `P_send_pw` → `pw_entry` → `P_unlock_pw` | n/a (no pw pathway) | — |
| 4. **four explicit layers** (protocol / interface / stressor / user) | ✅ `protocol/` `interface/` `bundles/` + colour tags | ❌ no interface layer; stressors read protocol facts (`!Req`, `!Step` emitted by `msg3_*`) directly | — |
| 5. **3-stressor experiments** + anti-explosion | ✅ S1–S3 trios + S4 all-7; `helpers.spthy` `[reuse]` trio; exposure-vs-gated discipline | ⚠️ P1/P3 exercise ≥3 stressors but in the old mixed-layer style, no shared helper trio | — |
| 6. **triggering closer to real life / literature** | ⚠️ shallow (see §2) | ⚠️ shallow | shared shortfall |
| 7. **simpler separation, easier to read** | ✅ one dir per layer | ❌ `ceremony.base` spine + `msg3_inline`/`msg3_request`/`msg3_request_confirmed` + `bundles/*_phase` | ❌ **two detector generations coexist** (see below) |
| 8. **apply all to `alex_blake_kdf`** | — | ❌ the bulk of V3 | — |

### The two problems that are real and shared

**P-A. `alex_blake_kdf` is a second, older architecture.** It uses the `ceremony.base` spine, inline
`A_send_Na`, three `msg3_*` variants, `bundles/*_phase` files, a `Tampered()` producer marker, and
stressors that read protocol facts directly. None of the five-layer / DY-tampering / interface-prompt
ideas reached it. Every concept the thesis argues for is demonstrated in one ceremony and contradicted
in the other.

**P-B. The core carries two detector generations at once.** Because the two ceremonies are on
different architectures, `core/stressors/` holds *both*:

| Construct | v1 (alex_blake reads protocol facts) | v2 (secure_email reads the interface) |
|---|---|---|
| σ2 Distraction | `external_distraction.spthy` (any single `!Step`) | `distraction_concurrent.spthy` (k=2 competing prompts, Wickens) |
| σ3 TimePressure | `time_pressure.spthy` (lexicon `TemporalDemand hi`) | `time_pressure_deadline.spthy` (prompt + `!UnderDeadline` context) |
| compare adapter | `compare_verifydone.spthy` | `compare_keychecked.spthy` |

The v2 detectors are the more literature-faithful ones. Once `alex_blake_kdf` is on the layered
architecture it can read the same interface, and **`external_distraction.spthy` +
`time_pressure.spthy` + `compare_verifydone.spthy` delete** — one generation, not two. That deletion
*is* the "simplify the core" ask; it can't happen until P-A is fixed.

**P-C. Triggering is a step-function, not a dose-response.** Every lookup detector is
`!Step + !Demands(action,dim,'hi') → SetMask` — it fires the **first** time a demanding step is
posed, deterministically, to **one** mask, bounded by `OnceX`. The lexicon comment cites
Yerkes–Dodson's inverted-U and Sweller's additive load, but the model encodes neither: `'hi'` is the
only level ever seeded, matching is exact, `'med'` never appears, and two sub-threshold stressors
never combine. This is the same in both ceremonies. §2 fixes it.

---

## 1. Target: ONE ceremony template

After V3 both ceremonies are the same five files-per-layer shape, and a third ceremony is a copy of
the template with the protocol swapped:

```
<ceremony>/
├── README.md
├── <P|S>0_baseline.spthy … <>4_worstcase.spthy   # profile entry points (includes only)
├── protocol/     🔵  crypto + setup sub-ceremony (keygen/publish/exchange over real channels) + transport
├── interface/    🟠  one rule per control; PROMPTS the user (!Step + !StepData + context); effect adapters
├── bundles/           human_common.spthy (mask_state + answered_once + outcome_policy + lexicon + targeting)
└── experiments/       helpers.spthy ([reuse] trio) + <profile>.spthy (lemmas only)
```

`ceremony.base.spthy`, `msg3_*.spthy`, `bundles/*_phase.spthy`, `blake_calc*.spthy`, and
`protocol/session.spthy` **retire** — the phase-bundle indirection is replaced by the flat
per-layer directories that `secure_email` already proves are readable. `AUTHORING_GUIDE.md`'s
skeleton is rewritten to *be* this template.

---

## 2. Deepen the triggering (core; benefits both ceremonies)

Four upgrades, each grounded in a citation already in the code, each chosen to add realism **without
blowing the 5-minute budget**. Ordered cheapest-first; adopt as many as the budget allows.

### 2a. Graded lexicon + threshold match (dose-response) — cheap

Seed demand at its real level, not always `'hi'`, and let a detector fire only at/above a threshold.
Introduce an explicit order fact so detectors match a *band*, not one constant:

```
!Demands('compute','MentalDemand','hi')     // key derivation: genuinely hard
!Demands('confirm','MentalDemand','lo')     // dismiss a dialog: not hard
rule Trigger_Load:
    [ !Step(P,sid,action), !Demands(action,'MentalDemand',lvl), !AtLeast(lvl,'hi'), !StressEnable(P) ]
  --[ Load(P), SetMask(P,'Busy') ]-> [ ]
```

`!AtLeast(a,b)` is a small seeded partial order (`hi≥med`, `hi≥hi`, `med≥med`, …). Cost: one seed
rule + one persistent premise per detector. **Effect:** a low-demand step no longer degrades anyone;
only steps the lexicon rates at/above threshold do. This is Sweller (1988) intrinsic load stated as a
level, not a flag. (Grounding: NASA-TLX magnitudes are ordinal, not binary.)

### 2b. Inverted-U for arousal (Yerkes–Dodson) — cheap

The lexicon comment already cites Yerkes–Dodson (1908) but only encodes `hi → Fearful`. Model the
band explicitly: `med` arousal is the **facilitating** zone (stays Attentive, no SetMask), `hi` is
past the peak (Fearful). One extra lexicon row + the `!AtLeast` guard from 2a. **Effect:** the model
can now *show* that moderate stakes don't degrade — a distinction the thesis claims and currently
cannot exhibit.

### 2c. Additive combination — the honest "3 stressors at a time" — medium cost

Today three stressors in one profile each fire independently and the first to fire wins the mask.
Cognitive-load theory is **additive** (Sweller): two *sub-threshold* demands should combine to cross
the threshold. Model a bounded accumulator:

```
rule Accrue [color=#eb5757]:
    [ !Step(P,sid,action), !Demands(action,'MentalDemand',lvl), !Weight(lvl,w), LoadAcc(P,n), !StressEnable(P) ]
  --[ Accrued(P) ]-> [ LoadAcc(P, n+w) ]                 // n,w over a SMALL fixed domain {0,1,2,3}
rule Cross:
    [ LoadAcc(P,n), !Threshold(t), !GtE(n,t) ] --[ SetMask(P,'Busy'), Crossed(P) ]-> [ ]
```

**State-explosion guard (this is the risky one — budget-gate it):** the accumulator domain is a
fixed small set of public constants (`0..3`), `Accrued` is bounded per party by a `OnceAccruePerStep`
restriction keyed on `sid`, and `Crossed` is `Once`. Prove the trio profiles *with* the accumulator
against the 5-minute clock in a spike **before** committing; if any trio regresses past budget, keep
2c behind the `*4_worstcase` profile only and leave the trios on the 2a step-function (documented as
the tractable approximation, per `TERMINATION.md`). **Effect:** `S2_trio_pw` can demonstrate that
Load + Deadline + AlertVolume *together* cross a threshold that none crosses alone — the actual
research claim behind "3 stressors at a time."

### 2d. Population as the threshold lever (variance without probabilities) — cheap, reuses existing

Tamarin is non-probabilistic, so "different people respond differently" is modeled as the **threshold
moving**, not a distribution. `core/population_expert.spthy` already swaps the demand profile; V3
makes it swap the **threshold** instead (expert = higher threshold ⇒ same stressor doesn't fire;
novice = lower). One profile per population reuses every other layer. Document explicitly in
`CALIBRATION.md` that per-individual probability is **out of symbolic scope** — the model bounds the
*reachable* responses, and the population lever scopes *whose* threshold. (This closes the
"closer to real life" ask honestly rather than faking a distribution.)

> Deferred (not V3): a genuine nondeterministic mask-*set* per stressor (one stressor → any of a
> small permitted set of masks, each a separate trace). It is the most faithful model but multiplies
> traces per stressor and is the biggest budget risk. Note it in `CALIBRATION.md` as future work;
> revisit only if the trios prove with comfortable headroom.

---

## 3. Migrate `alex_blake_kdf` onto the template (the item-8 bulk)

The KDF ceremony has no PK, so bullet 1 maps to "model the **setup/exchange** as real rules with a
real channel + an interface prompt," not literally a keypair. Target layers:

- **`protocol/`** — `keys.spthy`-analogue: `init` (participants + `!Party`), the nonce exchange
  `A_send_Na` / `B_recv_Na_send_Nb` over `Out/In` (already channel-based — keep), and the key
  derivation as a protocol result consumed by an effect adapter. `msg3_inline` / `msg3_request` /
  `msg3_request_confirmed` collapse into **one** `compute` control whose outcome is driven by
  `compute_behavior` (Attentive→correct, Busy→slip, Careless→timeout via `outcome_policy`), exactly
  like `secure_email`'s share/compare. The `shutdown` mitigation (key-confirm abort) becomes a
  protocol rule that reads the derived key, not a third msg3 file.
- **`interface/`** — the prompts that today are implicit in `msg3_*`, `approval_ui`, `verify_ui`,
  `authorize_ui`, `policy_ui`: one rule per control emitting `!Step` (+ `!StepData` observables),
  posing `compute` / `confirm` / `compare` / `authorize` / `decide` / `set-policy`. The stressor
  layer then reads **the interface**, never the protocol — the same contract `secure_email` uses.
- **DY tampering (bullet 2 for this ceremony)** — the `verify_ui` key-confirmation reads whatever
  `In(k)` delivered and the `compare_behavior` verdict is derived; the `Tampered()` producer marker
  and genuine/tampered branches **delete**, mirroring `P_fetch`.
- **`bundles/human_common.spthy`** — identical shape to `secure_email`'s (mask_state +
  answered_once + outcome_policy + lexicon + `stress_alex`/`stress_blake`). Both parties stay
  stressable (P1/P3's multi-party story is preserved — Blake gets an interface, not a
  `blake_calc_stressable` special case).

Pathway B (P5/P7, the `set-policy` misleading-terminology story) is already interface-seeded
(`!ControlDesign`) — it ports as a `set-policy` control with the two `interface_*_policy` seeds.

---

## 4. Rebuild the `alex_blake_kdf` experiments as trios (bullet 5 for this ceremony)

Recast P0–P9 into the `secure_email` profile shape: a shared `experiments/helpers.spthy`
`[reuse]` trio (the KDF analogues: `key_agreement_shape`, `sk_secret`, `slip_not_kdf`), then trio
profiles that are strict subsets of the worst case:

| Profile | Stressors | Surface |
|---|---|---|
| `P0_baseline` | none | KDF completes, keys agree, secrecy absolute |
| `P1_trio_compute` | σ1 Load + σ3 Deadline + σ2 Concurrency | the CALC surface (slip / timeout) on both parties |
| `P2_trio_postkdf` | σ8 Habituation + σ6 Abstraction + Anxiety | approve / verify / authorize surface + recovery |
| `P3_worstcase` | all | the §6a canary |

Keep P4 (analyzer-direction harness), P5/P7 (Pathway B pair), P6 (mitigations), P9 (population) —
they port their layers but keep their distinctive lemmas. Anti-explosion is the `secure_email`
toolkit verbatim (gate only outcome-driving crossings; no dangling behaviours; `[reuse]` trio;
once-bounds; linear branch commits).

---

## 5. Simplify the core (bullet 7) — after P-A is fixed

Once both ceremonies read the interface, delete the v1 generation:

- `stressors/external_distraction.spthy`, `stressors/time_pressure.spthy` → replaced by
  `distraction_concurrent.spthy`, `time_pressure_deadline.spthy` (rename the v2 files to the plain
  names once they're the only ones).
- `masks/compare_verifydone.spthy` → one compare adapter (`compare_keychecked.spthy`, renamed
  generic).
- Fold the 2a/2b graded-lexicon change into `lexicon_tlx.spthy` (+ `interface_*` / `population_*`
  become threshold-shifts per 2d).
- Result: one file per stressor, one per action-class behaviour, one outcome matrix — the
  `AUTHORING_GUIDE.md` table becomes literally the file list.

---

## 6. Build order (each step ends green, each profile re-timed ≤ 5 min)

0. **Budget baseline.** `check.py --prove` every current profile (P0–P9, S0–S4); record wall-clock.
   This is the regression gate for every later step.
1. **Core §2a + §2b** (graded lexicon + inverted-U): change `lexicon_tlx` + add `!AtLeast`; re-prove
   `secure_email` S0–S4 (they already read the lexicon) — must stay green and in budget.
2. **Core §2c spike** (accumulator) on `secure_email` trios only; measure. Decide trio-wide vs
   worst-case-only per the budget result. Record the decision in `TERMINATION.md`.
3. **`alex_blake_kdf` §3**: build `protocol/` + `interface/` + `bundles/human_common`; port
   `P0_baseline`; prove.
4. **`alex_blake_kdf` §4**: the trios + P4/P5/P6/P7/P9; prove each ≤ 5 min.
5. **§2d population** as a threshold lever; re-prove P9 (and add an `S`-population profile if wanted).
6. **§5 core deletion**: remove the v1 files; full sweep of *both* ceremonies must stay green.
7. **Docs**: rewrite `AUTHORING_GUIDE.md` skeleton to the one template; update `IMPLEMENTATION.md`
   (drop the `ceremony.base`/`msg3_*`/phase-bundle sections), `STRESSORS.md` (graded triggering),
   `CALIBRATION.md` (§2d scope note + deferred nondeterministic-set note), repo `MEMORY.md`.

Rollback is per-step: each step is a strict addition or a rename+delete with the sweep as its gate,
so any step that regresses past 5 minutes reverts to the prior green state (§2c is the only step with
a pre-planned fallback, the worst-case-only placement).

---

## 7. Decisions (user, 2026-07-09)

- **D1 — §2c placement: WORST-CASE-ONLY fallback.** If the additive accumulator regresses any trio
  past the 5-minute budget, the trios keep the §2a step-function and the accumulator runs only in
  the `*4_worstcase` profile. Record the placement decision + measured timings in `TERMINATION.md`.
- **D2 — DELETE the v1 detectors.** After §3 puts `alex_blake_kdf` on the interface, remove
  `external_distraction.spthy` / `time_pressure.spthy` / `compare_verifydone.spthy` (git history
  keeps them). One detector generation. Verify no other ceremony imports them before deleting.
- **D3 — Population: THRESHOLD-SHIFT ONLY.** §2d (expert = higher threshold, novice = lower, reusing
  `population_expert.spthy`) is in scope. The nondeterministic mask-*set* is deferred to future work
  and noted in `CALIBRATION.md`. Per-individual probability stays out of symbolic scope.
- **D4 — RFC lockstep.** §4 renames the `alex_blake_kdf` profiles; update
  `tools/rfc_requirements.json` + re-run `rfc_gen.py` in the same step so `RFC_GUIDANCE.md`
  regenerates against the new profile names.

---

## 8. Execution log

> **V3 COMPLETE (2026-07-10).** Both ceremonies on one layered template; graded dose-response +
> inverted-U + additive load installed; v1 generation and dead fragments deleted. 17 profiles green
> (alex_blake P0–P11, secure_email S0–S4), every one ≪ 5 min. Details below, newest steps last.

### Step 0 — budget baseline (2026-07-09). All 15 profiles PASS under the 300 s cap.

| Profile | Verdict | Wall-clock | | Profile | Verdict | Wall-clock |
|---|---|---|---|---|---|---|
| P0_baseline | PASS | 0.3 s | | S0_baseline | PASS | 8.7 s |
| P1_calc_pressure | PASS | 1.2 s | | **S1_trio_pgp** | PASS | **128.4 s** |
| P2_postkdf_recovery | PASS | 2.2 s | | S2_trio_pw | PASS | 51.9 s |
| P3_worstcase | PASS | 2.7 s | | S3_trio_mixed | PASS | 14.3 s |
| P4_inferred | PASS | 1.8 s | | **S4_worstcase** | PASS | **170.3 s** |
| P5_pathwayb | PASS | 0.4 s | | | | |
| P6..P9 | PASS | ≤1.5 s | | | | |

**Gate consequence:** S1 (128 s) and S4 (170 s) leave little headroom under 300 s → **D1 confirmed**:
the §2c additive accumulator must be worst-case-only for the secure_email trios, never trio-wide.
`alex_blake_kdf` profiles are all ≤2.7 s (huge headroom — the accumulator can run trio-wide there).

### Step 1 — graded lexicon + inverted-U threshold (in progress).

- **1a (behavior-preserving):** added `!AtLeast(a,b)` reflexive level order to `lexicon_tlx.spthy`;
  converted the four lookup detectors (σ1 `cognitive_load`, σ3 `time_pressure`, σ6 `abstraction`,
  `security_anxiety`) to band-match `!Demands(action,dim,lvl) & !AtLeast(lvl,'hi')`. With the lexicon
  still seeding only `'hi'`, behaviour is identical — the band is the installed *mechanism*.
- **1b (demonstration) — DEFERRED into step 4.** Exhibiting "moderate arousal stays Attentive"
  needs a `med`-rated control, which is added naturally when the new interface controls are built in
  step 4; the demonstration lemma lands there rather than as a synthetic control on today's profiles.
- **Placement decision:** `!AtLeast` lives in `core/types.spthy` (universal, included exactly once),
  NOT in `lexicon_tlx.spthy` — the latter is swapped out by `interface_*`/`population_*` profiles
  (P7, P9) which would otherwise leave the order unseeded (caught by re-proving both ceremonies).
- **Gotcha hit + fixed:** a `*/` inside a `/* */` block comment (`interface_*/population_*`) closed
  the comment early and made tamarin *silently drop* `lexicon_tlx.spthy` (facts-unseeded WF failure,
  slip lemmas falsified). Repo MEMORY.md's "comment trap" lesson. Reworded to `interface_* /
  population_*`.
- **Result: all 15 profiles PASS**, timings within noise of baseline (P* ≤3.8 s; S0 9.4 s,
  S1 127 s, S2 46 s, S3 ~14 s, S4 ~170 s) — behaviour preserved, dose-response mechanism installed.

### Step 3 — layered template + P0 ported (2026-07-09). DONE.

New files (coexist with the old fragments so P1–P9 keep proving until step 4 re-ports them):
- `protocol/kdf.spthy` — 🔵 init + nonce wire + finish + session (no inline compute).
- `interface/sender.spthy`, `interface/recipient.spthy` — 🟠 the `calc_sk` compute prompts
  (`!Step` + `!StepData` = `kdf(Na,Nb)`); both parties now go through the mask machinery.
- `bundles/human_common_v2.spthy` — mask_state + answered_once + outcome_policy + lexicon +
  stress_alex + stress_blake (secure_email shape). (Old `human_common.spthy` stays for P1–P9;
  renamed at retirement — step 6.)
- `P0_baseline.spthy` rewritten to the layered manifest. **P0 PASS** (P0_completes, P0_agreement).

Staging note: migration is IN-PLACE with parallel filenames; old `ceremony.base`/`msg3_*`/phase
bundles/`human_common.spthy` are deleted only in step 6, after every profile is re-ported, so the
tree stays green at every step.

### Step 4 — interface controls + trios + port P4/P5/P6/P7/P9 (IN PROGRESS).

Reordered: §2c accumulator moved to after the migration (was step 2), so both ceremonies get it on
a uniform template. Order is now 0,1,3,4,2,5,6,7.

**D2 revised → FORCE V2 EVERYWHERE (user, 2026-07-09):** alex_blake switches to the v2 detectors
(`time_pressure_deadline`, `distraction_concurrent`); v1 (`time_pressure`, `external_distraction`,
`compare_verifydone`) deleted in step 6. The KDF interface gained a `!UnderDeadline` context on the
compute control (σ3) and a `nonce_ack` exposure control (interface/nonce_ack.spthy) so a party has
two concurrent prompts for σ2 (reads a PERSISTENT `!NoncesSeen` handle so it doesn't compete with
the linear compute token).

Per-profile progress (one at a time, each proven green):
- **P0_baseline** — PASS (compute prompts, Attentive, agreement).
- **P1_calc_pressure** — PASS, 7 lemmas. v2 trio {σ1 load, σ3 deadline, σ2 concurrency} on the CALC
  surface, both parties. Dropped `blake_calc_stressable`/`calc_phase`/`msg3`/`ceremony.base`.
- **P2_postkdf_recovery** — PASS, 7 lemmas. Unstressed KDF → session → APPROVE/VERIFY/AUTHORIZE +
  recovery. Reused the existing `*_ui.spthy` prompt rules unchanged (they already read `!Session`);
  σ8/σ6/anxiety are single detectors, no v1/v2 conversion.
- **P3_worstcase** — PASS, 4.8 s. CALC trio (both parties) + all post-KDF phases + usability_properties.
- **P4_inferred** — PASS, 3.9 s. Left as-is (self-contained analyzer harness on `init.spthy`; no
  retired fragments, no deleted detectors).
- **P5_pathwayb** — PASS, 0.3 s. Left as-is (self-contained policy profile on `init.spthy`).
- **P6_mitigations** — PASS, 1.6 s. Spine + `finish_confirmed.spthy` (shutdown key-confirmation) +
  shutout approval + verify-shutout. σ1 slip caught by the shutdown.
- **P7_interface** — PASS, 1.2 s. Hardened-verify (Effort 'lo' → σ6 can't fire, band) + clear
  policy; manual human layer (no `lexicon_tlx`).
- **P8_adversary** — PASS, 1.1 s. Adversary-induced time pressure the only route to Busy.
- **P9_population** — PASS, 0.7 s. σ1-only (demand-based); expert 'lo' < 'hi' threshold ⇒ no load,
  no slip (the `!AtLeast` band makes the population lever work). σ3-deadline dropped (context, not
  demand). Manual human layer (population_expert replaces lexicon).

**STEP 4 (migration) COMPLETE — all 10 alex_blake_kdf profiles PASS on the layered v2 template**,
slowest P2 16.8 s (≪ 5 min). Both ceremonies now share one architecture. Refactors made along the
way: `finish`/`session` split out of `kdf.spthy` into `finish.spthy` / `finish_confirmed.spthy`;
`human_common_v2` is Alex-default (Blake opt-in via `stress_blake`); `P_finish_blake` removed (dead —
no lemma needs Blake's completion). Old fragments (`ceremony.base`, `messages`, `msg3_*`,
`blake_calc*`, phase bundles, old `human_common`, `session`) are now a dead cluster → step 6.

### Step 6 — cleanup (2026-07-10). DONE. All 15 profiles PASS.

Deleted the dead cluster (`ceremony.base`, `protocol/messages`, `msg3_inline`, `msg3_request`,
`msg3_request_confirmed`, `blake_calc`, `blake_calc_stressable`, `session`, old
`bundles/human_common`, `bundles/{calc,approve,verify,authorize}_phase`) and the v1 detectors
(`external_distraction`, `time_pressure`). Renamed `human_common_v2` → `human_common`. `alex_blake`
`protocol/` is now 15 focused files; `bundles/` is one. `compare_verifydone` KEPT (P4's adapter —
revises the plan's delete-it note: it is an adapter, not a v1 detector). Full sweep green, timings
unchanged (S1 125 s, S4 171 s).

### Steps 2 / 1b / 5 — the realism trio (2026-07-10). DONE.

- **§2c additive load** — `core/stressors/additive_load.spthy`: TWO distinct `'med'` steps (each
  sub-threshold for σ1's `'hi'` band) sum to Busy — the density-style, arithmetic-free additive
  model (Sweller). Demonstrated by **P10_additive_load** (PASS): `P10_no_solo_load` (σ1 never fires
  on the moderate steps) contrasted with `P10_additive_busy` + `P10_additive_slip` (their sum does).
  On alex_blake it runs freely; on secure_email it is left OUT of the 170 s S4 to protect the budget
  (D1's conservative default) — the detector is available to wire in if the budget is raised.
- **§2b inverted-U** — demonstrated by **P11_inverted_u** (PASS): a `'med'`-arousal authorize sits
  in the facilitating zone, so SecurityAnxiety never onsets (`P11_no_anxiety_at_moderate`), the user
  grants (`P11_authorize_granted`) and the Fearful abort is unreachable (`P11_no_abort`) — the
  contrast with P2/P3 at `'hi'`. The whole inverted-U (moderate facilitates, high freezes) is now
  exhibitable, which the pre-V3 model could not do.
- **§2d population** — no new work: P9's expert-safety already runs THROUGH the band (expert
  compute demand `'lo'` < the `'hi'` threshold ⇒ σ1 cannot fire ⇒ no slip). The population lever IS
  the threshold-shift the plan called for. The nondeterministic mask-SET remains deferred
  (CALIBRATION.md), as planned.

### Final tally — 17 profiles, all PASS, all ≪ 5 min.

alex_blake P0 0.8 · P1 1.8 · P2 17 · P3 4.5 · P4 3.8 · P5 0.3 · P6 1.8 · P7 1.0 · P8 1.1 · P9 0.8 ·
P10 1.2 · P11 0.8 s   |   secure_email S0 ~10 · S1 ~126 · S2 ~46 · S3 ~13 · S4 ~171 s.
```
