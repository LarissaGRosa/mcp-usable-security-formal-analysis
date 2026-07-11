# `tamarin_model` — what is implemented and how

> **V3.2 (2026-07-10): PROMPT/PERFORM seam — the interface prompts, the user performs.** The interface
> no longer declares the human's step. It only **poses a prompt** `!Prompt(P,pid,action)` and **displays**
> observables `!Displayed(P,pid,shown)`. The stressor detectors read `!Prompt` (fatigue is from being
> *shown* prompts; σ₁₀ still reads the human `!Failed`). The user's mask (`core/masks.spthy`) reads
> `!Prompt`+`!Displayed`, **performs** the step, and — where a downstream rule needs the value — commits
> `!StepData(P,pid,committed)` (the mask-dependent value the human stands behind: the reference-checked
> vs offered key at `compare`, the chosen recipient/channel at `share`, the produced key at `compute`).
> The interface's *advance* rules and the share→channel effect adapters consume that committed
> `!StepData`; the kdf key-confirmation shutdown reads the interface's `!Displayed` (the objective correct
> key). Wherever §2/§5 below say the interface emits `!Step`/`!StepData`, read `!Prompt`/`!Displayed`
> (posed by the interface) and `!StepData` (committed by the mask). Design record + step log:
> `MEMORY.md` lessons 18–19. All 17 profiles prove green under this seam.
>
> **V3.1 (2026-07-10): FLAT one-file-per-layer layout with `#ifdef` selection.** The ~105 tiny
> fragment files were consolidated to one file per model layer. `core/` is now six files —
> `framework.spthy` (types + transitions + the outcome matrix, always on), `masks.spthy`,
> `stressors.spthy`, `demands.spthy`, `knobs.spthy`, `properties.spthy` — and each ceremony is
> `base.spthy` + `protocol.spthy` + `interface.spthy` (+ `lemmas.spthy` for secure_email) + one
> self-contained file per profile. Every *selectable* rule (a stressor, a mask behaviour, an opt-in
> outcome row, an interface/knob variant, a kdf "phase") is wrapped in `#ifdef FLAG`; a profile
> `#define`s exactly what it arms, then `#include "base.spthy"`. The preprocessed theory per profile
> is byte-identical to the old selective-include theory, so all 17 profiles prove identically.
> **The file paths in §2/§5/§8 below have changed — see the ceremony READMEs for the current tree;**
> the rule snippets themselves are unchanged (only their containing file moved). The design record is
> `MEMORY.md` lesson 18.
>
> **V3 (2026-07-10): BOTH ceremonies now use one layered template.** `alex_blake_kdf` was migrated
> off the old `ceremony.base` + `msg3_*` + `bundles/*_phase` spine onto the same five-layer shape as
> `secure_email`: `protocol.spthy` (🔵 crypto + wire + finish) → `interface.spthy` (🟠 one rule per
> control, poses `!Prompt`/`!Displayed`) → stressor layer (🔴 detectors read `!Prompt`) →
> `core/masks.spthy` (🟢 performs the step, commits `!StepData` where needed). Triggering is a graded
> **dose-response**: the lexicon rates a step `'lo' < 'med' < 'hi'` and a lookup detector fires on a
> *band* (`!Demands(...,lvl) & !AtLeast(lvl, thr)`, order in `core/framework.spthy`). New realism:
> `SIGMA_ADDITIVE` in `core/stressors.spthy` (two `'med'` steps sum to overload; P10), the inverted-U
> facilitating zone (`'med'` arousal does not freeze; P11), and population as a threshold-shift (P9
> via the band). Profiles: alex_blake P0–P11, secure_email S0–S4 — 17 total, all ≤ 5 min.

This document describes the Tamarin model in this folder. It draws only on the
files under `tamarin_model/`.

> **Stressor layer is ceremony-agnostic.** Every detector block in `core/stressors.spthy` reads a generic
> `!Prompt(P,pid,action)` (the prompt the interface posed) plus, for the lookup detectors, a row of the
> `core/demands.spthy` usability lexicon — never a ceremony-specific task constant. This file describes
> the model with that interface; [`STRESSORS.md`](STRESSORS.md) is the detailed stressor reference and
> [`AGNOSTIC_STRESSOR_INTERFACE.md`](docs/AGNOSTIC_STRESSOR_INTERFACE.md) the design + rationale.

