# Plan: Extending Usability Stressors, Mask Transitions, and Masks

> **Scope.** Deliverables for the Ceremony Mask framework (the repo is **greenfield** — see §0):
> 0. **First toy ceremony + bootstrap slice (new — start here).** A concrete `alex_blake_kdf` ceremony (§C0) plus a vertical-slice build/test plan (§Phase 0) that proves *one stressor → one transition → one broken property* end-to-end **before** any breadth is added.
> 1. **Masks to review** — user-centered descriptions + precise behavioral signatures, reconciled with the HCI literature (Norman, Cranor).
> 2. **New stressors** — an empirically grounded catalogue (toward σ₁…σ₁₀) and *how* each is triggered (`f_U`).
> 3. **New mask transitions** — building out the `f_M` graph (reaching the unimplemented masks, chained degradation, habituation escalation, recovery).
>
> **Sources.** This iteration is grounded in the supplied research report *"Falhas de Usabilidade na Arquitetura de Segurança"* (Norman's error taxonomy; Whitten & Tygar's five properties; Cranor's Human-in-the-Loop / C-HIP; Ka-Ping Yee's 10 guidelines; Poka-Yoke; and six case studies: PGP/Mailvelope, MFA fatigue, AWS S3, clinical EHR workarounds, Shadow AI, warning habituation). The earlier draft's structure is kept; each construct below now carries its literature anchor.

---

## 0. Current state — greenfield (2026-06-22)

> **Reality check.** This working directory contains **only two design documents** — `mask_machinery_formalization.md` (the machinery) and this plan. There is **no Tamarin/Coq code yet**: none of the `.spthy` files named in this document exist on disk. The table below is therefore the *target* decomposition we are about to build, **not** an inventory of what runs today. (Earlier drafts of this plan were written as if a flat baseline already existed and merely needed refactoring; every "implemented today / *(exists)* / migrate the existing files" claim has been corrected to reflect the greenfield reality. The build order starts at **Phase 0** below, not at a refactor of nonexistent code.)

| Layer | Target file (Appendix A layout) | v1 scope — built in Phase 0 | Deferred (Phase 1, §1–§9) |
|---|---|---|---|
| Masks (`f_H`) | `core/masks/*.spthy` | `Attentive`, `Busy` | `Careless`, `Fearful`, `Naive`, `Elder`, `Habituated` |
| Stressors (`f_U`) | `core/stressors/*.spthy` | σ₁ `HighCognitiveLoad` | σ₂…σ₁₀ |
| Transitions (`f_M`) | `core/transitions/*.spthy` | **1 edge:** Attentive→Busy | edges into new masks; chaining; escalation; recovery |
| Outcomes | `core/types.spthy` | `kdf` (valid), `slip` | `mistake` / `bypass` / `auto_approve` / `timeout` / `withdrawal` |
| Action types | ceremony `requests.spthy` | `GEN_NONCE`, `CALC_SK`, `SEND_MSG` | `APPROVE_REQ`, `SET_POLICY`, `VERIFY_KEY` |
| Ceremony (𝒫) | `ceremonies/alex_blake_kdf/` | the toy ceremony **C0** (§C0) | further ceremonies |
| Experiments | `…/experiments/` | the Phase-0 slice lemmas (`L0_*`, `L1_*`) | one file per phenomenon (§9) |

Nothing here exists yet — so the first task is not to *extend* the model but to *bring up* its smallest runnable form (§Phase 0).

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
- **Channel/secrecy caveat (state it explicitly in `ceremony.spthy`).** Because $N_A, N_B$ travel in cleartext, a Dolev–Yao adversary on the wire can also compute $kdf(N_A,N_B)$ — so **SK-secrecy does *not* hold for the bare toy** and is deliberately **not** a baseline lemma. The upstream toy protects key material with asymmetric encryption; adding a confidential channel (or that encryption) is a *later* slice. For the usability study we center on **Agreement + Liveness**, which are exactly what masks degrade.
- **Usability Liveness** (formalization §5): all-`Attentive` ⇒ `Done` reachable with agreement.
- **Protocol Vulnerability** (formalization §5): a `Busy` `CALC_SK` ⇒ no correct $SK$ / agreement broken.

---

## Phase 0. Bootstrap — prove the machinery on the smallest slice first

