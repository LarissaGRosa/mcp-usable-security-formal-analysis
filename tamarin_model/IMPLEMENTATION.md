# `tamarin_model` — what is implemented and how

> **V3 (2026-07-10): BOTH ceremonies now use one layered template.** `alex_blake_kdf` was migrated
> off the old `ceremony.base` + `msg3_*` + `bundles/*_phase` spine onto the same five-layer shape as
> `secure_email`: `protocol/` (🔵 crypto + wire + finish) → `interface/` (🟠 one rule per control,
> emits `!Step`/`!StepData`) → stressor layer (🔴 detectors read the interface) → `masks/` (🟢
> behaviours) → `bundles/human_common.spthy`. Triggering is now a graded **dose-response**: the
> lexicon rates a step `'lo' < 'med' < 'hi'` and a detector fires on a *band* (`!AtLeast(lvl, thr)`
> in `core/types.spthy`), not an exact `'hi'`. New realism: `core/stressors/additive_load.spthy`
> (two `'med'` steps sum to overload; P10), the inverted-U facilitating zone (`'med'` arousal does
> not freeze; P11), and population as a threshold-shift (P9 via the band). Profiles: alex_blake
> P0–P11, secure_email S0–S4 — 17 total, all ≤ 5 min.
>
> **Sections §2, §3.2, §5, §7, §8 below describe the PRE-V3 alex_blake spine (`ceremony.base`,
> `msg3_inline`/`msg3_request*`, `blake_calc*`, the phase bundles) and the v1 detectors
> (`external_distraction`, `time_pressure`) — all DELETED in V3.** For the current architecture see
> [`AUTHORING_GUIDE.md`](AUTHORING_GUIDE.md) (the start-here template) and
> [`docs/V3_UNIFY_REALISM_PLAN.md`](docs/V3_UNIFY_REALISM_PLAN.md) (the migration record). The human
> layer (`core/masks`, `core/transitions`, the outcome matrix, the mask-state model) is UNCHANGED
> and is still described correctly below.

This document describes the Tamarin model in this folder. It draws only on the
files under `tamarin_model/`.

> **Stressor layer is ceremony-agnostic.** Every `core/stressors/*` detector reads a generic
> `!Step(P,sid,action)` (the ceremony's objective interaction step) plus, for the lookup detectors, a row
> of the `core/lexicon_tlx.spthy` usability lexicon — never a ceremony-specific task constant. This file
> describes the model with that interface; [`STRESSORS.md`](STRESSORS.md) is the detailed stressor
> reference and [`AGNOSTIC_STRESSOR_INTERFACE.md`](docs/AGNOSTIC_STRESSOR_INTERFACE.md) the design + rationale.

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
├── core/                              # human layer, reusable across ceremonies
│   ├── types.spthy                    # kdf symbol + OneInstancePerHuman
│   ├── mitigations.spthy              # shutout / verify-shutout restrictions
│   ├── masks/                         # f_H: how a mask answers an action
│   │   ├── attentive_calc.spthy
│   │   ├── busy_calc.spthy
│   │   ├── habituated_approve.spthy
│   │   └── … (one file per mask × action)
│   ├── lexicon_tlx.spthy              # Layer 2: action → NASA-TLX dimension + level (the cited verdict)
│   ├── stressors/                     # f_U: what triggers a mask shift (agnostic — reads !Step)
│   │   ├── cognitive_load.spthy           # σ1: !Step + !Demands(_,'MentalDemand','hi')
│   │   ├── time_pressure.spthy            # σ3: !Step + !Demands(_,'TemporalDemand','hi')
│   │   └── …
│   └── transitions/
│       ├── mask_state.spthy           # persistent current-mask rules
│       └── answered_once.spthy        # one answer per request
└── ceremonies/alex_blake_kdf/
    ├── ceremony.base.spthy            # shared spine (#include-d)
    ├── protocol/                      # protocol-layer fragments
    │   ├── init.spthy                 # participant init
    │   ├── messages.spthy             # Msg1 / Msg2
    │   ├── msg3_*.spthy               # Msg3 variants
    │   ├── approval_ui.spthy          # APPROVE_REQ phase
    │   ├── warning_ui.spthy           # recovery warning
    │   └── …
    ├── bundles/                       # phase bundles (Stage C): one include per phase
    │   ├── human_common.spthy         #   gates + answer discipline + Alex enable
    │   ├── calc_phase.spthy           #   CALC_SK producer + masks + stressors
    │   ├── approve_phase.spthy
    │   ├── verify_phase.spthy
    │   └── authorize_phase.spthy
    ├── experiments/P<N>_<name>.spthy  # lemmas only, one file per profile
    ├── P<N>_<name>.spthy              # profile entry-point theory (what you run)
    └── README.md
```

Two file roles separate cleanly. An **entry-point theory** (`P<N>_<name>.spthy`)
holds `theory … begin … end` and `#include`s its parts. A **fragment** (every
file under `core/` and `protocol/`, and `ceremony.base.spthy`) holds rules /
restrictions / lemmas with no `theory` wrapper, so it is reusable by `#include`.

