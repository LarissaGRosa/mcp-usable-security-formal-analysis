# Plan: Extending Usability Stressors, Mask Transitions, and Masks

> **Status (2026-06-26): Phase 0 + Experiments 02–14 are built and proven** in `tamarin_model/` — 15 experiments, 66 lemmas. Includes both **failure pathways** (A: stressor→mask→degraded; **B: task-mediated `mistake`**, Exp 13 / AWS-S3), the recovery edge, a **stressor-inference** family (Exp 10–12), and the first **failure↔fix pair** — σ₈ prompt-bombing (Exp 02) neutralized by a number-matching **`shutout`** mitigation (Exp 14). See §0. The rest of this plan is the remaining roadmap.

> **Scope.** Deliverables for the Ceremony Mask framework:
> 0. **First toy ceremony + bootstrap experiment (new — start here).** A concrete `alex_blake_kdf` ceremony (§C0) plus a vertical-experiment build/test plan (§Phase 0) that proves *one stressor → one transition → one broken property* end-to-end **before** any breadth is added.
> 1. **Masks to review** — user-centered descriptions + precise behavioral signatures, reconciled with the HCI literature (Norman, Cranor).
> 2. **New stressors** — an empirically grounded catalogue (toward σ₁…σ₁₀) and *how* each is triggered (`f_U`).
> 3. **New mask transitions** — building out the `f_M` graph (reaching the unimplemented masks, chained degradation, habituation escalation, recovery).
>
> **Sources.** This iteration is grounded in the supplied research report *"Falhas de Usabilidade na Arquitetura de Segurança"* (Norman's error taxonomy; Whitten & Tygar's five properties; Cranor's Human-in-the-Loop / C-HIP; Ka-Ping Yee's 10 guidelines; Poka-Yoke; and six case studies: PGP/Mailvelope, MFA fatigue, AWS S3, clinical EHR workarounds, Shadow AI, warning habituation). The earlier draft's structure is kept; each construct below now carries its literature anchor.

---

## 0. Current state — implemented through Experiment 14 (2026-06-26)

> **What runs today.** `tamarin_model/` holds a working model in the Appendix A two-layer layout. **Fifteen entry-point theories** — `00_baseline.spthy` … `14_shutout_mitigation.spthy` — each `#include` a shared `ceremony.base.spthy` spine plus only their own deltas (from `core/` + `protocol/`). **All 66 lemmas verify** under `tamarin-prover --prove` (Tamarin 1.12 / Maude 3.5.1), each experiment in **≤2 s**. The mask is a **persistent current mask that carries across action types** — `core/transitions/mask_state.spthy`. Verify with `.claude/skills/model-tamarin/check.py --prove <entry>.spthy`; per-ceremony usage is in `ceremonies/alex_blake_kdf/README.md`.

> **Two families of experiments.** Experiments **00–09** *declare* the stressor (a `Trigger_*` wired to a named request). Experiments **10–12** are the **stressor-inference** direction (the usability-analyzer goal): the ceremony records only the **objective operation** it poses to the human (`!Op(P, rid, optag, …)`) or the **trace** of what was handled/failed, and a `core/` detector *infers* the stressor — encoding the HCI knowledge (which operations are hard/abstract; repetition; prior failure) without any designer usability flag. Two sub-techniques: **operation-inference** (Exp 10 σ₁ from `op='kdf'`, Exp 11 σ₆ from `op='verify'`) and **trace-inference** (Exp 12 σ₁₀ from a prior `!Failed`, which also gives the first **chaining** edge σ₁→σ₁₀). NB: to stay clear of Tamarin's message-derivation check, detectors key on an operation **tag**, not by destructuring the term (MEMORY.md #11).

**Built vs pending (✅ done · ⬜ pending):**

| Layer | ✅ Built | ⬜ Pending |
|---|---|---|
| Masks (`f_H`) | `Attentive`, `Busy`, `Habituated`, `Careless`, `Naive`, `Fearful` | — (**`Elder` is out of scope** — see §3: it is a persona/trait, not a stressor-induced mask) |
| Stressors (`f_U`) | σ₁ `HighCognitiveLoad`, σ₂ `ExternalDistraction`, σ₃ `TimePressure`, σ₄ `MisleadingTerminology` (**Pathway B**), σ₆ `Abstraction`, σ₈ `Habituation`, `SecurityAnxiety`, σ₁₀ `RepeatedFailure`; **σ₁/σ₆/σ₁₀ also have inference detectors** | σ₅ `LackOfFeedback`, σ₇ `SecondaryTask`, σ₉ `AlertVolume` |
| Transitions (`f_M`) | Attentive→Busy (σ₁ **&** σ₃), Attentive→Careless (σ₂), Attentive→Habituated (σ₈), Attentive→Naive (σ₆), Attentive→Fearful (SecurityAnxiety); **Habituated→Attentive recovery** (warning) | chaining (e.g. Naive→Fearful); escalation; other recovery edges |
| **Failure pathways** | **A** (stressor→mask→degraded action) ✅; **B** (task-mediated `mistake`, NO mask change — Exp 13) ✅ | — |
| Outcomes | valid (`kdf`), `slip`, `auto_approve`, `timeout`, `mistake` (both pathways), `abort`/withdrawal | `bypass` |
| Action types | `CALC_SK`, `SEND_MSG`, `GEN_NONCE`, `APPROVE_REQ`, `VERIFY_KEY`, `AUTHORIZE`, **`SET_POLICY`** | — |
| Ceremony (𝒫) | C0 `alex_blake_kdf` + `APPROVE_REQ`, `VERIFY_KEY`, `AUTHORIZE`, `SET_POLICY` UI phases + recovery warning | payload flags (§6); further ceremonies |
| Mitigations (§7) | **`shutout`** (number-matching MFA, `core/mitigations.spthy`, Exp 14) + the recovery warning (Exp 05) | `shutdown`, decaying `warning`, Yee protective flags; more failure↔fix pairs |
| Experiments | `L0_*`…`L3_*`, `LM_*`, `L5_*`…`L13_*` (14 experiments) | one file per remaining phenomenon (§9) |

**Experiments proven so far** (each is a profile `𝓔` in the §6a sense — a minimal `#include` set):

| Experiment | Stressor → mask → outcome | Failure semantics | Lemmas |
|---|---|---|---|
| **00** baseline | — (Attentive only) | baseline (Agreement + Liveness) | `L0_completes`, `L0_agreement` |
| **01** busy_under_load | σ₁ → Busy → `slip` | **unsafe-success** (wrong key, completes) | five `L1_*` |
| **02** habituated_mfa | σ₈ → Habituated → `auto_approve` | **unsafe-success** (approves an injected prompt) | five `L2_*` |
| **03** careless_distraction | σ₂ → Careless → `timeout` | **safe-fail** (ceremony stalls) | five `L3_*` |
| **04** multi_stressor | **σ₁+σ₂+σ₈ merged** → {Busy, Careless, Habituated} | **interaction**: compound failures in one run | six `LM_*` |
| **05** warning_recovery | σ₈ → Habituated, then **UI warning → Attentive** | **recovery**: mask persists, then re-engages | five `L5_*` |
| **06** abstraction_naive | σ₆ Abstraction → **Naive** → `mistake` (VERIFY_KEY) | **unsafe-success**: accepts a tampered fingerprint | four `L6_*` |
| **07** anxiety_fearful | SecurityAnxiety → **Fearful** → `abort` (AUTHORIZE) | **safe-fail**: active refusal / withdrawal | four `L7_*` |
| **08** timepressure_busy | σ₃ TimePressure → **Busy** → `slip` | **unsafe-success**: 2nd route into Busy | four `L8_*` |
| **09** all_stressors | **all 6 stressors / 6 masks / 4 phases + recovery** | **maximal**: every failure reachable; safety composes | seven `L9_*` |
| **10** inferred_load | σ₁ **inferred** from `op='kdf'` → Busy → slip | inference (operation); sound: load only from a posed kdf | four `L10_*` |
| **11** inferred_abstraction | σ₆ **inferred** from `op='verify'` → Naive → mistake | inference (operation); accepts a tampered fingerprint | four `L11_*` |
| **12** inferred_repeated_failure | σ₁₀ **inferred** from a prior `!Failed` → Careless | inference (trace) + **chaining** σ₁→σ₁₀ | three `L12_*` |
| **13** pathwayb_s3 | σ₄ MisleadingTerminology → **Attentive `mistake`** (SET_POLICY) | **Pathway B**: task-mediated, no mask change (AWS-S3) | four `L13_*` |
| **14** shutout_mitigation | σ₈ habituation, but injected prompt is **number-matching `shutout`** | **fix verified**: user still habituates, breach neutralized (pairs with Exp 02) | three `L14_*` |