> **Why this precedes §1–§10.** The repo is greenfield (§0). The grand plan builds *breadth* — all outcomes, 7 masks, 10 stressors, the `core/`+`ceremonies/` split. But you cannot refactor or regression-test what does not exist, so the lowest-risk path is a **vertical slice**: one end-to-end causal chain — *one stressor → one transition → one degraded action → one broken property* — proved in Tamarin before any breadth is added. The slice de-risks the modeling idiom **and** becomes the regression anchor that every later step must keep green.

**The unit of progress is a "slice."** Each slice is independently provable and adds *exactly one* construct plus the lemmas that test it. The test vocabulary — what "green" means in a prover — has three kinds:

- **sanity (`exists-trace`)** — the intended honest trace is reachable. Guards against an over-constrained model that proves safety *vacuously*. **Every slice needs at least one.**
- **failure-reachability (`exists-trace`)** — the new *bad* chain can actually happen.
- **safety / control (`all-traces`)** — the bad outcome is bounded (only via the stressor; never under the mitigation).

> The Tamarin fragments below are **design targets** written in Tamarin-ish syntax to make the slice unambiguous; none is claimed proven. Each must be validated with `tamarin-prover … --prove` (no `sorry`, no hand-fed `oracle`) as it is written.

### Slice 0 — Walking skeleton (ceremony + `Attentive` only, no stressors)

Smallest runnable theory: the protocol layer + happy path compile and prove, establishing the baseline the failures will perturb. **Resist adding any stressor, transition, or second mask here.**

```
theory ToyCeremony_Slice0 begin
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

### Slice 1 — One stressor + one transition (the headline loop)

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

**Minimal payload:** only a `complexity` field (`'Hard'`) is needed now — **not** §6's full six-field `flags` tuple. §6's enrichment is deferred until a *second* flag-keyed stressor needs it; the slice proves the mechanism with one field.

**The slice's test suite** — five lemmas that map 1:1 onto the formalization's three formal properties plus the §2 safe-fail/unsafe-success distinction:

| Lemma | Kind | Asserts | Machinery tie |
|---|---|---|---|
| `L1_attentive_ok` | `exists-trace` | `Calc(p,'Attentive') & Key(p,k)` — happy path still alive (no Slice-0 regression) | Liveness |
| `L1_load_causes_slip` | `exists-trace` | `Load@s ⇒ Mask(Attentive,Busy)@m ⇒ Slip@o`, `#s<#m<#o` — failure chain reachable | feedback-loop §4 |
| `L1_unsafe_completion` | `exists-trace` | `Finish('Alex')` reachable with `Key('Alex',ka) & Key('Blake',kb) & not(ka=kb)` — completes **wrongly**, not a safe stall | §2 unsafe-success |
| `L1_stressor_causality` | `all-traces` | every `Mask(_,'Attentive','Busy')@m` has a prior `Load@s, #s<#m` | Safety: Stressor Causality |
| `L1_busy_no_correct_key` | `all-traces` | `Calc(p,'Busy') & Key(p,k) ⇒ not(Ex a b. k=kdf(a,b))` (holds structurally: `~wrong` is fresh) | Protocol Vulnerability |