## 3. The three layers

### 3.1 Crypto layer

`core/types.spthy` declares the `kdf/2` symbol and one framework restriction:

```
functions: kdf/2     // kdf(a,b)=kdf(a',b') iff a=a' & b=b'

restriction OneInstancePerHuman:
  "All p #i #j. Start(p)@i & Start(p)@j ==> #i = #j"
```

`OneInstancePerHuman` bounds each identity to one instance per trace. Without
it, `Init` fires repeatedly and spawns concurrent sessions.

### 3.2 Protocol layer

`protocol/init.spthy` and `protocol/messages.spthy` are shared by every
experiment. They cover participant init and Msg1/Msg2:

```
Msg1  A->B : N_A           (GEN_NONCE)
Msg2  B->A : N_B           (GEN_NONCE; then Blake's CALC_SK)
```

Blake no longer computes the key inline. `B_recv_Na_send_Nb` sends `N_B` and leaves
`BlakeWait(idB,<Na,Nb>)`; Blake's CALC_SK is answered by a separate fragment, so Blake
is subject to the mask machinery as well. The default `protocol/blake_calc.spthy`
(pulled in by `ceremony.base.spthy`) answers Attentive and posts no `!Req`, so Blake
stays inert to the stressors and every existing profile is unchanged.
`protocol/blake_calc_stressable.spthy` instead posts a `'Hard'` `!Req('Blake',…)` for the masks
**and** a `!Step('Blake',_,'compute')` for the agnostic detectors, so the shared human layer can
degrade Blake (profiles P1 / P3).

Msg3 — Alex's step — varies per profile. The variants:

| Variant | File | Shape |
|---|---|---|
| inline | `msg3_inline.spthy` | Alex computes `SK` directly |
| request/ack | `msg3_request.spthy` | Alex issues a `!Req(...,'CALC_SK','Hard')` (for the masks) + `!Step(_,_,'compute')` (for the detectors), a mask answers, Alex ACKs |
| request/confirm | `msg3_request_confirmed.spthy` | as request/ack, plus a key-confirmation that aborts on mismatch (the `shutdown` mitigation) |

In the request/ack variant Alex does not compute the key; he posts a request and
consumes whatever key results. Which mask answers is decided by the profile's
stressor and transition. The producer emits **two** facts — the `!Req` the masks read for the
key's *content*, and the agnostic `!Step` the detectors read:

```
rule A_recv_Nb_request:
    [ AlexWait(idA,Na), In(Nb), Fr(~rid) ]
  --[ Request('Alex', ~rid, 'CALC_SK', 'Hard') ]->
    [ AlexAwaitKey(idA, ~rid),
      !Req('Alex', ~rid, 'CALC_SK', <Na,Nb>, 'Hard'),   // masks (f_H) read this
      !Step('Alex', ~rid, 'compute') ]                  // detectors (f_U) read this
```

Additional protocol phases extend the ceremony past key derivation:
`approval_ui.spthy` (APPROVE_REQ — MFA-style prompts), `verify_ui.spthy`
(VERIFY_KEY — fingerprint check), `authorize_ui.spthy` (AUTHORIZE),
`policy_ui.spthy` (SET_POLICY), `warning_ui.spthy` (recovery warning).

### 3.3 Human layer (`core/`)

The human layer has three rule kinds.

**f_U — the stressor (`core/stressors/`).** A stressor reads the agnostic `!Step` interface and
emits `SetMask(P, <mask>)` at onset. It names no ceremony task. `cognitive_load.spthy` (σ₁) reads a
step plus the lexicon's verdict that the step is mentally demanding:

```
rule Trigger_HighCognitiveLoad:
    [ !Step(P, sid, action),
      !Demands(action, 'MentalDemand', 'hi'),   // from core/lexicon_tlx.spthy
      !StressEnable(P) ]
  --[ Load(P), SetMask(P,'Busy') ]->
    [ ]

restriction OneStressPerParty:
  "All p #i #j. Load(p)@i & Load(p)@j ==> #i = #j"
```

It reads persistent facts (`!Step`, `!Demands` — no consume-and-reproduce, so no sources loop). The
lexicon row `!Demands('compute','MentalDemand','hi')` makes it fire on any `compute` step, so the
HCI judgment "a key derivation is hard" lives once in the lexicon, not in the rule. `OneStressPerParty`
caps it to one onset per party. The detectors come in four shapes — lookup (`!Step` + a `!Demands`
row: σ₁/σ₃/σ₆/SecurityAnxiety), density (count `k` distinct `!Step` of one action: σ₈/σ₉),
action-generic (any `!Step`: σ₂), and chaining (reads the `!Failed` outcome, not a step: σ₁₀). See
[`STRESSORS.md`](STRESSORS.md) for all of them.

**f_H — the mask (`core/masks/`).** A mask answers an action as one mode. The
Busy answer to CALC_SK emits a fresh wrong key whose top symbol is not `kdf`:

```
rule Calc_Busy_slip:
    [ !Req(P, rid, 'CALC_SK', <Na,Nb>, c), Fr(~wrong) ]
  --[ Calc(P,'Busy'), RespMask(P,'Busy'), Mask(P,'Attentive','Busy'),
      Slip(P), Answered(rid), Key(P, ~wrong) ]->
    [ KeyResult(P, rid, ~wrong) ]
```

`~wrong` is fresh, so it can never equal `kdf(_,_)`. The Habituated answer to
APPROVE_REQ approves a prompt of any kind, including an adversary-injected one:

```
rule Approve_Habituated:
    [ !Prompt(P, pid, kind) ]
  --[ Approve(P, pid, 'Habituated'), RespMask(P,'Habituated'),
      AutoApprove(P, pid), Mask(P,'Attentive','Habituated'), Answered(pid) ]->
    [ !Approved(P, pid, 'Habituated') ]
```

**f_M — the transition (`core/transitions/`).** This is the persistent
current-mask model and is described in §4.

## 4. The persistent current-mask model

`core/transitions/mask_state.spthy` decides which mask a response is allowed to
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

`answered_once.spthy` keeps one request answered at most once, so a single
`!Req` / `!Prompt` cannot be answered by two masks:

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

Each profile entry-point reads as a manifest: the spine + `human_common` + the
phase bundles it exercises + its lemmas. `P1_calc_pressure` (multi-party, so it
skips `ceremony.base` to make Blake degradable):

```
theory ToyCeremony_P1_CalcPressure
begin

#include "../../core/types.spthy"                     // crypto layer
#include "protocol/init.spthy"                         // participants (+ !Party)
#include "protocol/messages.spthy"                      // Msg1/Msg2 (Blake at BlakeWait)
#include "protocol/blake_calc_stressable.spthy"         // Blake's 'Hard' CALC_SK

#include "bundles/calc_phase.spthy"                     // producer + masks + sigma1/sigma3/sigma2
#include "bundles/human_common.spthy"                   // gates + answer discipline + stress_alex
#include "protocol/stress_blake.spthy"                  // enable Blake too

#include "experiments/P1_calc_pressure.spthy"           // lemmas

end
```

A profile must be **closed**: every fact on a rule's left side has a producer, or
Tamarin rejects the theory.

### Data-flow for a Busy slip (P1)

```
A_recv_Nb_request                       Trigger_HighCognitiveLoad
   emits !Req(...,'Hard') (for masks)    reads !Step + !Demands(_,'MentalDemand','hi')
       + !Step(...,'compute')  ───────▶    + !StressEnable, emits SetMask('Alex','Busy')
        │                                          │
        │ !Req / !Step persist                     │ Busy now active
        ▼                                          ▼
Calc_Busy_slip   reads !Req, emits RespMask('Alex','Busy') ── checked by
   emits Key('Alex', ~wrong)  (top symbol ≠ kdf)              mask_state.spthy
        │
        ▼
A_send_ack   consumes KeyResult, emits Finish('Alex')
        │
        ▼  Blake holds kdf(Na,Nb); Alex holds ~wrong  →  keys disagree, ceremony completes
   UNSAFE-SUCCESS   (and symmetrically when Blake is the stressed party)
```