**Key as-built deviations from the original plan text** (the prose below predates the build; trust the code where they differ):

1. **Derived-mask, not stored `St_H`.** The mask is never a stored state fact; `f_H` derives it from the active `!Stressor` at response time and emits `Mask(...)` only as an *action* fact (machinery §6.2 / §6a-rule-1). The Experiment-00/1 fragments below still show the older `St_H`/`MaskShift` style and are kept as exposition only.
2. **Mask `f_H` files are action-scoped**, e.g. `attentive_calc.spthy`, `attentive_approve.spthy` — *not* one-file-per-mask as Appendix A originally drew. Forced by Tamarin: a rule whose LHS fact is never produced is a **hard wellformedness failure**, so an experiment may include only files it can *close*. See the revised Appendix A.
3. **One entry-point theory per experiment** (`00_baseline.spthy` … `03_careless_distraction.spthy`), not a single `ceremony.spthy`, because the experiments differ in their msg-3 protocol rules (inline vs request/ack vs approval UI). Each = a shared `ceremony.base.spthy` spine + that experiment's deltas; protocol fragments live under `protocol/`.
4. **`OneInstancePerHuman`** restriction (in `core/types.spthy`) pins each human to a single instance per trace.
5. **Three distinct failure semantics** are now demonstrated, sharpening §2's safe-fail/unsafe-success distinction into a proven trichotomy (see the experiment table).
6. **Persistent cross-action mask (new).** The mask is *not* re-derived per action: a `SetMask(p,m)` event is emitted at each stressor's onset (and `SetMask(p,'Attentive')` by the recovery warning), and the current-mask gates in `core/transitions/mask_state.spthy` make every f_H respond as the current mask, which persists across CALC_SK → APPROVE_REQ until a recovery. So a Busy/Careless user also degrades at the approval step (Busy → `auto_approve`, Careless → `timeout`; new `busy_approve.spthy`/`careless_approve.spthy`). Proven by `LM_mask_persists_across_actions` (no Attentive approval can follow a slip). Encoded as **"degrade active until recovery"** rather than strict latest-mask-wins — the cheaper choice that keeps the all-traces proofs ≤2 s (strict latest-wins blows up once three stressors interleave). The per-edge `from_attentive*.spthy` and `recovery.spthy` files are gone (the f_M edge is now the trigger's `SetMask` + the shared gates).

---

## C0. The Toy Ceremony — Alex–Blake mutual-nonce KDF (first concrete ceremony)

The framework so far is abstract: the formalization defines the machinery $\langle \mathcal{P}, \mathcal{H}, \mathcal{U}, \mathcal{N} \rangle$ generically, and the extension menu (§1–§9) is broad. Before building any of it we pin down **one** concrete ceremony to host the machinery and to be the substrate for every experiment. This is the `alex_blake_kdf` ceremony of Appendix A.

**Provenance.** A mutual nonce exchange adapted from the Tamarin *toy protocol* (`benjaminkiesl/tamarin_toy_protocol`), but re-read as a **ceremony**: the cryptographic operations are *not* performed by an automated agent — they are **human physical/cognitive actions**. That re-reading is the whole point; it exposes the *Usability Surface* on which stressors act.

**Parties.** Alex (A, initiator) and Blake (B, responder). Goal: agree on a session key $SK = kdf(N_A, N_B)$.

**Message flow (protocol view).**
1. $A \to B : N_A$
2. $B \to A : N_B$
3. $A \to B : \text{ACK}$

with $SK = kdf(N_A, N_B)$ derived **independently** by each party (all calculations performed by the participants).

**Ceremony view (the Usability Surface).** Each protocol message decomposes into human micro-actions; §4's stressors attach to specific ones. This is what a ceremony adds over a protocol:

| # | Protocol msg | Human micro-action | Model action type | Hardness | Stressor surface |
|---|---|---|---|---|---|
| 1 | $A\to B: N_A$ | Alex generates/recalls a fresh nonce; transcribes & sends | `GEN_NONCE` + `SEND_MSG` | Easy | distraction → transcription slip |
| 2 | $B\to A: N_B$ | Blake reads $N_A$; generates $N_B$; **derives $SK=kdf(N_A,N_B)$**; sends | `GEN_NONCE` + **`CALC_SK`** + `SEND_MSG` | **Hard** (the KDF) | cognitive load on the derivation |
| 3 | $A\to B: \text{ACK}$ | Alex reads $N_B$; **derives $SK=kdf(N_A,N_B)$**; confirms | **`CALC_SK`** + `SEND_MSG` | **Hard** (the KDF) | cognitive load on the derivation |

The **`CALC_SK`** step — "compute a KDF in your head / by hand" — is the natural *Hard* request: it is the formalization's $r_{hard}$ and the trigger for σ₁ `HighCognitiveLoad`. This is precisely why the toy ceremony, tiny as it is, is already a sufficient host for the headline failure loop with **no extra machinery**.

**Mapping to the machinery (formalization §2–§4).** $\mathcal{P}$'s stages instantiate as Alex's view `Start →(send N_A) WaitNonce →(recv N_B, CALC_SK, send ACK) Done` (Blake mirrors). $f_U, f_M, f_H$ are exactly the formalization's functions, with their domain fixed to the action vocabulary $\{$`GEN_NONCE`, `CALC_SK`, `SEND_MSG`$\}$.

**Properties — to establish, then to break.**
- **Security baseline = Agreement.** An honest run ⇒ Alex and Blake derive the *same* $SK$ (agreement on $\langle N_A, N_B\rangle$). This is the property the usability failures will violate.
- **Channel/secrecy caveat (state it explicitly in `ceremony.spthy`).** Because $N_A, N_B$ travel in cleartext, a Dolev–Yao adversary on the wire can also compute $kdf(N_A,N_B)$ — so **SK-secrecy does *not* hold for the bare toy** and is deliberately **not** a baseline lemma. The upstream toy protects key material with asymmetric encryption; adding a confidential channel (or that encryption) is a *later* experiment. For the usability study we center on **Agreement + Liveness**, which are exactly what masks degrade.
- **Usability Liveness** (formalization §5): all-`Attentive` ⇒ `Done` reachable with agreement.
- **Protocol Vulnerability** (formalization §5): a `Busy` `CALC_SK` ⇒ no correct $SK$ / agreement broken.

---

## Phase 0. Bootstrap — prove the machinery on the smallest experiment first

> **Why this preceded §1–§10 (✅ this phase is complete; see §0).** The repo was greenfield when this was written. The grand plan builds *breadth* — all outcomes, 7 masks, 10 stressors, the `core/`+`ceremonies/` split. But you cannot refactor or regression-test what does not exist, so the lowest-risk path was a **vertical experiment**: one end-to-end causal chain — *one stressor → one transition → one degraded action → one broken property* — proved in Tamarin before any breadth. The experiment de-risked the modeling idiom **and** became the regression anchor every later step keeps green. *(The fragments shown below are the original sketch; the as-built model uses the derived-mask encoding — see the §0 deviations and the encoding note after Experiment 01.)*

**The unit of progress is a "experiment."** Each experiment is independently provable and adds *exactly one* construct plus the lemmas that test it. The test vocabulary — what "green" means in a prover — has three kinds:

- **sanity (`exists-trace`)** — the intended honest trace is reachable. Guards against an over-constrained model that proves safety *vacuously*. **Every experiment needs at least one.**
- **failure-reachability (`exists-trace`)** — the new *bad* chain can actually happen.
- **safety / control (`all-traces`)** — the bad outcome is bounded (only via the stressor; never under the mitigation).

> The Tamarin fragments below are **design targets** written in Tamarin-ish syntax to make the experiment unambiguous; none is claimed proven. Each must be validated with `tamarin-prover … --prove` (no `sorry`, no hand-fed `oracle`) as it is written.

### Experiment 00 — Walking skeleton (ceremony + `Attentive` only, no stressors)

Smallest runnable theory: the protocol layer + happy path compile and prove, establishing the baseline the failures will perturb. **Resist adding any stressor, transition, or second mask here.**