## 1. What the model is

The model encodes a security ceremony — a two-party key-derivation handshake —
together with a **human layer** that represents how a human under stress
deviates from the prescribed steps. Tamarin proves trace properties (lemmas)
over each combination.

The ceremony is `alex_blake_kdf`. Alex and Blake exchange two nonces and derive
a shared key `SK = kdf(N_A, N_B)`. Either party can be placed under stress. Each
**profile** is one self-contained Tamarin theory that composes the shared
ceremony spine plus the phase bundles / stressors it exercises, then states the
lemmas it proves.

Three concepts carry the human model:

- **Mask** — the mode a human operates in (`Attentive`, `Busy`, `Careless`,
  `Habituated`, `Naive`, `Fearful`). `Attentive` follows the protocol; the
  others degrade it.
- **Stressor** — a condition that shifts the human from `Attentive` to a
  degraded mask (`HighCognitiveLoad`, `ExternalDistraction`, `TimePressure`,
  `MisleadingTerminology`, `Abstraction`, `Habituation`, `AlertVolume`,
  `SecurityAnxiety`, `RepeatedFailure`).
- **Mitigation** — a protocol step that constrains what a degraded mask emits,
  so a degraded mask no longer produces a bad outcome.

## 2. Directory layout

```
tamarin_model/
├── core/                       # human layer, reusable across ceremonies (one file per layer)
│   ├── framework.spthy         # ALWAYS ON: kdf symbol + OneInstancePerHuman + the 'lo'<'med'<'hi'
│   │                           #   band + the persistent mask-state gates + answered-once + the
│   │                           #   (mask, action) -> outcome matrix
│   ├── masks.spthy             # f_H behaviours + opt-in outcome rows   (#ifdef MASK_* / OUTCOME_*)
│   ├── stressors.spthy         # the 10 sigma detectors                  (#ifdef SIGMA*)
│   ├── demands.spthy           # demand profiles: lexicon / population / interface (#ifdef LEXICON_DEFAULT/…)
│   ├── knobs.spthy             # adversary + mitigations                 (#ifdef ADVERSARY / MITIGATIONS)
│   └── properties.spthy        # ceremony-agnostic property library      (#ifdef PROPERTIES)
└── ceremonies/
    ├── secure_email/
    │   ├── S0_baseline.spthy … S4_worstcase.spthy   # profiles: #define flags + #include base + lemmas
    │   ├── base.spthy          # ceremony-constant #defines + the layer #includes
    │   ├── protocol.spthy      🔵  interface.spthy 🟠  lemmas.spthy ([reuse] trio)  README.md
    └── alex_blake_kdf/
        ├── P0_baseline.spthy … P11_inverted_u.spthy # profiles (P4/P5 are custom, no base)
        ├── base.spthy          # wire-profile #defines + the layer #includes
        ├── protocol.spthy 🔵    interface.spthy 🟠    README.md
```