The slip is driven by `!Step` (the agnostic detector), while the mask reads `!Req` for the key
content — the two-fact split from §3.2.

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

The 21 original single-construct experiments were consolidated into 7 profiles
(Stage D); each mask-mediated profile exercises ≥3 stressors.

> Before the agnostic migration the profiles split into a *declared* tier (the stressor read a
> designer flag like `'Hard'`) and an *inferred* tier (a detector read the objective operation). That
> axis is **gone**: every detector now reads the objective `!Step`, and the "is this step hard?"
> judgment lives in the lexicon for all of them. What still differs between the profiles is which
> **producer** emits the steps and which phases/parties are exercised.

**Real-protocol profiles (P1, P2, P3).** The steps are emitted by the real ceremony phases (Msg3
request, approval/verify/authorize UIs). Outcomes:

| Outcome | Meaning | Example |
|---|---|---|
| unsafe-success | ceremony completes with a wrong/unauthorized result | P1 Busy slip, P2 Habituated auto-approve / Naive accept |
| safe-fail | ceremony stalls or the user refuses | P1 Careless timeout, P2 Fearful abort |

`P1_calc_pressure` puts σ₁/σ₃/σ₂ on the CALC phase of **both** parties; `P2`
runs the post-KDF phases (σ₈/σ₆/anxiety) plus the recovery warning; `P3` is the
maximal worst case — all phases/masks/stressors on both parties.

**Analyzer-direction profile (P4).** Instead of the real protocol phases, a single token-bounded
harness (`protocol/infer_harness.spthy`) poses the *objective* steps — `compute`, `compare`,
`decide` — and the **same agnostic detectors** fire, hosting σ₁/σ₆/σ₁₀/σ₉ in one ceremony. This is
the "analyzer direction": the ceremony states what the human objectively does, and the detectors read
it (no designer flag anywhere). The harness emits the protocol facts the masks need (`!Op`, `!Decision`)
alongside the `!Step` the detectors read, and seeds a fixed number of operation + decision tokens so
the posers are bounded and the density detectors (σ₉) terminate. σ₁₀ `RepeatedFailure` is the chaining
edge — it reads the `!Failed` outcome a σ₁ slip leaves (not a step), so a slip can escalate to Careless.

**Pathway B (P5).** A task-mediated mistake with no mask change. An Attentive
user sets a safe policy under clear terminology, and an unsafe policy under
misleading terminology (the AWS S3 "Any Authenticated Users" case). The design
quality is an **interface-level seed** (`core/interface_clear_policy.spthy` /
`core/interface_misleading_policy.spthy` → a `!ControlDesign` row the behaviour
reads, like the detectors read `!Demands`), not a per-step flag: P5 includes both
seeds (quantifies over both designs); P7 includes only the clear one and proves
the unsafe policy *unreachable* — the Pathway-B RFC pair. The defining lemma:

```
lemma P5_mistake_is_task_mediated_not_mask:
  all-traces
  "All p pid #i. Mistake(p,pid)@i ==> ( RespMask(p,'Attentive')@i & not (Ex m #s. SetMask(p,m)@s) )"
```

**Mitigations (P6).** A mitigation constrains a degraded mask so the bad outcome
becomes unreachable while the mask shift still arises. P6 carries all three in
one ceremony.

- `shutout` (Poka-Yoke "Control") — `core/mitigations.spthy`. The protocol marks
  a protected item, and a restriction forbids the bad outcome on it:

  ```
  restriction ShutoutBlocksAutoApprove:
    "All p pid #i. AutoApprove(p,pid)@i ==> not (Ex #j. Shutout(pid)@j)"

  restriction VerifyShutout:
    "All p vid #i. Accept(p,vid)@i ==> not (Ex #j. Tampered(vid)@j)"
  ```

  In P6, `shutout` blocks auto-approve via number-matching MFA and verify-shutout
  makes the fingerprint compare automatic.