```
theory ToyCeremony_Baseline begin
functions: kdf/2     // free 2-ary symbol: kdf(a,b)=kdf(a',b') iff a=a' & b=b'
// DY adversary controls the wire (Out/In). Secrecy is NOT claimed (see §C0 caveat).

rule Init_Alex:  [ Fr(~idA) ] --[ Start('Alex') ]-> [ AlexInit(~idA), St_H('Alex','Attentive') ]
rule Init_Blake: [ Fr(~idB) ] --[ Start('Blake') ]-> [ BlakeInit(~idB), St_H('Blake','Attentive') ]

// Msg1  A->B : N_A    (GEN_NONCE; Attentive => valid)
rule A_send_Na:
  [ AlexInit(idA), St_H('Alex','Attentive'), Fr(~Na) ]
  --[ Gen('Alex','Attentive'), Send('Alex',~Na) ]->
  [ AlexWait(idA,~Na), St_H('Alex','Attentive'), Out(~Na) ]

// Msg2  B->A : N_B    (GEN_NONCE + CALC_SK; Attentive => valid)
rule B_recv_Na_send_Nb:
  [ BlakeInit(idB), St_H('Blake','Attentive'), In(Na), Fr(~Nb) ]
  --[ Gen('Blake','Attentive'), Calc('Blake','Attentive'), Key('Blake', kdf(Na,~Nb)), Send('Blake',~Nb) ]->
  [ BlakeDone(idB, kdf(Na,~Nb)), St_H('Blake','Attentive'), Out(~Nb) ]

// Msg3  A->B : ACK    (CALC_SK + SEND; Attentive => valid)
rule A_recv_Nb_ack:
  [ AlexWait(idA,Na), St_H('Alex','Attentive'), In(Nb) ]
  --[ Calc('Alex','Attentive'), Key('Alex', kdf(Na,Nb)), Finish('Alex') ]->
  [ AlexDone(idA, kdf(Na,Nb)), St_H('Alex','Attentive'), Out('ACK') ]

lemma L0_completes:   // sanity: the ceremony can finish
  exists-trace "Ex #i. Finish('Alex') @ i"

lemma L0_agreement:   // honest run => same SK (shared variable k forces equality)
  exists-trace "Ex k #i #j. Key('Alex',k)@i & Key('Blake',k)@j"
end
```

**Done = both lemmas green under `--prove`.**

### Experiment 01 — One stressor + one transition (the headline loop)

Add the single causal chain **σ₁ `HighCognitiveLoad` → (`Attentive`→`Busy`) → `slip` on `CALC_SK`**. This is the "one mask transition with one stressor within the ceremony" the bootstrap targets, and it instantiates the formalization's §4 feedback-loop algorithm verbatim. Apply the stressor to **Alex's msg-3 `CALC_SK`**; keep Blake `Attentive` so the disagreement is attributable to one party.

Refactor: Alex's msg-3 rule no longer computes `kdf` inline — it **issues a `CALC_SK` request** `ProtocolRequest('Alex', rid, 'CALC_SK', <Na,Nb>, 'Hard')` and later consumes `KeyResult('Alex', rid, sk)` to send ACK with whatever key resulted. Then add exactly four rules:

```
// f_U : a Hard request deposits the stressor (copy the request, don't consume it)
rule Trigger_HighCognitiveLoad:
  [ ProtocolRequest(P, rid, 'CALC_SK', m, 'Hard') ]
  --[ Load(P) ]->
  [ ProtocolRequest(P, rid, 'CALC_SK', m, 'Hard'), !Stressor(P,'HighCognitiveLoad') ]

// f_M : Attentive --HighCognitiveLoad--> Busy
rule MaskShift_Attentive_Load_Busy:
  [ St_H(P,'Attentive'), !Stressor(P,'HighCognitiveLoad') ]
  --[ Mask(P,'Attentive','Busy') ]->
  [ St_H(P,'Busy') ]

// f_H : Attentive answers CALC_SK correctly
rule Calc_Attentive:
  [ ProtocolRequest(P, rid, 'CALC_SK', <Na,Nb>, c), St_H(P,'Attentive') ]
  --[ Calc(P,'Attentive'), Key(P, kdf(Na,Nb)) ]->
  [ St_H(P,'Attentive'), KeyResult(P, rid, kdf(Na,Nb)) ]

// f_H : Busy slips — emits a FRESH wrong key (top symbol != kdf, so it can never equal kdf(_,_))
rule Calc_Busy_slip:
  [ ProtocolRequest(P, rid, 'CALC_SK', <Na,Nb>, c), St_H(P,'Busy'), Fr(~wrong) ]
  --[ Calc(P,'Busy'), Slip(P), Key(P, ~wrong) ]->
  [ St_H(P,'Busy'), KeyResult(P, rid, ~wrong) ]
```

**Minimal payload:** only a `complexity` field (`'Hard'`) is needed now — **not** §6's full six-field `flags` tuple. §6's enrichment is deferred until a *second* flag-keyed stressor needs it; the experiment proves the mechanism with one field.

**The experiment's test suite** — five lemmas that map 1:1 onto the formalization's three formal properties plus the §2 safe-fail/unsafe-success distinction:

| Lemma | Kind | Asserts | Machinery tie |
|---|---|---|---|
| `L1_attentive_ok` | `exists-trace` | `Calc(p,'Attentive') & Key(p,k)` — happy path still alive (no Experiment-00 regression) | Liveness |
| `L1_load_causes_slip` | `exists-trace` | `Load@s ⇒ Mask(Attentive,Busy)@m ⇒ Slip@o`, `#s<#m<#o` — failure chain reachable | feedback-loop §4 |
| `L1_unsafe_completion` | `exists-trace` | `Finish('Alex')` reachable with `Key('Alex',ka) & Key('Blake',kb) & not(ka=kb)` — completes **wrongly**, not a safe stall | §2 unsafe-success |
| `L1_stressor_causality` | `all-traces` | every `Mask(_,'Attentive','Busy')@m` has a prior `Load@s, #s<#m` | Safety: Stressor Causality |
| `L1_busy_no_correct_key` | `all-traces` | `Calc(p,'Busy') & Key(p,k) ⇒ not(Ex a b. k=kdf(a,b))` (holds structurally: `~wrong` is fresh) | Protocol Vulnerability |

```
lemma L1_attentive_ok:        // sanity: happy path survives (no Experiment-00 regression)
  exists-trace
  "Ex p k #i. Calc(p,'Attentive')@i & Key(p,k)@i"

lemma L1_load_causes_slip:
  exists-trace
  "Ex p #s #m #o. Load(p)@s & Mask(p,'Attentive','Busy')@m & Slip(p)@o & #s < #m & #m < #o"

lemma L1_unsafe_completion:
  exists-trace
  "Ex ka kb #i #j #f. Key('Alex',ka)@i & Key('Blake',kb)@j & Finish('Alex')@f & not(ka = kb)"

lemma L1_stressor_causality:
  all-traces
  "All p #m. Mask(p,'Attentive','Busy')@m ==> (Ex #s. Load(p)@s & #s < #m)"

lemma L1_busy_no_correct_key:
  all-traces
  "All p k #i. (Calc(p,'Busy')@i & Key(p,k)@i) ==> not(Ex a b. k = kdf(a,b))"
```

**This one experiment already exercises every machinery layer** — $\mathcal{P}$ (the steps), $\mathcal{U}$ ($f_U$ = `Trigger_HighCognitiveLoad`), $\mathcal{H}/f_M$ (the `MaskShift` edge), $f_H$ (degraded `Calc_Busy_slip`), and $\mathcal{N}$ (the `Out`/`In` wire). That is exactly why it is the right first thing to build: it is the minimum that touches the whole model.

> **Encoding note — the stored-mask style shown above was replaced (done).** The fragments carry the mask as a *stored* linear fact (`St_H(P,'Busy')`) flipped by a `MaskShift` rule. **This is not what is on disk.** In the actual model the mask is *derived* (machinery §6.2 / §6a-rule-1): `St_H`/`MaskShift` are gone; only the monotone `!Stressor(P,σ)` facts persist, and `f_H` derives the mask at response time, emitting `Mask(P,'Attentive','Busy')` as an *action* fact. The `L1_*` lemmas key off the `Mask(...)`/`Slip(...)`/`Key(...)` action facts, so they were unaffected by the switch. The stored-`St_H` style actually made Tamarin's sources solver **loop** (it could source `St_H` from the rule that consumes it); the derived style is loop-free. The fragments are retained only as a gentler first reading. As built, Experiment 01 also issues the CALC_SK request as a **persistent `!Req`** and adds `OneInstancePerHuman` / `OneStressPerParty` / `OneAnswer` / `AttentiveOnlyBeforeLoad` restrictions.

### After the experiment — how to grow (re-entry into the grand plan)

Each later construct is "one more experiment," reusing the same three-kind test ladder:

- **Experiment 02 — ✅ DONE (built differently than first sketched).** σ₈ `Habituation` → `Habituated` → `auto_approve`, on a new `APPROVE_REQ` UI phase (`protocol/approval_ui.spthy`): a persistent `!Session` issues repeated prompts; an Attentive user verifies (`'self'` prompts only) while a habituated one auto-approves *any* prompt — including an adversary-`'injected'` one (the prompt-bombing breach). σ₈ is **history-keyed**: it fires after ≥2 distinct prior Attentive approvals. Five `L2_*` lemmas (sanity, breach-reachable, causality, derived-mask, and the Attentive-never-injected contrast). The **`shutout` mitigation half is still ⬜ pending** — Experiment 02 proves the failure; the number-matching fix is a later experiment (needs §7).
- **Experiment 03 — ✅ DONE (this is the distraction/Careless experiment, *not* Pathway B).** σ₂ `ExternalDistraction` → `Careless` → `timeout`, reusing the Experiment-01 CALC_SK request flow. Establishes the **safe-fail** semantics (the ceremony stalls; Careless emits no key) versus Experiment 01/2's unsafe-success. Five `L3_*` lemmas. **Pathway B is now ⬜ unbuilt** and reassigned to a future experiment (see §10).
- **Experiments 04–09 — ✅ DONE.** Multi-stressor (04), recovery (05), Abstraction→Naive (06), SecurityAnxiety→Fearful (07), TimePressure→Busy (08), and the maximal all-stressors ceremony (09). **Highest-value remaining ⬜:** **Pathway B** (σ₄ `MisleadingTerminology` → `mistake` from an *Attentive* user, no transition — the second failure pathway), **chaining** (σ₁₀ RepeatedFailure → Naive→Fearful), and `bypass`/σ₇.
- **Payload enrichment (§6) + the full `core/` split** have already happened structurally; what remains is the six-field `flags` tuple, needed once a flag-keyed stressor (σ₃–σ₇) lands.

---

## 1. Theoretical grounding → model constructs

This is the bridge: each HCI framework maps to a concrete object in the Tamarin model.

| Literature | Core idea | Becomes in the model |
|---|---|---|
| **Norman — Slip** | correct intent, failed execution (distraction, automaticity) | outcome `slip()`; produced by Busy/Careless under load |
| **Norman — Mistake** | wrong intent from a wrong mental model | outcome `mistake()`; **can be produced even by Attentive** when the request is misleading — a failure pathway that bypasses mask transitions |
| **Norman — Gulf of Execution/Evaluation** | "how do I act?" / "did it work?" | request **flags** `guidance` and `feedback`; their absence is what triggers mistakes |
| **Whitten & Tygar — Unmotivated user** | security is a secondary task | stressor `SecondaryTask`; drives bypass/skip |
| **Whitten & Tygar — Abstraction** | crypto has no physical analog | stressor `Abstraction`; feeds `HighCognitiveLoad`, Naive mistakes |
| **Whitten & Tygar — Lack of feedback** | correct security is invisible | request flag `feedback='None'`; enables Gulf-of-Evaluation mistakes |
| **Whitten & Tygar — Barn Door** | exposure is irreversible | outcome **severity** flag; a safety-lemma concern, not a behavior |
| **Whitten & Tygar — Weakest link** | one error breaks everything | the `all-traces` safety lemmas; one bad `f_H` must not reach `Success` |
| **Cranor — C-HIP receiver stages** | deliver→attend→comprehend→believe→motivate→act | the stage at which a mask "drops out" labels *which* failure it is |
| **Cranor — user types** | Clueless / Unmotivated / Cognitively-limited / Malicious | maps onto masks (see §3) |
| **Yee — 10 guidelines** | path-of-least-resistance, visibility, trusted path… | **protective** request flags + recovery triggers (§7) |
| **Poka-Yoke — Shutout/Shutdown/Warning** | mistake-proofing levels | request flag `pokayoke ∈ {none, warning, shutdown, shutout}`; a shutout makes even a bad mask unable to emit a bad outcome (§7) |

**Two failure pathways (key architectural insight).** The current architecture assumes *stressor → mask change → degraded action*. Norman's **mistake** reveals a second pathway: *misleading task design → wrong action regardless of mask*. The model must support both:

- **Pathway A — mask-mediated** (slips, withdrawal, habituated approval): stressor flips the mask; the new mask's `f_H` degrades the output. *(current architecture)*
- **Pathway B — task-mediated mistake** ✅ **(built, Exp 13)** (S3 terminology): `f_H` reads a request flag (`terminology='Misleading'`) and produces `mistake()` **even for Attentive**, with no mask change (no `SetMask`). Proven by `L13_mistake_is_task_mediated_not_mask`. The ceremony carries the supplied terminology flag (σ₄ is presentation, not inferable). σ₅ `LackOfFeedback` would extend the same mechanism ⬜.

---

## 2. Outcome vocabulary (refine `types.spthy`)

The single most important enrichment. **Built so far:** valid (`kdf`), `slip` (Experiment 01), `auto_approve` (Experiment 02), `timeout` (Experiment 03). The rest are the *target* vocabulary, still ⬜ pending. Each carries a `UsabilityFailure` reason label:

| Status | Outcome value | Reason label | Meaning | Norman/literature | Case study |
|---|---|---|---|---|---|
| ✅ | valid (`~n`,`kdf`,`data`) | — | task done as designed | — | — |
| ✅ | `slip()` | `'Slip'` | correct intent, wrong execution | Norman slip | — |
| ✅ | `mistake()` | `'Mistake'` | confident wrong action, wrong mental model | Norman mistake | S3 "Any Authenticated Users" |
| ⬜ | `bypass()` | `'Bypass'` | deliberately circumvents the control to finish the primary task | Unmotivated / workaround | EHR sticky-notes, Shadow AI |
| ✅ | `auto_approve()` | `'HabituatedApproval'` | reflexive "yes" without reading | habituation / RS | MFA prompt-bombing, warning fatigue |
| ✅ | `timeout()` | `'Timeout'` | disengages / gives up | — | — |
| ✅ | `abort()` | `'Withdrawal'` | refuses to continue (distrust) | — | Fearful |

`mistake()`, `bypass()`, and `auto_approve()` are the dangerous ones: unlike `timeout`, they let the ceremony *proceed* with a compromised result — which is precisely how the real-world incidents broke security. Lemmas should distinguish "ceremony stalls (safe-fail)" from "ceremony completes wrongly (unsafe-success)".

---

## 3. Masks to review (user-centered + reconciled with Cranor)

Cranor's four honest-user types map cleanly onto the masks; the mapping both validates the set and reveals one gap (**Habituated**).

| Cranor type | Mask | Fit |
|---|---|---|
| Clueless (unaware action is security-relevant) | **Naive** | strong |
| Cognitively-limited (motivated, capable, but memory/complexity-bound) | ~~Elder~~ → **Busy / Naive** (stressor-induced) | Elder descoped (persona, not stressor-induced — see below); the cognitive-barrier effects are covered by Busy (pace/load) and Naive (complexity) |
| Unmotivated (knows, but friction not worth it) | **Careless** (+ proposed split) | partial — see Habituated/bypass |
| Malicious | — | out of scope (honest-but-erring model) |

### Behavioral signature matrix (target design)

Outcomes per `f_H(mask, action)`. New action types `APPROVE_REQ` (push/MFA), `SET_POLICY` (config) added (§6).