```
lemma L1_attentive_ok:        // sanity: happy path survives (no Slice-0 regression)
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

**This one slice already exercises every machinery layer** — $\mathcal{P}$ (the steps), $\mathcal{U}$ ($f_U$ = `Trigger_HighCognitiveLoad`), $\mathcal{H}/f_M$ (the `MaskShift` edge), $f_H$ (degraded `Calc_Busy_slip`), and $\mathcal{N}$ (the `Out`/`In` wire). That is exactly why it is the right first thing to build: it is the minimum that touches the whole model.

> **Encoding note — stored mask is a Phase-0 convenience.** The fragments above carry the mask as a *stored* linear fact (`St_H(P,'Busy')`) and flip it with a `MaskShift` rule. This is fine and clearer at two masks, but it is the **stored-mask style §6a rule 1 (and machinery §6.2) argues against**: every persisted mask value is an independent state dimension ($\times|M|$), and the explicit `MaskShift` step adds an interleaving. Once a profile uses ≥3 masks or chained transitions, **migrate to the action-label style**: drop `St_H`/`MaskShift`, keep only the monotone `!Stressor(P,σ)` facts, and let `f_H` *derive* the mask from the active stressor at response time (emitting `Mask(P,'Attentive','Busy')` as an action fact for the lemmas, not a state fact). The `L1_*` lemmas are written against the `Mask(...)`/`Slip(...)`/`Key(...)` **action facts**, so they survive that refactor unchanged — which is the point of fixing it before masks multiply, not after.

### After the slice — how to grow (re-entry into the grand plan)

Each later construct is "one more slice," reusing the same three-kind test ladder:

- **Slice 2** — first *failure + mitigation* pair: σ₈ `Habituation` → `Habituated` → `auto_approve`, then number-matching `shutout` neutralizes it (one `exists-trace` failure lemma + one `all-traces` mitigation lemma). `APPROVE_REQ` enters here.
- **Slice 3** — **Pathway B**: terminology-driven `mistake` emitted by **Attentive** with *no* transition — proves the second failure pathway (§1).
- **Slice 4+** — drive out the remaining masks/stressors per §3–§5, each as a failure/mitigation lemma pair drawn from §8's case-study table.
- **Only once ≥2 stressors share flag-reading** do §6's payload enrichment and Appendix A's `core/`+`ceremonies/` split pay for themselves — i.e. the reorg happens *after* the slices prove the seams, **not** before. (This inverts the old sequencing, which assumed an existing flat model to migrate; see §10.)

---

## 1. Theoretical grounding → model constructs

This is the bridge: each HCI framework maps to a concrete object in the Tamarin model.

| Literature | Core idea | Becomes in the model |
|---|---|---|
| **Norman — Slip** | correct intent, failed execution (distraction, automaticity) | outcome `slip()`; produced by Busy/Careless/Elder under load |
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
- **Pathway B — task-mediated mistake** (S3 terminology, PGP key metaphor): `f_H` reads a request flag (`terminology='Misleading'`, `feedback='None'`) and produces `mistake()` **even for Attentive**, with no `MaskChanged`. Reuses the payload-flag mechanism in §6.

---

## 2. Outcome vocabulary (refine `types.spthy`)

The single most important enrichment. The Slice-1 outcome set (§Phase 0) is just `kdf` (valid) and `slip`; everything below is the *target* vocabulary, **not yet built**. Proposed outcome set, each with a `UsabilityFailure` reason label:

| Outcome value | Reason label | Meaning | Norman/literature | Case study |
|---|---|---|---|---|
| valid (`~n`,`kdf`,`data`) | — | task done as designed | — | — |
| `slip()` | `'Slip'` | correct intent, wrong execution | Norman slip | — |
| `mistake()` | `'Mistake'` | confident wrong action, wrong mental model | Norman mistake | S3 "Any Authenticated Users" |
| `bypass()` | `'Bypass'` | deliberately circumvents the control to finish the primary task | Unmotivated / workaround | EHR sticky-notes, Shadow AI |
| `auto_approve()` | `'HabituatedApproval'` | reflexive "yes" without reading | habituation / RS | MFA prompt-bombing, warning fatigue |
| `timeout()` | `'Timeout'` | disengages / gives up | — | — |
| `abort()` | `'Withdrawal'` | refuses to continue (distrust) | — | Fearful |

`mistake()`, `bypass()`, and `auto_approve()` are the dangerous ones: unlike `timeout`, they let the ceremony *proceed* with a compromised result — which is precisely how the real-world incidents broke security. Lemmas should distinguish "ceremony stalls (safe-fail)" from "ceremony completes wrongly (unsafe-success)".

---

## 3. Masks to review (user-centered + reconciled with Cranor)

Cranor's four honest-user types map cleanly onto the masks; the mapping both validates the set and reveals one gap (**Habituated**).

| Cranor type | Mask | Fit |
|---|---|---|
| Clueless (unaware action is security-relevant) | **Naive** | strong |
| Cognitively-limited (motivated, capable, but memory/complexity-bound) | **Elder** (+ Busy under load) | strong — reframes Elder as *cognitive-barrier*, not age per se |
| Unmotivated (knows, but friction not worth it) | **Careless** (+ proposed split) | partial — see Habituated/bypass |
| Malicious | — | out of scope (honest-but-erring model) |

### Behavioral signature matrix (target design)

Outcomes per `f_H(mask, action)`. New action types `APPROVE_REQ` (push/MFA), `SET_POLICY` (config) added (§6).

| Mask | GEN_NONCE | CALC_SK (hard) | SEND_MSG | APPROVE_REQ | SET_POLICY | User-centered description |
|---|---|---|---|---|---|---|
| **Attentive** | valid | valid | valid | valid (verifies) | valid *if* terminology clear, else `mistake` (Pathway B) | "I read each step, double-check, and finish as intended." |
| **Busy** | `slip` | `slip` | valid | `auto_approve` | `bypass` | "Short on time, I skim and act fast — that's when I slip, or work around the control to keep moving." |
| **Careless** | `timeout` | `timeout` | `timeout` | `auto_approve` | `bypass` | "I don't engage with security; I skip, dismiss, or take the shortcut." |
| **Fearful** *(new)* | valid (slow) | `abort`/`timeout` | `abort` on sensitive sends | `abort` (rejects all, even valid) | `abort` | "I don't trust this; on anything security-critical I hesitate, back out, or refuse." |
| **Naive** *(new)* | valid *iff* guided | `mistake` (no mental model) | valid (follows literally) | `auto_approve` (doesn't grasp the risk) | `mistake` | "I'm new; I do exactly what the screen says and I'm lost the moment a step assumes knowledge I lack." |
| **Elder** *(new)* | valid *iff* untimed | `slip`/`timeout` under pace | valid untimed, `timeout` rushed | valid (slow) | `mistake` | "Careful when unhurried; dense or fast steps cause slips and missed deadlines." |
| **Habituated** *(new, from research)* | valid | valid | valid | **`auto_approve`** (reflexive yes) | valid | "I've seen this prompt a hundred times; I click through without reading to make it stop." |

**On `Habituated`** — empirically the strongest single addition the research supports (BYU fMRI repetition-suppression; MFA fatigue at Uber/Cisco/MGM). It is *not* Careless: the Careless user disengages (`timeout`), the Habituated user **actively approves** (`auto_approve`) — the exact behavior that prompt-bombing weaponizes. Recommend adding it as mask #7.

**Optional split — `Unmotivated`/`Pragmatic`** (Shadow AI, clinical workarounds): a user who *understands* the control but routes around it (`bypass`). Folded into Busy/Careless in the target matrix. Decide in §11 whether it warrants its own mask.

---

## 4. New stressors — what to model and how (`f_U`)

Literature-grounded catalogue. Shared implementation pattern (the same shape as the Phase-0 `Trigger_HighCognitiveLoad` rule): fire on a condition, emit `UsabilityProblem`, deposit `!ActiveStressor`, copy (don't consume) `HumanState`/`ProtocolRequest`.

| # | Stressor | Trigger (`f_U`) | Anchor | Feeds → |
|---|---|---|---|---|
| σ₁ | `HighCognitiveLoad` **(Slice 1)** | `CALC_SK` request, `complexity='Hard'` | Abstraction | Attentive→Busy |
| σ₂ | `ExternalDistraction` | unconditional | Norman slip | Attentive→Careless |
| σ₃ | `TimePressure` | request carries deadline marker | EHR workarounds | Attentive→Busy, Elder→error |
| σ₄ | `MisleadingTerminology` | request flag `terminology='Misleading'` | S3 case | **Pathway B** mistake (any mask) |
| σ₅ | `LackOfFeedback` | request flag `feedback='None'` | Whitten #3, PGP9 | Pathway B mistake; Gulf of Evaluation |
| σ₆ | `Abstraction` | request flag `concept='Abstract'` (key metaphor) | Whitten #2, PGP | Attentive→Naive; HighCognitiveLoad |
| σ₇ | `SecondaryTask` | participant has a competing primary-task fact | Whitten #1, Shadow AI | →bypass (Busy/Careless) |
| σ₈ | `Habituation` | **N≥2 identical prior `APPROVE_REQ`** (history-keyed; assert in lemma) | BYU RS; MFA fatigue | Attentive→Habituated |
| σ₉ | `AlertVolume`/`DecisionFatigue` | ≥k requests within the trace before a `Step` | MFA prompt-bombing | →Habituated/Careless |
| σ₁₀ | `RepeatedFailure` | a prior `UsabilityFailure` exists earlier | — | Busy→Careless; Fearful→abandon |

**Three trigger flavours** (carry over from prior draft):
1. **Type-keyed** (σ₁): trivial — match request type.
2. **Flag-keyed** (σ₃–σ₇): needs the payload enrichment in §6. Unlocks five stressors at once.
3. **History-keyed** (σ₈, σ₉, σ₁₀): the causal ordering lives in the **lemma** (`#i < #j`), not the rule LHS — the rule deposits the stressor; the experiment asserts the chain. Document this so authors don't try to encode history in the multiset LHS.