Two file roles separate cleanly. A **profile theory** (`P<N>_<name>.spthy` / `S<N>_<name>.spthy`)
holds `theory … begin`, its `#define FLAG` list, `#include "base.spthy"`, its lemmas, and `end`. A
**layer file** (everything under `core/`, and each ceremony's `base`/`protocol`/`interface`/`lemmas`)
holds `#ifdef`-guarded rules / restrictions / lemmas with no `theory` wrapper, reusable by `#include`.
A profile's `#define` list IS its manifest: it names exactly the stressors, phases and knobs it arms.

## 3. The three layers

### 3.1 Crypto layer

`core/framework.spthy` (the `[types]` section) declares the `kdf/2` symbol and one framework restriction:

```
functions: kdf/2     // kdf(a,b)=kdf(a',b') iff a=a' & b=b'

restriction OneInstancePerHuman:
  "All p #i #j. Start(p)@i & Start(p)@j ==> #i = #j"
```

`OneInstancePerHuman` bounds each identity to one instance per trace. Without
it, `Init` fires repeatedly and spawns concurrent sessions.

### 3.2 Protocol + interface layers

Each ceremony is split into two author-facing files under `ceremonies/<name>/`:

- **`protocol.spthy`** (🔵) — crypto, wire, finish, and (in kdf) the `UI_*` post-KDF producers.
  Selectable blocks are `#ifdef`-gated (`KDF_INIT`, `KDF_WIRE`, `FINISH_PLAIN`/`FINISH_CONFIRMED`,
  `UI_VERIFY`, `INFER_HARNESS`, …).
- **`interface.spthy`** (🟠) — one rule per mock control; each **poses** `!Prompt(P,pid,action)` and,
  when the step has observables, `!Displayed(P,pid,shown)`. Advance rules and effect adapters in the
  same file **consume** the mask's committed `!StepData` or outcome facts.

The kdf wire is the canonical example. After init and nonce exchange:

```
Msg1  Alex -> Blake : N_A     (P_send_na / P_recv_na_send_nb)
Msg2  Blake -> Alex : N_B     (P_recv_nb leaves AlexHasNonces)
```

Key derivation is no longer inline. The **interface** prompts each party to compute:

```
rule IF_calc_alex:
    [ AlexHasNonces(idA, <Na, Nb>), Fr(~rid) ]
  --[ UIStep('Alex', 'calc_sk') ]->
    [ !Prompt('Alex', ~rid, 'compute'),
      !Displayed('Alex', ~rid, kdf(Na, Nb)),
      !UnderDeadline(~rid),
      AlexAwaitKey(idA, ~rid) ]
```

The mask (`core/masks.spthy`, `MASK_COMPUTE`) reads `!Prompt`+`!Displayed`, performs the step, and
emits `Respond(P,rid,value)`; `COMPUTE_KEYRESULT` wraps that as `KeyResult`. Both Alex and Blake can
be prompted (`IF_CALC_ALEX` / `IF_CALC_BLAKE`), so both are mask-capable when a profile arms the flags.

Finish variants are profile-selected:

| Flag | Behaviour |
|---|---|
| `FINISH_PLAIN` | Alex finishes on whatever key `KeyResult` holds (unsafe-success possible) |
| `FINISH_CONFIRMED` | shutdown compares `KeyResult` against the interface's `!Displayed` correct key |

Post-KDF controls (`UI_APPROVE`, `UI_VERIFY`, `UI_AUTHORIZE`, `UI_POLICY`, `UI_WARNING`) live in
`protocol.spthy` and follow the same prompt/perform contract: they pose `!Prompt`+`!Displayed`; the
mask performs and commits; advance rules consume the outcome.

### 3.3 Human layer (`core/`)

The human layer lives in six consolidated files. Three rule kinds matter:

**f_U — the stressor (`core/stressors.spthy`).** A detector reads the interface's `!Prompt` and
emits `SetMask(P, <mask>)` at onset. It names no ceremony task. σ₁ (HighCognitiveLoad) is the lookup
shape:

```
rule Trigger_HighCognitiveLoad:
    [ !Prompt(P, sid, action),
      !Demands(action, 'MentalDemand', lvl), !AtLeast(lvl, 'hi'),
      !StressEnable(P) ]
  --[ Load(P), SetMask(P,'Busy') ]->
    [ ]

restriction OneStressPerParty:
  "All p #i #j. Load(p)@i & Load(p)@j ==> #i = #j"
```

Detectors read persistent facts (`!Prompt`, `!Demands` — no consume-and-reproduce, so no sources
loop). The lexicon row in `core/demands.spthy` makes it fire on any `compute` prompt whose rated
level crosses the threshold band. `OneStressPerParty` caps it to one onset per party. Four detector
shapes: lookup (`!Prompt` + `!Demands` band: σ₁/σ₃/σ₆/anxiety), density (count `k` distinct
`!Prompt` of one action: σ₈/σ₉), action-generic (two distinct `!Prompt`: σ₂), and chaining (reads
`!Failed`, not a prompt: σ₁₀). See [`STRESSORS.md`](STRESSORS.md).

**f_H — the mask (`core/masks.spthy`).** A mask **performs** the prompted step. It reads
`!Prompt`+`!Displayed`, consults the outcome matrix in `core/framework.spthy`, and emits action facts
plus — where a downstream rule needs the value — committed `!StepData`. The Busy compute slip mints a
fresh wrong key:

```
rule Compute_slip:
    [ !Prompt(P, rid, 'compute'), !Displayed(P, rid, correct), Fr(~wrong) ]
  --[ Calc(P,'Busy'), RespMask(P,'Busy'), Slip(P), Answered(rid),
      Key(P, ~wrong), !StepData(P, rid, ~wrong), Respond(P, rid, ~wrong) ]->
    [ !Failed(P) ]
```

`~wrong` is fresh, so it can never equal `kdf(_,_)`. Habituated confirm auto-approves any posed prompt:

```
rule Confirm_habituated:
    [ !Prompt(P, pid, 'confirm'), !Displayed(P, pid, <claimed, own>) ]
  --[ Approve(P, pid, 'Habituated'), RespMask(P,'Habituated'),
      AutoApprove(P, pid), Answered(pid) ]->
    [ !Approved(P, pid, 'Habituated') ]
```

**f_M — the transition (`core/framework.spthy`, mask-state section).** The persistent current-mask
model is described in §4.

## 4. The persistent current-mask model

The mask-state section of `core/framework.spthy` decides which mask a response is allowed to
use. The mask is not stored in a fact; it is read from the ordering of
`SetMask` events on the trace:

- each stressor emits `SetMask(p, <its mask>)` at onset;
- a recovery (the UI warning) emits `SetMask(p, 'Attentive')`;
- every f_H emits `RespMask(p, <the mask it responds as>)`.

A degrade `m` is **active** when some `SetMask(p,m)` has no later
`SetMask(p,'Attentive')`. Three restrictions enforce the reading:

```
restriction OneSetMaskPerMask:
  "All p m #i #j. SetMask(p,m)@i & SetMask(p,m)@j ==> #i = #j"

restriction RespondDegradedRequiresActive:
  "All p m #i. RespMask(p,m)@i & not(m = 'Attentive') ==>
     (Ex #s. SetMask(p,m)@s & #s < #i
             & not (Ex #r. SetMask(p,'Attentive')@r & #s < #r & #r < #i))"

restriction AttentiveRequiresNoActiveDegrade:
  "All p #i. RespMask(p,'Attentive')@i ==>
     not (Ex m #s. SetMask(p,m)@s & not(m = 'Attentive') & #s < #i
                   & not (Ex #r. SetMask(p,'Attentive')@r & #s < #r & #r < #i))"
```

Consequence: a degraded mask persists across action types (CALC_SK →
APPROVE_REQ → …) until a recovery. A user driven Busy on the KDF stays degraded
at the approval prompt. The model uses "active until recovery" rather than
strict latest-wins; that reading forbids a spurious degrade→Attentive revert and
keeps proofs terminating.

The answered-once restriction (also in `core/framework.spthy`) keeps one prompt answered at most
once, so a single `!Prompt` cannot be answered by two masks:

```
restriction AnsweredOnce:
  "All x #i #j. Answered(x)@i & Answered(x)@j ==> #i = #j"
```

### State-machine view

```
                  SetMask(p,'Busy')         SetMask(p,'Attentive')
   ┌───────────┐  / SetMask(p,'Habituated') ┌─────────────┐  (UI warning)
   │ Attentive │ ───────────────────────────│  degraded   │
   │           │                            │ Busy /      │
   │ follows   │ ◀──────────────────────────│ Careless /  │
   │ protocol  │   recovery: SetMask(        │ Habituated /│
   └───────────┘     p,'Attentive')         │ Naive / …   │
                                            └─────────────┘
                                          persists across CALC_SK,
                                          APPROVE_REQ, VERIFY_KEY, …
```

## 5. How a profile is assembled

Each profile theory reads as a manifest: a `#define` list of exactly what it arms, then
`#include "base.spthy"` (which pulls every layer), then its lemmas. `P1_calc_pressure`
(multi-party — it arms Blake's compute + stress):

```
theory ToyCeremony_P1_CalcPressure
begin

#define FINISH_PLAIN          // plain finish + session
#define LEXICON_DEFAULT       // the novice demand lexicon
#define IF_CALC_BLAKE         // Blake computes too
#define IF_NONCE_ACK          // second prompt -> sigma2 concurrency
#define STRESS_BLAKE          // enable Blake as a stress target
#define SIGMA1_LOAD           // sigma1
#define SIGMA3_DEADLINE       // sigma3
#define SIGMA2_CONCURRENCY    // sigma2

#include "base.spthy"         // KDF_INIT + KDF_WIRE + compute pipeline + Alex targeting + all layers

// … P1's lemmas …

end
```

`base.spthy` `#define`s the wire-profile constants (`KDF_INIT`, `KDF_WIRE`, `COMPUTE_KEYRESULT`,
`MASK_COMPUTE`, `IF_CALC_ALEX`, `STRESS_ALEX`) and `#include`s `core/framework` → `protocol.spthy` →
`interface.spthy` → `core/{demands,masks,stressors,knobs,properties}`. Because a profile's `#define`s
precede the `#include`, every `#ifdef` block it named is in scope when the layer files are pulled in.
A profile must be **closed**: every fact on a rule's left side has a producer, or Tamarin rejects it.
(P4 and P5 are self-contained — they `#include` the merged layer files directly instead of `base`,
because they replace the wire with the inference harness / policy-only assembly.)

### Data-flow for a Busy slip (P1)

```
IF_calc_alex (interface)                Trigger_HighCognitiveLoad (stressors)
   poses !Prompt(...,'compute')          reads !Prompt + !Demands band ('hi')
   + !Displayed(..., kdf(Na,Nb))  ───▶   + !StressEnable → SetMask('Alex','Busy')
        │                                          │
        │ !Prompt / !Displayed persist             │ Busy now active
        ▼                                          ▼
Compute_slip (masks)  reads !Prompt+!Displayed, emits Respond(~wrong) ── gated by
   → KeyResult('Alex', ~wrong)                         framework mask-state
        │
        ▼
P_finish_alex   consumes KeyResult, emits Finish('Alex')
        │
        ▼  Blake holds kdf(Na,Nb); Alex holds ~wrong  →  keys disagree, ceremony completes
   UNSAFE-SUCCESS   (and symmetrically when Blake is the stressed party)
```

The slip is driven by the interface's `!Prompt` (what the detectors read), while the mask performs
against `!Displayed` (the observables) and commits the wrong key in `!StepData`/`Respond`.

## 6. Lemmas

Each profile states lemmas of two kinds. An `exists-trace` lemma shows a
behaviour is reachable; an `all-traces` lemma shows a property holds on every
trace. From `P1_calc_pressure`:

```
// reachability: a Busy slip is reachable                        (exists-trace)
lemma P1_slip_reachable:
  exists-trace "Ex p #o. Slip(p)@o"

// reachability: the ceremony completes with disagreeing keys    (unsafe-success)
lemma P1_either_party_disagreement:
  exists-trace
  "Ex ka kb #i #j #f. Key('Alex',ka)@i & Key('Blake',kb)@j & Finish('Alex')@f
                      & not(ka = kb)"

// invariant: a stressor onset happens only for an ENABLED party (all-traces)
lemma P1_load_requires_enable:
  all-traces
  "All p #l. Load(p)@l ==> (Ex #s. StressOn(p)@s & #s < #l)"

// invariant: a Busy CALC_SK never produces a correct kdf key    (all-traces)
lemma P1_busy_no_correct_key:
  all-traces
  "All p k #i. (Calc(p,'Busy')@i & Key(p,k)@i) ==> not(Ex a b. k = kdf(a,b))"
```

## 7. The profiles

The original single-construct experiments were consolidated into 12 alex_blake_kdf profiles
(P0–P11) and 5 secure_email profiles (S0–S4); each mask-mediated profile exercises ≥3 stressors.

> Before the agnostic migration the profiles split into a *declared* tier (the stressor read a
> designer flag like `'Hard'`) and an *inferred* tier (a detector read the objective operation). That
> axis is **gone**: every detector now reads the interface's `!Prompt`, and the "is this step hard?"
> judgment lives in the lexicon for all of them. What still differs between the profiles is which
> **producer** poses the prompts and which phases/parties are exercised.

**Real-protocol profiles (P1, P2, P3).** The steps are emitted by the real ceremony phases (Msg3
request, approval/verify/authorize UIs). Outcomes:

| Outcome | Meaning | Example |
|---|---|---|
| unsafe-success | ceremony completes with a wrong/unauthorized result | P1 Busy slip, P2 Habituated auto-approve / Naive accept |
| safe-fail | ceremony stalls or the user refuses | P1 Careless timeout, P2 Fearful abort |

`P1_calc_pressure` puts σ₁/σ₃/σ₂ on the CALC phase of **both** parties; `P2`
runs the post-KDF phases (σ₈/σ₆/anxiety) plus the recovery warning; `P3` is the
maximal worst case — all phases/masks/stressors on both parties.

**Analyzer-direction profile (P4).** Instead of the real protocol phases, the `INFER_HARNESS` block
in `protocol.spthy` poses bounded `!Prompt`+`!Displayed` steps — `compute`, `compare`, `decide` —
and the **same agnostic detectors** fire. The harness seeds a fixed number of operation + decision
tokens so the density detectors (σ₉) terminate. σ₁₀ `RepeatedFailure` is the chaining edge — it reads
the `!Failed` outcome a σ₁ slip leaves (not a prompt), so a slip can escalate to Careless.

**Pathway B (P5).** A task-mediated mistake with no mask change. An Attentive
user sets a safe policy under clear terminology, and an unsafe policy under
misleading terminology (the AWS S3 "Any Authenticated Users" case). The design
quality is an **interface-level seed** (`core/demands.spthy`, `#ifdef IF_CLEAR` /
`IF_MISLEADING` → a `!ControlDesign` row the behaviour reads, like the detectors read `!Demands`),
not a per-step flag: P5 `#define`s both (quantifies over both designs); P7 `#define`s only `IF_CLEAR`
and proves
the unsafe policy *unreachable* — the Pathway-B RFC pair. The defining lemma:

```
lemma P5_mistake_is_task_mediated_not_mask:
  all-traces
  "All p pid #i. Mistake(p,pid)@i ==> ( RespMask(p,'Attentive')@i & not (Ex m #s. SetMask(p,m)@s) )"
```

**Mitigations (P6).** A mitigation constrains a degraded mask so the bad outcome
becomes unreachable while the mask shift still arises. P6 carries all three in
one ceremony.

- `shutout` (Poka-Yoke "Control") — `core/knobs.spthy` (`#ifdef MITIGATIONS`). The protocol marks
  a protected item, and a restriction forbids the bad outcome on it:

  ```
  restriction ShutoutBlocksAutoApprove:
    "All p pid #i. AutoApprove(p,pid)@i ==> not (Ex #j. Shutout(pid)@j)"

  restriction VerifyShutout:
    "All p vid #i. Accept(p,vid)@i ==> not (Ex #j. Tampered(vid)@j)"
  ```

  In P6, `shutout` blocks auto-approve via number-matching MFA and verify-shutout
  makes the fingerprint compare automatic.

- `shutdown` (Poka-Yoke "Detection") — `#ifdef FINISH_CONFIRMED` in `protocol.spthy`.
  A key-confirmation step detects the wrong key (against the interface's `!Displayed` correct value) and halts:

  ```
  rule P_confirm_ok:
      [ AlexAwaitKey(idA, rid), KeyResult('Alex', rid, sk), !Displayed('Alex', rid, correct) ]
    --[ KeyEq(sk, correct), KeyConfirmed('Alex'), Finish('Alex') ]-> [ AlexDone(idA, sk), Out('ACK') ]

  rule P_confirm_abort:
      [ AlexAwaitKey(idA, rid), KeyResult('Alex', rid, sk), !Displayed('Alex', rid, correct) ]
    --[ KeyNeq(sk, correct), ShutdownAbort('Alex') ]-> [ ]
  ```

  In P6 this turns the Busy slip's unsafe-success into a safe-fail. Its fix lemma:

  ```
  lemma P6_no_slip_completion:
    all-traces
    "not (Ex #s #f. Slip('Alex')@s & Finish('Alex')@f)"
  ```

## 8. Running the model

From the repo root (`stronger_usability_masks/`):

```bash
export PATH="$HOME/.local/bin:$PATH"
S=.claude/skills/model-tamarin
D=tamarin_model/ceremonies/alex_blake_kdf

# one profile
python3 $S/check.py --prove $D/P1_calc_pressure.spthy

# interactive GUI
tamarin-prover interactive $D/ --interface=127.0.0.1 --port=3001
```

The model has 17 profiles (alex_blake_kdf P0–P11, secure_email S0–S4); all lemmas verify
under Tamarin 1.12 / Maude 3.5.1. The 12 kdf profiles sweep in ≈30 s (slowest: P2 ≈ 6 s);
secure_email S0–S4 in ≈8 min (slowest: S4 ≈ 3 min, the 7-detector worst case).

### Phases as flags

A kdf "phase" (a post-KDF control) is a producer + its mask behaviour, now named by two flags a
profile `#define`s together, e.g. VERIFY = `UI_VERIFY` (the producer, `#ifdef`-guarded in
`protocol.spthy`) + `MASK_COMPARE` + `MASK_COMPARE_KEYCHECKED` (the behaviour, guarded in
`core/masks.spthy`). Arming a stressor is one more `#define` (`SIGMA6_ABSTRACTION`). The demand
profile is one flag too (`LEXICON_DEFAULT`, or `POP_EXPERT` / `IF_HARDENED` / an inline seed).
`P3` `#define`s the full set for the worst-case scope; each `#ifdef` compiles in exactly its block.

### Per-participant stress targeting

Every rule in `core/stressors.spthy` reads `!StressEnable(P)`, so a stressor fires only for
an enabled party:

```
rule Trigger_HighCognitiveLoad:
    [ !Prompt(P, sid, action), !Demands(action, 'MentalDemand', lvl),
      !AtLeast(lvl, 'hi'), !StressEnable(P) ]
  --[ Load(P), SetMask(P,'Busy') ]->
    [ ]
```

The `KDF_INIT` block in `protocol.spthy` deposits a persistent `!Party(p,id)`; the `STRESS_ALEX`
and `STRESS_BLAKE` blocks each read it to seed `!StressEnable` for one party. `base.spthy` arms
`STRESS_ALEX` by default; a profile adds `#define STRESS_BLAKE` for whoever else it stresses. An
un-enabled party stays Attentive even when its step is present — `P1_calc_pressure` enables both
parties and proves a stressor onset implies a prior enable (`P1_load_requires_enable`).

## 9. Termination decisions

Several restrictions exist to keep the all-traces search terminating:

- `OneStressPerParty` / `OnceHabituate` / `OneAlertVolume` / … — one onset per
  stressor per party. A detector reads a persistent fact and re-fires without this bound.
- `OneSetMaskPerMask` — one `SetMask` per mask per party, so the interval
  reasoning in `core/framework.spthy` (mask-state section) stays finite.
- `OnceStressAlex` / `OnceStressBlake` — one `StressOn` per party, so the
  persistent `!StressEnable` is seeded a bounded number of times.
- the `INFER_HARNESS` block in `protocol.spthy` seeds a fixed number of operation + decision tokens
  (P4), so the step posers are bounded and the density detectors terminate.
- `Inequality` (the `Neq(x,x) ==> F` distinctness restriction) guards the σ₉ density detector, and
  σ₈ uses its own `InequalityHabituation` — so the two can be composed in one theory (both fire in
  S4) without a duplicate-restriction-name clash.

These bounds are recorded as semantic no-ops (re-entering a mask you already hold
changes nothing) or as the documented tractability choice for worst-case
analysis.