Outcomes per `f_H(mask, action)`. **Built cells are marked** `✅` with the file that implements them; the rest are target design. (Built `f_H` is currently action-scoped — see §0 note 2 — so e.g. Attentive's CALC_SK cell is `attentive_calc.spthy` and its APPROVE_REQ cell is `attentive_approve.spthy`.)

| Status | Mask | GEN_NONCE | CALC_SK (hard) | SEND_MSG | APPROVE_REQ | SET_POLICY | User-centered description |
|---|---|---|---|---|---|---|---|
| ✅ | **Attentive** | valid | ✅ valid | valid | ✅ valid (verifies `'self'`) | valid *if* terminology clear, else `mistake` (Pathway B) | "I read each step, double-check, and finish as intended." |
| ✅ | **Busy** | `slip` | ✅ `slip` | valid | ✅ `auto_approve` (`busy_approve`) | `bypass` | "Short on time, I skim and act fast — that's when I slip, or work around the control to keep moving." |
| ✅ | **Careless** | `timeout` | ✅ `timeout` | `timeout` | ✅ `timeout` (`careless_approve`; was `auto_approve` — revised: Careless dismisses) | `bypass` | "I don't engage with security; I skip, dismiss, or take the shortcut." |
| ✅ | **Fearful** | valid (slow) | `abort`/`timeout` | `abort` on sensitive sends | `abort` (rejects all, even valid) | `abort` | ✅ built on the new **AUTHORIZE** phase (Exp 07): Fearful `abort`. "I don't trust this; on anything security-critical I hesitate, back out, or refuse." |
| ✅ | **Naive** | valid *iff* guided | `mistake` (no mental model) | valid (follows literally) | `auto_approve` (doesn't grasp the risk) | `mistake` | ✅ built on the new **VERIFY_KEY** phase (Exp 06): Naive `mistake` (accepts tampered). "I do exactly what the screen says; lost when a step assumes knowledge I lack." |
| ✂️ | **Elder** *(out of scope)* | — | — | — | — | — | *Descoped: Elder is a persona/trait (who the user is), not a mask induced by a ceremony stressor like the others. See note below.* |
| ✅ | **Habituated** | valid | valid | valid | ✅ **`auto_approve`** (reflexive yes) | valid | "I've seen this prompt a hundred times; I click through without reading to make it stop." |

**On `Habituated`** — ✅ **built (Experiment 02)**; the §11 decision to add it is resolved *yes*. Empirically the strongest single addition the research supports (BYU fMRI repetition-suppression; MFA fatigue at Uber/Cisco/MGM). It is *not* Careless — both are built and the contrast is now *proven*: the Careless user disengages (`timeout`, Experiment 03, safe-fail), the Habituated user **actively approves** (`auto_approve`, Experiment 02, unsafe-success) — the exact behavior prompt-bombing weaponizes. Note: only the cells exercised by an experiment are built; the other cells in the Busy/Careless/Habituated rows (e.g. their `SET_POLICY`/`bypass` behavior) remain target design.

**On `Elder` — ✂️ out of scope (decided 2026-06-26).** Unlike the other masks, Elder is a *persona/trait* — a property of *who the user is* (age, memory/complexity limits), not a transient mask *induced by a ceremony stressor*. Our model derives masks from the ceremony's stressors (and the analyzer infers them from steps); a trait the user brings to the ceremony belongs to a separate "starting persona" mechanism (cf. trait start states, §11.5) rather than the stressor→mask machinery. The *effects* often attributed to Elder are already covered by stressor-induced masks (pace → Busy via σ₃ TimePressure; complexity → Naive/Busy). So Elder is not built; the cognitive-barrier phenomena are modelled through the existing masks.

**Optional split — `Unmotivated`/`Pragmatic`** (Shadow AI, clinical workarounds): a user who *understands* the control but routes around it (`bypass`). Folded into Busy/Careless in the target matrix. Decide in §11 whether it warrants its own mask.

---

## 4. New stressors — what to model and how (`f_U`)

Literature-grounded catalogue. Shared implementation pattern (the same shape as the Phase-0 `Trigger_HighCognitiveLoad` rule): fire on a condition, emit `UsabilityProblem`, deposit `!ActiveStressor`, copy (don't consume) `HumanState`/`ProtocolRequest`.

| Status | # | Stressor | Trigger (`f_U`) | Anchor | Feeds → |
|---|---|---|---|---|---|
| ✅ | σ₁ | `HighCognitiveLoad` **(Experiment 01)** | `CALC_SK` request, `complexity='Hard'` | Abstraction | Attentive→Busy |
| ✅ | σ₂ | `ExternalDistraction` **(Experiment 03)** | unconditional (any pending `!Req`, ignores `complexity`) | Norman slip | Attentive→Careless |
| ✅ | σ₃ | `TimePressure` **(Exp 08)** | deadline on CALC_SK (any complexity) | EHR workarounds | Attentive→Busy |
| ✅ | σ₄ | `MisleadingTerminology` **(Exp 13)** | supplied `terminology='misleading'` flag on SET_POLICY | S3 case | **Pathway B** mistake (no mask change) |
| ⬜ | σ₅ | `LackOfFeedback` | request flag `feedback='None'` | Whitten #3, PGP9 | Pathway B mistake; Gulf of Evaluation |
| ✅ | σ₆ | `Abstraction` **(Exp 06)** | the abstract VERIFY_KEY fingerprint check | Whitten #2, PGP | Attentive→Naive |
| ⬜ | σ₇ | `SecondaryTask` | participant has a competing primary-task fact | Whitten #1, Shadow AI | →bypass (Busy/Careless) |
| ✅ | σ₈ | `Habituation` **(Experiment 02)** | **N≥2 distinct prior Attentive `APPROVE_REQ`** (history-keyed: reads two persistent `!Approved` facts, distinctness via `Neq`) | BYU RS; MFA fatigue | Attentive→Habituated |
| ⬜ | σ₉ | `AlertVolume`/`DecisionFatigue` | ≥k requests within the trace before a `Step` | MFA prompt-bombing | →Habituated/Careless |
| ⬜ | σ₁₀ | `RepeatedFailure` | a prior `UsabilityFailure` exists earlier | — | Busy→Careless; Fearful→abandon |

**Three trigger flavours** (✅ flavours 1 and 3 now have working exemplars):
1. **Type-keyed** (σ₁ ✅): trivial — match request type / `complexity`. σ₂ ✅ is the degenerate "any request" case.
2. **Flag-keyed** (σ₃–σ₇ ⬜): needs the payload enrichment in §6. Unlocks five stressors at once.
3. **History-keyed** (σ₈ ✅, σ₉/σ₁₀ ⬜): *count/existence* lives in the rule LHS (σ₈ reads two distinct persistent `!Approved` facts, distinctness forced by a `Neq` restriction), while *temporal ordering* lives in the **lemma** (`#a < #h`). The lesson held: don't try to encode the ordering in the multiset LHS — only the existence of the prior events.

**Next stressors to implement (⬜):** σ₄ `MisleadingTerminology` (cleanest demonstration of **Pathway B** — a `mistake` from an *Attentive* user, no transition), σ₅ `LackOfFeedback`, σ₇ `SecondaryTask` (→ `bypass`), σ₁₀ `RepeatedFailure` (→ chaining, e.g. Naive→Fearful). *(✅ done: σ₁, σ₂, σ₃, σ₆, σ₈, SecurityAnxiety — Experiments 01–09.)*

---

## 5. New mask transitions (`f_M` graph)

```
  Attentive ──Abstraction/UnclearInstr──▶ Naive ──RepeatedFailure──▶ Fearful
     │ │ │ │                                │                          │
     │ │ │ └─SecurityAnxiety/LowTrust──────▶ Fearful                   │ (terminal:
     │ │ └───CogLoad/TimePressure──────────▶ Busy                      │  abort/timeout)
     │ └─────Distraction───────────────────▶ Careless ◀──RepeatedFailure─┘
     └───────Habituation (N≥2 prompts)─────▶ Habituated ──(more prompts)──▶ auto_approve

  Trait start states (init.spthy):  Naive · (Fearful)        [Elder ✂️ out of scope — §3]

  RECOVERY (new direction, via Poka-Yoke / Yee — §7):
  Habituated ──NumberMatching (shutout)──▶ Attentive   (re-engagement forced)
  Fearful    ──TrustedPath + clear feedback──▶ Attentive
  Naive      ──Guidance repeated / success───▶ Attentive
```

| Status | Source | Condition | Target | Rationale / anchor |
|---|---|---|---|---|
| ✅ | Attentive | `HighCognitiveLoad` **(Experiment 01)** | Busy | — |
| ✅ | Attentive | `ExternalDistraction` **(Experiment 03)** | Careless | — |
| ✅ | Attentive | `TimePressure` **(Exp 08)** | Busy | EHR |
| ✅ | Attentive | `Abstraction` **(Exp 06)** | Naive | PGP key metaphor |
| ✅ | Attentive | `SecurityAnxiety` **(Exp 07)** | Fearful | low trust |
| ✅ | Attentive | `Habituation` (N≥2) **(Experiment 02)** | **Habituated** | BYU / MFA fatigue |
| ⬜ | Naive | `RepeatedFailure` | Fearful | confusion → withdrawal |
| ✂️ | ~~Elder~~ | `TimePressure`/`StepDensity` | Fearful | **out of scope** (Elder descoped — §3) |
| ⬜ | Busy | `RepeatedFailure` | Careless | errors → disengagement |
| ⬜ | Habituated | more prompts | (terminal `auto_approve`) | prompt-bombing payoff |
| ✅/⬜ | Naive / Fearful / **Habituated ✅** | **recovery condition** (Habituated via UI warning, Exp 05) | Attentive | mitigations work (§7) |

> **As-built mechanics (current).** Edges are *not* `MaskShift` rules over a stored `HumanState`. The mask is a **persistent current mask derived from `SetMask(P,m)` events** (`core/transitions/mask_state.spthy`): each stressor emits `SetMask` at its onset (inside the trigger rule), the recovery warning emits `SetMask(P,'Attentive')`, and the gates (`RespondDegradedRequiresActive`, `AttentiveRequiresNoActiveDegrade`) make every `f_H` respond as the current mask, which **persists across action types until a recovery**. So an edge `Attentive→X` is just "stressor X's trigger emits `SetMask(P,'X')`"; the **recovery** edge (Habituated→Attentive, Exp 05) is the warning emitting `SetMask(P,'Attentive')` that supersedes the degrade. Encoded as *"degrade active until recovery"* (not strict latest-wins — the tractable choice; machinery §6.8). All `SetMask`-latching events are bounded once per party (`OneStressPerParty`, `OnceHabituate`, `OneSetMaskPerMask`, …) so the interval reasoning terminates (≤2 s). The per-edge `from_attentive*.spthy` gate files and the separate `recovery.spthy` of earlier drafts **no longer exist** — they were folded into the trigger's `SetMask` + `mask_state.spthy`. Remaining: other recovery edges (Fearful/Naive→Attentive) ⬜, **chaining** (only σ₁→σ₁₀→Careless, via the `!Failed` detector, is built) 🟡, **trait start states** ⬜. **Branching caution** still holds — keep per-experiment stressor sets small (§6a).

---

## 6. Cross-cutting prerequisite: enrich the request payload

Pathway B, five stressors, and the guidance-conditional masks all depend on `f_H`/`f_U` being able to read properties of the request. The base `ProtocolRequest(id, rid, type, data)` carries only opaque `data`; Experiment 01 (§Phase 0) already adds a single standalone `complexity` arg, and this section folds that — plus the rest — into one `flags` tuple.

**Proposed:** `ProtocolRequest(id, rid, type, <data, flags>)` with
`flags = <complexity, guidance, feedback, terminology, sensitivity, pokayoke>`
(constants like `'Hard'/'Easy'`, `'Guided'/'Bare'`, `'Visible'/'None'`, `'Clear'/'Misleading'`, `'Sensitive'/'Normal'`, `'none'/'warning'/'shutdown'/'shutout'`).

- **Set** in `protocol_requests.spthy` — the designer's choices become explicit and auditable (this *is* the Yee/Poka-Yoke design surface).
- **Read** by `f_U` (flag-keyed stressors) and `f_H` (guidance-conditional outcomes, Pathway-B mistakes).
- **Cost:** touches every rule matching `ProtocolRequest`. Do it as one mechanical refactor **once a second flag-keyed stressor needs it** (not before — see §10's re-sequencing); re-run the Phase-0 experiment lemmas (`L0_*`, `L1_*`) to confirm no regression.

New **action types** to add alongside (each = one request rule + one advance rule + one `f_H` row per mask): `APPROVE_REQ` (MFA push), `SET_POLICY` (S3-style config), `VERIFY_KEY` (PGP key-signing metaphor).

---

## 6a. State-space discipline — composable experiment profiles (avoid explosion)

> **The constraint that makes the breadth above tractable.** The construct menu (7 masks, 10 stressors, chained transitions, mitigations) is a *catalogue*, not a single model to instantiate at once. Modeled naïvely, one participant's human state $\langle M, \Sigma\rangle$ with $\Sigma \subseteq \{\sigma_1..\sigma_{10}\}$ is a powerset — $6{,}144$ states per human, $6{,}144^{N}$ for $N$ participants — and Tamarin will not terminate. This section is the rule that keeps every experiment (§Phase 0, §9) provable. Formalized in `mask_machinery_formalization.md` §6.

**An experiment is a *profile*, never the whole machinery.** A profile selects a small subset:
$$\mathcal{E} = \langle\, C,\ \mathcal{M}\subseteq\text{Masks},\ \mathcal{S}_\sigma\subseteq\{\sigma_1..\sigma_{10}\} \,\rangle$$
and instantiates *only* the masks, stressors, and `f_M` edges among them that the profile names. The full system is the union of profiles — but the union is **never built**; each `ceremony.spthy` `#include`s only what its experiment exercises (Appendix A already enforces this at the file level). Phase 0 is the smallest profile: $\mathcal{E}_0 = \langle C_0, \{\text{Attentive},\text{Busy}\}, \{\sigma_1\}\rangle$, one edge, one stressed party.

**Five rules each `*.spthy` author must follow:**

| # | Rule | Effect on state space | Where enforced |
|---|---|---|---|
| 1 | **Mask is a label, not a stored fact** — `f_H` computes the mask from the active stressor at response time; don't carry `M` as an independent state dimension. | removes the $\times|M|$ factor | `core/masks/*` emit `Mask(...)` as an action fact, not a persistent `!Mask` |
| 2 | **At most one active stressor per human** — a restriction caps `!Stressor(h,_)` to one; no powerset of $\Sigma$. | $2^{k} \rightarrow k{+}1$ | restriction in `core/types.spthy` |
| 3 | **Monotone only** — stressors accumulate, masks degrade; recovery is a *separate positive* `!Mitigation` fact (§7), never stressor removal. | reachable graph is a DAG ⇒ partial-order pruning | `core/transitions/*` consume linear `HumanState`, no LHS negation |
| 4 | **Narrow interface** — the only `𝒫→𝓗` coupling is request `complexity ∈ {Easy,Hard}` (`f_U`); layers compose through that one field. | no monolithic $\mathcal{P}\times\mathcal{H}\times\mathcal{U}\times\mathcal{N}$ product | §6 payload; `f_U` reads `complexity` only |
| 5 | **Per-experiment, one human** — prove §5's vulnerability on each $\langle$1 mask, 1 stressor$\rangle$ experiment under a single honest stressed party; orthogonal experiments compose **additively**. | $\sum_k|\text{experiment}_k|$ not $\prod_k 2^{|\mathcal S_{\sigma,k}|}$ | one experiment file per phenomenon (§9) |

**Consequence for sequencing.** Adding a mask or stressor to the *catalogue* never enlarges an existing experiment — it is a *new* profile (new include set, new experiment file). This is why Phase-1 steps parallelize (§10) and why the `core/`+`ceremonies/` split (Appendix A) pays off: includes *are* the profile selector. Keep $|\mathcal{S}_\sigma|$ per experiment small (ideally 1–2); a worst-case-discovery experiment that deliberately enables several stressors at once must `log`/comment the expected blow-up and run on the single-human, monotone encoding only. **Realized as Experiment 04** (`04_multi_stressor.spthy`): σ₁+σ₂+σ₈ and four masks on one human, used to study stressor *interaction* (e.g. a compound run that both slips on the KDF and auto-approves an injected prompt). It proves under the single-human + monotone + single-active-per-stressor discipline; its header carries the blow-up caveat.

---

## 7. Mitigations as first-class (Yee + Poka-Yoke)

The research is as much about *fixes* as failures. Modeling mitigations lets experiments verify **"does this design change neutralize this mask?"** — far more valuable than only demonstrating failure.

**Poka-Yoke levels** (the `pokayoke` flag) constrain `f_H` outputs:
- `shutout` (Control) ✅ **built (Exp 14, `core/mitigations.spthy`)** — protocol rejects a malformed/unverified input, so even a bad mask **cannot** emit a bad outcome. *Number-matching MFA = shutout: the Habituated user can't `auto_approve` because approval now requires a value only an engaged user can supply.* Realized as restriction `ShutoutBlocksAutoApprove` (`AutoApprove ⇒ ¬Shutout`); proven to neutralize the Exp-02 breach (`L14_shutout_blocks_injected`).
- `shutdown` — protocol halts on unsafe parameters (Block Public Access auto-enabled for S3).
- `warning` — non-blocking alert; weakest, and itself subject to habituation (σ₈) — the model can show warnings *decaying* in effectiveness.

**Yee guidelines** become protective request flags / recovery triggers:
- *Path of Least Resistance* — if the secure action is also the easy one, `SecondaryTask`/bypass stressors don't fire.
- *Visibility / Trusted Path* — `feedback='Visible'` blocks Pathway-B mistakes and enables Fearful→Attentive recovery.
- *Expected Ability / Clarity* — `guidance='Guided'` keeps Naive correct and drives Naive→Attentive recovery.

**Recovery mechanism:** a protective request deposits `!Mitigation(id, kind)`; recovery transition rules consume it to restore `Attentive`. Pairs of experiments (`failure` vs `mitigated`) then prove the fix.

---

## 8. Case study → model mapping (empirical anchor)

| Case study | Mask | Stressor | Outcome | Mitigation (→ recovery) |
|---|---|---|---|---|
| PGP / Mailvelope | Naive | `Abstraction`, `LackOfFeedback` | `mistake` / `timeout` (cleartext send) | `guidance`, auto key-mgmt (Yee: Expected Ability) |
| MFA prompt-bombing | Habituated | `Habituation`, `AlertVolume` | `auto_approve` | number-matching = `shutout` |
| AWS S3 | Attentive→**still fails** | `MisleadingTerminology`, `LackOfFeedback` | `mistake` (Pathway B) | Block Public Access = `shutdown`; clear terminology |
| Clinical EHR | Busy | `TimePressure`, `SecondaryTask`, `TaskInterference` | `bypass` (shared creds, taped sensors) | NFC + long-lived PIN = Path of Least Resistance |
| Shadow AI | Careless/Unmotivated | `SecondaryTask` | `bypass` (exfil to public LLM) | context-detecting block = `warning`/`shutout` |
| Warning habituation | Habituated | `Habituation` (RS after 2nd view) | `auto_approve` (click-through) | polymorphic warnings (resist RS) |

This table is the validation target: every row should become a passing pair of lemmas (failure reachable; mitigation neutralizes it).

---

## 9. Experiments to add

One self-contained file per phenomenon (lemmas only, mirroring the Phase-0 experiment lemmas; an `exists-trace` for the failure + an `all-traces` for the mitigation). **Built so far:** `experiments/02_habituated_mfa.spthy` (the failure half of `exp_mfa_fatigue` below) and `experiments/03_careless_distraction.spthy` (an `ExternalDistraction`/Careless safe-fail experiment, not originally on this list). Remaining files ⬜:

| File | Demonstrates |
|---|---|
| `exp_mfa_fatigue.spthy` ✅ **(complete pair)** | repeated `APPROVE_REQ` → Habituation → Habituated → `auto_approve` (failure = `02_habituated_mfa`); number-matching **shutout** neutralizes it (fix = `14_shutout_mitigation`) |
| `exp_s3_mistake.spthy` ✅ **(= Experiment 13)** | misleading terminology → **Attentive** still emits `mistake` (Pathway B); clear terminology is safe. *(`shutdown`-mitigation half still ⬜.)* |
| `exp_pgp_naive.spthy` | bare/abstract `VERIFY_KEY` → Naive → `mistake`; guided request keeps Naive correct |
| `exp_ehr_workaround.spthy` | TimePressure + SecondaryTask → Busy → `bypass`; path-of-least-resistance removes the incentive |
| `exp_warning_habituation.spthy` | warning effectiveness decays with repetition; polymorphic warning resists |
| ~~`exp_elder_pace.spthy`~~ | ✂️ **out of scope** — Elder descoped (§3); the pace effect is covered by σ₃ TimePressure → Busy (Exp 08) |
| `exp_cascade.spthy` | Attentive→Busy→(RepeatedFailure)→Careless |
| `exp_recovery.spthy` | Fearful/Naive/Habituated → Attentive via `!Mitigation` |

---

## 10. Suggested sequencing

> **Ordering (as executed).** The build started with the **vertical experiment** and grew breadth afterward. Phase 0 (Experiments 0–1) and two Phase-1 experiments (2–3) are done; the `core/`+`ceremonies/` layout was scaffolded early (not deferred). The payload-flags refactor (§6) remains the one genuinely deferred item, pending a flag-keyed stressor.

**Phase 0 — Bootstrap. ✅ DONE.**
- **0a. Experiment 00 ✅** — walking skeleton: toy ceremony C0 + `Attentive`-only; `L0_completes` + `L0_agreement` verified.
- **0b. Experiment 01 ✅** — σ₁ `HighCognitiveLoad` + Attentive→Busy + Busy `slip`; five `L1_*` verified.

**Phase 1 — Breadth (each step = a failure (and where possible mitigation) lemma set).**
1. **Outcome vocabulary (§2)** — 🟡 *partial*: `slip`, `auto_approve`, `timeout` are built; `mistake`/`bypass`/`abort` still ⬜.
2. **Mask-signature spec (§3)** — 🟡 *partial*: Attentive/Busy/Careless/Habituated/Naive/Fearful all built (the matrix is built only for the cells the experiments exercise); `Elder` ✂️ out of scope (§3).
3. **Habituated + MFA** — ✅ **complete pair**: σ₈, Attentive→Habituated, `APPROVE_REQ`, breach (`02_habituated_mfa`) **and** the number-matching `shutout` fix (`14_shutout_mitigation`).
   **3b. Distraction + Careless ✅** — σ₂, Attentive→Careless, `timeout`, `03_careless_distraction` (added; demonstrates safe-fail).
4. **Pathway B + S3 — ✅ DONE (Exp 13).** σ₄ terminology-driven `mistake` in `f_H`, `SET_POLICY`, `13_pathwayb_s3` (= `exp_s3_mistake`). Remaining ⬜: σ₅ `LackOfFeedback` (same mechanism) and the `shutdown`/clear-terminology **mitigation half**.
5. **Naive / Fearful ⬜** — guidance-conditional actions + trait start states (Naive, Fearful) and recovery edges. *(σ₃/σ₆ and the Attentive→Naive/Fearful edges are already built — Exp 06/07/08; Elder ✂️ out of scope, §3.)*
6. **Chaining & recovery ⬜** — σ₁₀, Busy→Careless, `!Mitigation` recovery, `exp_cascade` + `exp_recovery`. *(The σ₈ `shutout` is the natural first recovery edge.)*
7. **Payload enrichment (§6) ⬜ / `core/`+`ceremonies/` reorg ✅** — the structural split is already in place (it paid off immediately, not "only here"). What remains is the six-field `flags` tuple, needed once a flag-keyed stressor (σ₃–σ₇) lands; re-run all `L*` lemmas as regression then.
8. **Remaining stressors / cases ⬜** (Shadow AI bypass, warning polymorphism) as needed.

Each entry point is independently provable (`check.py --prove ceremonies/alex_blake_kdf/NN_<name>.spthy`) and respects the module seams; Phase-1 steps parallelize.

> **Sequencing note.** Reality diverged from the original order: the `core/`+`ceremonies/` reorg (step 7) was done *early* (after Experiment 01) rather than last, because Tamarin's wellformedness forces closed theories and the split made per-experiment profiles clean. The payload-flags half of step 7 is genuinely deferred until a flag-keyed stressor needs it.

---

## 11. Decisions needed before coding

> **Several are now resolved by the build** (✅); the rest are still open (⬜).

0. ✅ **Bootstrap entry point + channel** — *resolved.* C0 + Experiment 00→1 built; channel is Dolev–Yao, **Agreement + Liveness** proven, SK-secrecy deliberately deferred (per the §C0 caveat).
1. 🟡 **Outcome set** — *partially adopted.* `slip`/`auto_approve`/`timeout` built; `mistake`/`bypass`/`abort` still to add. No merges so far.
2. ✅ **Pathway B** — *resolved (Exp 13).* A `mistake` without a mask change, read from the request's `terminology` flag in `f_H` (`core/masks/attentive_policy.spthy`); proven task-mediated (`L13_mistake_is_task_mediated_not_mask`). σ₅ `LackOfFeedback` would reuse the same mechanism ⬜.
3. ✅ **`Habituated` as a mask** — *resolved: yes* (Experiment 02). `Unmotivated` is still folded into Busy/Careless (no separate mask built).
4. 🟡 **Mitigations first-class** — *substantially resolved.* Two mitigations built: the recovery warning (Exp 05) and the **`shutout`** Poka-Yoke (`core/mitigations.spthy`, Exp 14 — the first verified failure↔fix pair). Remaining ⬜: `shutdown` / decaying `warning` levels, Yee protective flags, recovery edges for Fearful/Naive, and more failure↔fix pairs (EHR, Shadow AI).
5. ⬜ **Trait start states** — still open: **Naive** (and possibly Fearful) as a selectable initial mask in `protocol/init.spthy` (today `init.spthy` carries no mask, since the mask is derived). *(Elder is ✂️ out of scope — §3.)*

---

## Appendix A. Repository layout for multiple ceremonies

**Guiding principle — two layers, two folders.** The human layer (masks, stressors, transitions, mitigations, outcomes) is *ceremony-agnostic*: it is written once and reused verbatim. The protocol layer (who the participants are, what requests they issue, how the state advances, what to prove) is *ceremony-specific*. Keep them in separate trees so that **adding a new ceremony touches zero files under `core/`.**

This works because action *types* are a small, shared **interface** (`GEN_NONCE`, `CALC_SK`, `SEND_MSG`, `APPROVE_REQ`, `SET_POLICY`, `VERIFY_KEY`…). Each mask defines its response to a type once, in `core/` (in a `<mask>_<actiongroup>.spthy` file — see the wellformedness note below); a ceremony is then just protocol logic that emits requests of those standard types. New ceremonies pick from the existing vocabulary; only a genuinely new kind of human action requires extending the interface (and then one file per participating mask).

**On-disk layout as built** (✅ = present; the rest is the projected shape as the catalogue grows):

```
tamarin_model/
├── core/                              # HUMAN LAYER — reusable across all ceremonies
│   ├── types.spthy                    # ✅ kdf/2 + OneInstancePerHuman restriction
│   ├── masks/                         #   f_H — ACTION-SCOPED: <mask>_<actiongroup>.spthy (see note)
│   │   ├── attentive_{calc,approve,verify,authorize,op,verify_op}.spthy   # ✅ Attentive, per action
│   │   ├── busy_{calc,approve,op}.spthy        # ✅ Busy (slip / auto_approve / op-slip)
│   │   ├── careless_{calc,approve,op}.spthy    # ✅ Careless (timeout / dismiss)
│   │   ├── habituated_approve.spthy            # ✅ Habituated (auto_approve)
│   │   ├── naive_{verify,verify_op}.spthy      # ✅ Naive (mistake)
│   │   ├── fearful_authorize.spthy             # ✅ Fearful (abort)
│   │   └── (elder ✂️ out of scope — §3)
│   ├── stressors/                     #   f_U — one trigger rule (+ its restriction) per file
│   │   ├── cognitive_load.spthy · time_pressure.spthy        # ✅ σ₁ · σ₃  (→ SetMask Busy)
│   │   ├── external_distraction.spthy                        # ✅ σ₂  (→ SetMask Careless)
│   │   ├── abstraction.spthy · habituation.spthy             # ✅ σ₆ · σ₈
│   │   ├── security_anxiety.spthy                            # ✅ SecurityAnxiety (→ Fearful)
│   │   ├── *_inferred.spthy (cognitive_load, abstraction, repeated_failure)  # ✅ inferred detectors (Exp 10–12)
│   │   └── {misleading_terminology, lack_of_feedback, secondary_task, alert_volume}.spthy  # ⬜
│   └── transitions/                   #   f_M — the current-mask GATES (edges live in the triggers' SetMask)
│       ├── mask_state.spthy           # ✅ OneSetMaskPerMask + RespondDegradedRequiresActive + AttentiveRequiresNoActiveDegrade
│       ├── answered_once.spthy        # ✅ AnsweredOnce
│       └── (no per-edge files: each f_M edge = its stressor trigger emitting SetMask; recovery = SetMask 'Attentive')
│
├── ceremonies/                        # PROTOCOL LAYER — one folder per ceremony
│   └── alex_blake_kdf/                #   the toy ceremony C0 (§C0): SK = kdf(N_A, N_B)
│       ├── ceremony.base.spthy        # ✅ shared spine: core/types + protocol/init + protocol/messages
│       ├── 00_baseline.spthy               # ✅ ENTRY — base + msg3_inline + L0
│       ├── 01_busy_under_load.spthy               # ✅ ENTRY — base + Busy machinery + msg3_request + L1
│       ├── 02_habituated_mfa.spthy               # ✅ ENTRY — base + Habituated machinery + msg3_inline + approval_ui + L2
│       ├── 03_careless_distraction.spthy               # ✅ ENTRY — base + Careless machinery + msg3_request + L3
│       ├── README.md                  # ✅ experiment index + run + how-to-add
│       ├── protocol/                  #   protocol fragments (the moving parts)
│       │   ├── init.spthy             # ✅ Init_Alex/Blake (no mask fact — mask is derived)
│       │   ├── messages.spthy         # ✅ Msg1 + Msg2 (shared)
│       │   ├── msg3_inline.spthy      # ✅ Msg3 INLINE (Experiment 00 baseline; KDF baseline for Experiment 02)
│       │   ├── msg3_request.spthy     # ✅ Msg3 REQUEST/ACK (Experiments 1 & 3: !Req + A_send_ack)
│       │   └── approval_ui.spthy      # ✅ APPROVE_REQ UI phase (Experiment 02: !Session, self/injected prompts)
│       └── experiments/               #   lemmas only, ceremony-specific
│           ├── 00_baseline.spthy  # ✅ L0_*
│           ├── 01_busy_under_load.spthy   # ✅ L1_*
│           ├── 02_habituated_mfa.spthy # ✅ L2_*
│           └── 03_careless_distraction.spthy # ✅ L3_*
│   └── <next_ceremony>/               # ⬜ reuses all of core/ unchanged
└── README.md                          # ⬜ (top-level; per-ceremony README exists)
```

**Entry point & includes.** There is **one entry-point theory per experiment** (not a single `ceremony.spthy`), because the experiments differ in their msg-3 protocol rules. Each entry `#include`s the shared `ceremony.base.spthy` (core types + init + Msg1/Msg2), then only its **deltas** — the mask/stressor/transition it exercises (from `../../core/`), its `protocol/msg3_*` variant, and its experiment. `#include` resolves **relative to the including file** (nested includes work: an entry → `base` → `../../core/...` + `protocol/...`), and an experiment may include a fragment only if the assembly stays *closed* (the wellformedness note below). Run with `check.py --prove NN_<name>.spthy`. The actual Experiment 02 entry:

```
theory ToyCeremony_HabituatedMFA begin
  #include "ceremony.base.spthy"                                  // core types + init + Msg1/Msg2
  #include "../../core/masks/attentive_approve.spthy"
  #include "../../core/masks/habituated_approve.spthy"
  #include "../../core/stressors/habituation.spthy"               // sigma8 trigger emits SetMask 'Habituated'
  #include "../../core/transitions/mask_state.spthy"              // current-mask gates
  #include "../../core/transitions/answered_once.spthy"
  #include "protocol/msg3_inline.spthy"
  #include "protocol/session.spthy"
  #include "protocol/approval_ui.spthy"
  #include "experiments/02_habituated_mfa.spthy"
end
```

The entry reads as a manifest of what the experiment *is*: spine + deltas. *(Directory-mode `tamarin-prover interactive ceremonies/alex_blake_kdf/` lists exactly the four `ToyCeremony_*` theories (`Baseline`, `BusyUnderLoad`, `HabituatedMFA`, `CarelessDistraction`); `ceremony.base.spthy` and the `protocol/` fragments are pulled in via `#include`, not listed as broken theories.)*

**How to add things — each touches one predictable place:**

| To add… | Create / edit | Touches `core/`? | Touches ceremonies? |
|---|---|---|---|
| a **mask** *(behavior for an action it degrades)* | new `core/masks/<mask>_<actiongroup>.spthy` per action group | +1 file each | include line in each experiment using it |
| a **stressor + its transition** | new file in `core/stressors/` (trigger rule that emits `SetMask(P,m)` at onset + a once-bound) — the `f_M` edge lives *in the trigger*; the shared `mask_state.spthy` gates do the rest | +1 file | include line only |
| a **mitigation** *(⬜)* | a protocol step emitting a recovery `SetMask(P,'Attentive')` (cf. `protocol/warning_ui.spthy`); the general `core/mitigations.spthy` exists (shutout); add restrictions there | +0–1 file | +1 protocol file |
| an **experiment** | new file in that ceremony's `experiments/` | no | +1 file |
| a whole **new ceremony** | new folder under `ceremonies/` (init, messages, msg3 variant, entry, experiments) | **none** | +1 folder |
| a new **action type** | one `<mask>_<newaction>.spthy` per participating mask + a request/advance rule in the ceremony | +1 file/mask | request + UI rule |

**Naming conventions** (keep grep-able):
- Mask f_H rules: `<Action>_<Mask>[_<outcome>]` — e.g. `Calc_Attentive`, `Calc_Busy_slip`, `Approve_Habituated`. Files: `<mask>_<actiongroup>.spthy`.
- Stressor rules: `Trigger_<StressorName>`; files `core/stressors/<snake_case>.spthy`.
- Transitions: in the **current-mask** style an `f_M` edge is its **stressor trigger emitting `SetMask(P,m)`** at onset (rule `Trigger_<Stressor>` / `Detect_<Stressor>`); the shared gates live in `core/transitions/mask_state.spthy`. There are no per-edge `from_*` files and no separate `recovery.spthy` — recovery is a step emitting `SetMask(P,'Attentive')`.

> **Wellformedness constraint (the reason files are action-scoped).** Tamarin rejects a theory in which a rule's left-hand-side fact is never produced by any right-hand side (`WELL-FORMEDNESS FAILED: Facts occur in the LHS but not in any RHS`) — it is a hard failure, not a warning, so `check.py` exits 1. Therefore **every assembled experiment must be *closed***: it may include a mask file only if it also provides that file's premises. A single per-mask file holding both `Calc_*` (needs `!Req`) and `Approve_*` (needs `!Prompt`) would force *every* including experiment to supply *both* action types. Splitting `f_H` by **(mask × action group)** keeps each fragment's premises tied to one action type, so an experiment includes exactly what it can close. The cost — a mask's behavior spans several files — is the price of §6.1 minimal-profile includes under this constraint, and is the deliberate inversion of the earlier "one file per mask" guidance.

**Scaffolding the layout — ✅ done.** The tree above is built (Experiments 0–3). Growth from here is purely additive: a new construct is a new fragment file plus its include line in a new (or existing) `NN_<name>.spthy` entry (each entry = `ceremony.base.spthy` + deltas); re-run all `L*` lemmas via `check.py --prove` after any change touching a shared file (`ceremony.base`, `protocol/*`, or a reused `core/` fragment) to confirm no regression. The per-ceremony `README.md` carries the experiment index and an "adding an experiment" checklist.