**First stressors to implement:** σ₈ `Habituation` (the headline result, motivates Habituated + the MFA experiment), σ₄ `MisleadingTerminology` (cleanest demonstration of Pathway B), σ₃ `TimePressure` (drives Busy/Elder).

---

## 5. New mask transitions (`f_M` graph)

```
  Attentive ──Abstraction/UnclearInstr──▶ Naive ──RepeatedFailure──▶ Fearful
     │ │ │ │                                │                          │
     │ │ │ └─SecurityAnxiety/LowTrust──────▶ Fearful                   │ (terminal:
     │ │ └───CogLoad/TimePressure──────────▶ Busy                      │  abort/timeout)
     │ └─────Distraction───────────────────▶ Careless ◀──RepeatedFailure─┘
     └───────Habituation (N≥2 prompts)─────▶ Habituated ──(more prompts)──▶ auto_approve

  Trait start states (init.spthy):  Naive · Elder · (Fearful)
  Elder ──TimePressure/StepDensity──▶ Fearful

  RECOVERY (new direction, via Poka-Yoke / Yee — §7):
  Habituated ──NumberMatching (shutout)──▶ Attentive   (re-engagement forced)
  Fearful    ──TrustedPath + clear feedback──▶ Attentive
  Naive      ──Guidance repeated / success───▶ Attentive
```