- `shutdown` (Poka-Yoke "Detection") — `protocol/msg3_request_confirmed.spthy`.
  A key-confirmation step detects the wrong key and halts:

  ```
  rule A_confirm_ok:                                     // keys match -> finish
      [ AlexAwaitKey(idA, rid), KeyResult('Alex', rid, sk), !Req('Alex', rid, 'CALC_SK', <Na,Nb>, c) ]
    --[ KeyEq(sk, kdf(Na,Nb)), KeyConfirmed('Alex'), Finish('Alex') ]-> [ AlexDone(idA, sk) ]

  rule A_confirm_abort:                                  // mismatch -> halt
      [ AlexAwaitKey(idA, rid), KeyResult('Alex', rid, sk), !Req('Alex', rid, 'CALC_SK', <Na,Nb>, c) ]
    --[ KeyNeq(sk, kdf(Na,Nb)), ShutdownAbort('Alex') ]-> [ ]

  restriction KeyEqHolds:  "All x y #i. KeyEq(x,y)@i ==> x = y"
  restriction KeyNeqHolds: "All x #i. KeyNeq(x,x)@i ==> F"
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

Per the README, the model has 7 profiles and 40 lemmas; all lemmas verify
under Tamarin 1.12 / Maude 3.5.1, each profile in ≤4 s (slowest: P4 ≈ 3.8 s).

### Phase bundles

`bundles/` groups each ceremony phase into one include: its producer, every mask
that answers it, and every stressor that targets it. `bundles/calc_phase.spthy`:

```
#include "../protocol/msg3_request.spthy"            // producer: Alex's 'Hard' request + !Step('compute')
#include "../../../core/masks/attentive_calc.spthy"
#include "../../../core/masks/busy_calc.spthy"
#include "../../../core/masks/careless_calc.spthy"
#include "../../../core/lexicon_tlx.spthy"           // Layer-2 lexicon (the lookup detectors read it)
#include "../../../core/stressors/cognitive_load.spthy"     // σ1
#include "../../../core/stressors/time_pressure.spthy"      // σ3
#include "../../../core/stressors/external_distraction.spthy" // σ2
```

`bundles/human_common.spthy` carries the `mask_state` + `answered_once` gates and
the Alex stress-enable. A bundle-composed profile is `ceremony.base` +
`human_common` + the phase bundles it wants (+ `protocol/session.spthy` for any
post-KDF phase). `P3` composes all four phase bundles for the worst-case scope.
Adding a stressor to a phase is one include line in its bundle; every profile
using that phase inherits it. The lexicon is included once per theory wherever a
lookup detector is used.

### Per-participant stress targeting

Every `core/stressors` rule reads `!StressEnable(P)`, so a stressor fires only for
an enabled party:

```
rule Trigger_HighCognitiveLoad:
    [ !Step(P, sid, action), !Demands(action, 'MentalDemand', 'hi'), !StressEnable(P) ]
  --[ Load(P), SetMask(P,'Busy') ]->
    [ ]
```

`protocol/init.spthy` deposits a persistent `!Party(p,id)`; `protocol/stress_alex.spthy`
and `protocol/stress_blake.spthy` each read it to seed `!StressEnable` for one party.
A profile includes the enable for whoever it stresses. An un-enabled party stays
Attentive even when its step is present — `P1_calc_pressure` enables both parties and
proves a stressor onset implies a prior enable (`P1_load_requires_enable`).

## 9. Termination decisions

Several restrictions exist to keep the all-traces search terminating:

- `OneStressPerParty` / `OnceHabituate` / `OneAlertVolume` / … — one onset per
  stressor per party. A detector reads a persistent fact and re-fires without this bound.
- `OneSetMaskPerMask` — one `SetMask` per mask per party, so the interval
  reasoning in `mask_state.spthy` stays finite.
- `OnceStressAlex` / `OnceStressBlake` — one `StressOn` per party, so the
  persistent `!StressEnable` is seeded a bounded number of times.
- `protocol/infer_harness.spthy` seeds a fixed number of operation + decision tokens
  (P4), so the step posers are bounded and the density detectors terminate.
- `Inequality` (the `Neq(x,x) ==> F` distinctness restriction) is shared by the two
  density detectors σ₈ and σ₉ under one name, so they are never composed in one theory
  (σ₈ in P2/P6, σ₉ in P4/S1).

These bounds are recorded as semantic no-ops (re-entering a mask you already hold
changes nothing) or as the documented tractability choice for worst-case
analysis.
```