| Source | Condition | Target | Rationale / anchor |
|---|---|---|---|
| Attentive | `HighCognitiveLoad` **(Slice 1)** | Busy | — |
| Attentive | `ExternalDistraction` | Careless | — |
| Attentive | `TimePressure` | Busy | EHR |
| Attentive | `Abstraction`/`MisleadingTerminology` | Naive | PGP key metaphor |
| Attentive | `SecurityAnxiety` | Fearful | low trust |
| Attentive | `Habituation` (N≥2) | **Habituated** | BYU / MFA fatigue |
| Naive | `RepeatedFailure` | Fearful | confusion → withdrawal |
| Elder | `TimePressure`/`StepDensity` | Fearful | pace pressure |
| Busy | `RepeatedFailure` | Careless | errors → disengagement |
| Habituated | more prompts | (terminal `auto_approve`) | prompt-bombing payoff |
| Naive / Fearful / Habituated | **recovery condition** | Attentive | mitigations work (§7) |

**Mechanics:** one rule per row; consume linear `HumanState`, require persistent `!ActiveStressor`, emit `MaskChanged`. **Recovery** edges consume a positive `!Mitigation(id, kind)` fact (symmetric with stressors — keeps the system monotone; avoids LHS negation). **Trait start states:** parameterize `init.spthy` so an experiment can start a participant as Elder/Naive. **Branching caution:** multiple enabled transitions out of one `HumanState` make Tamarin explore all paths — desirable for worst-case discovery, but keep per-experiment stressor sets small to bound proof search (the profile/state-space discipline is spelled out in §6a).

---

## 6. Cross-cutting prerequisite: enrich the request payload

Pathway B, five stressors, and the guidance-conditional masks all depend on `f_H`/`f_U` being able to read properties of the request. The base `ProtocolRequest(id, rid, type, data)` carries only opaque `data`; Slice 1 (§Phase 0) already adds a single standalone `complexity` arg, and this section folds that — plus the rest — into one `flags` tuple.

**Proposed:** `ProtocolRequest(id, rid, type, <data, flags>)` with
`flags = <complexity, guidance, feedback, terminology, sensitivity, pokayoke>`
(constants like `'Hard'/'Easy'`, `'Guided'/'Bare'`, `'Visible'/'None'`, `'Clear'/'Misleading'`, `'Sensitive'/'Normal'`, `'none'/'warning'/'shutdown'/'shutout'`).

- **Set** in `protocol_requests.spthy` — the designer's choices become explicit and auditable (this *is* the Yee/Poka-Yoke design surface).
- **Read** by `f_U` (flag-keyed stressors) and `f_H` (guidance-conditional outcomes, Pathway-B mistakes).
- **Cost:** touches every rule matching `ProtocolRequest`. Do it as one mechanical refactor **once a second flag-keyed stressor needs it** (not before — see §10's re-sequencing); re-run the Phase-0 slice lemmas (`L0_*`, `L1_*`) to confirm no regression.

New **action types** to add alongside (each = one request rule + one advance rule + one `f_H` row per mask): `APPROVE_REQ` (MFA push), `SET_POLICY` (S3-style config), `VERIFY_KEY` (PGP key-signing metaphor).

---

## 6a. State-space discipline — composable experiment profiles (avoid explosion)

> **The constraint that makes the breadth above tractable.** The construct menu (7 masks, 10 stressors, chained transitions, mitigations) is a *catalogue*, not a single model to instantiate at once. Modeled naïvely, one participant's human state $\langle M, \Sigma\rangle$ with $\Sigma \subseteq \{\sigma_1..\sigma_{10}\}$ is a powerset — $6{,}144$ states per human, $6{,}144^{N}$ for $N$ participants — and Tamarin will not terminate. This section is the rule that keeps every slice (§Phase 0, §9) provable. Formalized in `mask_machinery_formalization.md` §6.

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
| 5 | **Per-slice, one human** — prove §5's vulnerability on each $\langle$1 mask, 1 stressor$\rangle$ slice under a single honest stressed party; orthogonal slices compose **additively**. | $\sum_k|\text{slice}_k|$ not $\prod_k 2^{|\mathcal S_{\sigma,k}|}$ | one experiment file per phenomenon (§9) |

**Consequence for sequencing.** Adding a mask or stressor to the *catalogue* never enlarges an existing slice — it is a *new* profile (new include set, new experiment file). This is why Phase-1 steps parallelize (§10) and why the `core/`+`ceremonies/` split (Appendix A) pays off: includes *are* the profile selector. Keep $|\mathcal{S}_\sigma|$ per experiment small (ideally 1–2); a worst-case-discovery experiment that deliberately enables several stressors at once must `log`/comment the expected blow-up and run on the single-human, monotone encoding only.

---

## 7. Mitigations as first-class (Yee + Poka-Yoke)

The research is as much about *fixes* as failures. Modeling mitigations lets experiments verify **"does this design change neutralize this mask?"** — far more valuable than only demonstrating failure.

**Poka-Yoke levels** (the `pokayoke` flag) constrain `f_H` outputs:
- `shutout` (Control) — protocol rejects a malformed/unverified input, so even a bad mask **cannot** emit a bad outcome. *Number-matching MFA = shutout: the Habituated user can't `auto_approve` because approval now requires a value only an engaged user can supply.*
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

One self-contained file per phenomenon (lemmas only, mirroring the Phase-0 slice lemmas; an `exists-trace` for the failure + an `all-traces` for the mitigation):

| File | Demonstrates |
|---|---|
| `exp_mfa_fatigue.spthy` | repeated `APPROVE_REQ` → Habituation → Habituated → `auto_approve`; number-matching shutout neutralizes it |
| `exp_s3_mistake.spthy` | misleading terminology → **Attentive** still emits `mistake` (Pathway B); clear terminology / shutdown prevents it |
| `exp_pgp_naive.spthy` | bare/abstract `VERIFY_KEY` → Naive → `mistake`; guided request keeps Naive correct |
| `exp_ehr_workaround.spthy` | TimePressure + SecondaryTask → Busy → `bypass`; path-of-least-resistance removes the incentive |
| `exp_warning_habituation.spthy` | warning effectiveness decays with repetition; polymorphic warning resists |
| `exp_elder_pace.spthy` | untimed Elder succeeds; under TimePressure fails (pace, not capability) |
| `exp_cascade.spthy` | Attentive→Busy→(RepeatedFailure)→Careless |
| `exp_recovery.spthy` | Fearful/Naive/Habituated → Attentive via `!Mitigation` |

---

## 10. Suggested sequencing

> **Greenfield ordering.** There is nothing to migrate, so the build starts with the **vertical slice** and grows breadth afterward. The old "reorg/refactor first" ordering assumed an existing flat model; on a greenfield it is inverted — scaffold the `core/`+`ceremonies/` layout (Appendix A) and do the payload refactor (§6) only once ≥2 slices justify the seams.

**Phase 0 — Bootstrap (do first; see §Phase 0).**
- **0a. Slice 0** — walking skeleton: toy ceremony C0 + `Attentive`-only; prove `L0_completes` + `L0_agreement`.
- **0b. Slice 1** — σ₁ `HighCognitiveLoad` + Attentive→Busy + Busy `slip`; prove the five `L1_*` lemmas. *The smallest end-to-end test of the machinery.*

**Phase 1 — Breadth (each step = a failure/mitigation lemma pair, reusing the slice idiom).**
1. **Outcome vocabulary (§2)** — add `mistake`/`bypass`/`auto_approve` constants + reason labels; activate `abort`/`withdrawal`.
2. **Mask-signature spec (§3)** — lock the `f_H` matrix as spec; add **Habituated**.
3. **Habituated + MFA** — σ₈, Attentive→Habituated, `APPROVE_REQ`, shutout recovery, `exp_mfa_fatigue`. *(Highest-impact, fully grounded.)*
4. **Pathway B + S3** — σ₄/σ₅, terminology-driven `mistake` in `f_H`, `SET_POLICY`, `exp_s3_mistake`.
5. **Naive / Elder / Fearful** — guidance/pace-conditional actions, trait start states, σ₃/σ₆, their experiments.
6. **Chaining & recovery** — σ₁₀, Busy→Careless, `!Mitigation` recovery, `exp_cascade` + `exp_recovery`.
7. **Payload enrichment (§6) + `core/`/`ceremonies/` reorg (Appendix A)** — once ≥2 flag-keyed stressors share the mechanism; re-run all prior `L*`/`exp_*` lemmas as regression. *(Deferred on purpose — the seams pay off only here.)*
8. **Remaining stressors / cases** (Shadow AI bypass, warning polymorphism) as needed.

Each step is independently provable (`tamarin-prover ceremonies/alex_blake_kdf/ceremony.spthy --prove`) and respects the module seams; Phase-1 steps parallelize once Phase 0 is green.

---

## 11. Decisions needed before coding

0. **Bootstrap entry point + channel assumption** — confirm the toy ceremony **C0** and the Phase-0 vertical slice (Slice 0 → Slice 1) as the first build, *before* any breadth (§Phase 0, §10). And confirm the channel model for C0: run the nonce exchange over a Dolev–Yao wire and prove **Agreement + Liveness** (*not* SK-secrecy — see §C0 caveat), or add a confidential channel now to also obtain secrecy? *(Recommended: defer secrecy; keep the toy minimal so the usability failures stay the focus.)*
1. **Outcome set** — adopt the six-outcome vocabulary in §2 (slip/mistake/bypass/auto_approve/timeout/withdrawal)? Any merges?
2. **Pathway B** — accept that some failures (mistakes) occur **without** a mask change, read directly from request flags in `f_H`? This is the biggest architectural shift.
3. **Add `Habituated` as mask #7?** (Strongly recommended by the research.) And split out `Unmotivated`, or fold bypass into Busy/Careless?
4. **Mitigations first-class** — model Poka-Yoke/Yee as protective flags + `!Mitigation` recovery, or keep the framework purely degradational for v1?
5. **Trait start states** — confirm Naive/Elder become selectable initial masks in `init.spthy`.

---

## Appendix A. Repository layout for multiple ceremonies

**Guiding principle — two layers, two folders.** The human layer (masks, stressors, transitions, mitigations, outcomes) is *ceremony-agnostic*: it is written once and reused verbatim. The protocol layer (who the participants are, what requests they issue, how the state advances, what to prove) is *ceremony-specific*. Keep them in separate trees so that **adding a new ceremony touches zero files under `core/`.**

This works because action *types* are a small, shared **interface** (`GEN_NONCE`, `CALC_SK`, `SEND_MSG`, `APPROVE_REQ`, `SET_POLICY`, `VERIFY_KEY`…). Every mask defines its response to each type once, in `core/`; a ceremony is then just protocol logic that emits requests of those standard types. New ceremonies pick from the existing vocabulary; only a genuinely new kind of human action requires extending the interface (and then one block per mask).

```
tamarin_model/
├── core/                         # HUMAN LAYER — reusable across all ceremonies
│   ├── types.spthy               #   crypto fns, restrictions, fact inventory, OUTCOME constants (§2)
│   ├── masks/                    #   f_H — one file per mask, all action types inside
│   │   ├── attentive.spthy
│   │   ├── busy.spthy
│   │   ├── careless.spthy
│   │   ├── fearful.spthy
│   │   ├── naive.spthy
│   │   ├── elder.spthy
│   │   └── habituated.spthy
│   ├── stressors/                #   f_U — one file per stressor (one trigger rule each)
│   │   ├── cognitive_load.spthy
│   │   ├── external_distraction.spthy
│   │   ├── time_pressure.spthy
│   │   ├── misleading_terminology.spthy
│   │   ├── habituation.spthy
│   │   └── …
│   ├── transitions/              #   f_M — grouped by source mask + recovery
│   │   ├── from_attentive.spthy
│   │   ├── from_naive.spthy
│   │   ├── chaining.spthy        #   Busy→Careless, Naive→Fearful, …
│   │   └── recovery.spthy        #   *→Attentive via !Mitigation (§7)
│   └── mitigations.spthy         #   Poka-Yoke / Yee protective triggers (§7)
│
├── ceremonies/                   # PROTOCOL LAYER — one folder per ceremony
│   └── alex_blake_kdf/           #   the toy ceremony C0 (§C0): SK = kdf(N_A, N_B)
│       ├── init.spthy            #     participant init + chosen start masks
│       ├── requests.spthy        #     protocol_requests (emits standard action types)
│       ├── advance.spthy         #     protocol_advance
│       ├── ceremony.spthy        #     ENTRY POINT — includes core/* + this ceremony + experiments
│       └── experiments/          #     lemmas only, ceremony-specific
│           ├── slice0_skeleton.spthy  #  Phase 0 · L0_* (Attentive walking skeleton)
│           ├── slice1_cogload.spthy   #  Phase 0 · L1_* (one stressor + one transition)
│           └── exp_mfa_fatigue.spthy  #  Phase 1 · §9 phenomena …
│   └── <next_ceremony>/          #   reuses all of core/ unchanged
│       └── …
└── README.md                     # the map: layer principle + how-to-add table below
```

**Entry point & includes.** Each ceremony has its own top theory file (`ceremony.spthy`) that `#include`s the core modules, its own protocol files, then the experiments it wants. Run a ceremony with `tamarin-prover ceremonies/alex_blake_kdf/ceremony.spthy --prove`. Tamarin resolves `#include` **relative to the including file**, so core modules are reached as `../../core/...`:

```
theory AlexBlakeKDF begin
  #include "../../core/types.spthy"
  #include "../../core/masks/attentive.spthy"   // … one line per mask in use
  #include "../../core/stressors/habituation.spthy"
  #include "../../core/transitions/from_attentive.spthy"
  #include "../../core/mitigations.spthy"
  #include "init.spthy"
  #include "requests.spthy"
  #include "advance.spthy"
  #include "experiments/exp_mfa_fatigue.spthy"
end
```

A ceremony includes only the masks/stressors it exercises — this also bounds Tamarin's proof search (fewer enabled transitions = less branching, per §5).

**How to add things — each touches one predictable place:**

| To add… | Create / edit | Touches `core/`? | Touches ceremonies? |
|---|---|---|---|
| a **mask** | new file in `core/masks/`; add its include to each ceremony that uses it | +1 file | include line only |
| a **stressor** | new file in `core/stressors/` | +1 file | include line only |
| a **transition** | a rule in the matching `core/transitions/` file | edit 1 file | no |
| a **mitigation** | a rule in `core/mitigations.spthy` | edit 1 file | no |
| an **experiment** | new file in that ceremony's `experiments/` | no | +1 file |
| a whole **new ceremony** | new folder under `ceremonies/` (init, requests, advance, ceremony, experiments) | **none** | +1 folder |
| a new **action type** (rare) | one rule-block in every `core/masks/*` + a request/advance rule in the ceremony | +1 block/mask | request+advance |

**Naming conventions** (keep grep-able):
- Mask rules: `Action_<Mask>_<TYPE>`.
- Stressor rules: `Trigger_<StressorName>`.
- Transition rules: `MaskShift_<From>_<Stressor>_<To>`; recovery: `Recover_<From>_<Mitigation>`.
- Files lower_snake_case; one stressor/one mask per file matches one concept per file.

**Scaffolding the layout (greenfield — there is nothing to migrate):**
The Phase-0 slices may start life as a *single* `ceremonies/alex_blake_kdf/ceremony.spthy` (skeleton + Slice 1 inline) — do **not** pre-split before the seams are exercised. Grow into the tree above only when Phase-1 step 7 fires:
1. `mkdir -p core/{masks,stressors,transitions} ceremonies/alex_blake_kdf/experiments`.
2. As Slice 0/1 are written, place: crypto + outcome constants → `core/types.spthy`; `Attentive`/`Busy` `f_H` → `core/masks/{attentive,busy}.spthy`; σ₁ → `core/stressors/cognitive_load.spthy`; the Attentive→Busy edge → `core/transitions/from_attentive.spthy`.
3. Ceremony layer → `ceremonies/alex_blake_kdf/{init,requests,advance,ceremony}.spthy`; the `L0_*`/`L1_*` lemmas → `…/experiments/`.
4. `ceremony.spthy` is the entry point; its `#include`s use the `../../core/...` form shown above.
5. Re-run the Phase-0 lemmas after any reorg to confirm it is behavior-preserving **before** adding new constructs.

> **Trade-off noted:** masks are split **by mask** (one file = one persona's full behavior) rather than by action-type. This optimizes for "review everything Naive does" and for adding personas cheaply (+1 file). The cost is that adding a *new action type* edits every mask file — but action types are a near-closed interface, whereas masks and ceremonies are what actually grow, so the axis is chosen to make the common case cheap.
