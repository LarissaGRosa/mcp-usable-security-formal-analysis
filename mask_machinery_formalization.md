# Mathematical Formalization of the Ceremony Mask Machinery

This document defines the **Mask and Usability Machinery** as a formal system of interacting state machines, separating the protocol logic from human cognitive states.

## 1. System Definition

The Ceremony System $\mathcal{S}$ is a tuple:
$$\mathcal{S} = \langle \mathcal{P}, \mathcal{H}, \mathcal{U}, \mathcal{N} \rangle$$

Where:
- $\mathcal{P}$: The **Protocol Layer** (State Machine of rules).
- $\mathcal{H}$: The **Human Layer** (Set of Masks and Stressors).
- $\mathcal{U}$: The **Usability Feedback Loop** (Transition logic).
- $\mathcal{N}$: The **Network/Environment** (Message pool).

## 2. State Spaces

### 2.1 Human State ($S_H$)
The state of a human participant $i$ is defined as:
$$S_{H,i} = \langle M_i, \Sigma_i \rangle$$
- $M_i \in \{ \text{Attentive, Busy, Careless, Fearful, Naive, Elder} \}$: The current **Mask**.
- $\Sigma_i \subseteq \{ \sigma_1, \sigma_2, \dots, \sigma_{10} \}$: The set of active **Security Stressors** (e.g., High Cognitive Load, Time Pressure).

### 2.2 Protocol State ($S_P$)
The protocol state is defined by the sequence of completed steps and active requests:
$$S_P = \langle stage, R \rangle$$
- $stage \in \{ \text{Start, WaitNonce, WaitACK, Done} \}$.
- $R$: A set of active **Requests** $r = \langle type, \text{complexity} \rangle$, where $\text{complexity} \in \{ \text{Easy, Hard} \}$.

## 3. Transition Machinery

### 3.1 Usability Trigger Function ($f_U$)
The usability layer injects stressors into the human state based on the protocol's requests:
$$f_U: (R) \to \Sigma$$
Specifically, if a request $r \in R$ has $\text{complexity} = \text{Hard}$, then:
$$\Sigma_{next} = \Sigma_{current} \cup \{ \text{HighCognitiveLoad} \}$$

### 3.2 Mask Transition Function ($f_M$)
Masks are dynamic and change based on the accumulation of stressors:
$$f_M: (M, \Sigma) \to M$$
Example transition (The "Busy" shift):
$$f_M(\text{Attentive}, \Sigma) = \begin{cases} \text{Busy} & \text{if } \text{HighCognitiveLoad} \in \Sigma \\ \text{Attentive} & \text{otherwise} \end{cases}$$

### 3.3 Human Response Function ($f_H$)
The action performed by the human depends on the current mask and the protocol request:
$$f_H: (M, r) \to Action$$
- $f_H(\text{Attentive}, \text{AskNonce}) = \text{ValidNonce}$
- $f_H(\text{Busy}, \text{AskNonce}) = \text{CorruptedNonce}$
- $f_H(\text{Careless}, \text{AskAction}) = \emptyset$ (No response/Timeout)

## 4. The Feedback Loop Algorithm

The global transition $\Delta$ follows this causal chain:

1. **Protocol Step**: $\mathcal{P}$ moves to $stage_k$ and issues request $r_{hard}$.
2. **Usability Trigger**: $f_U(r_{hard})$ adds $\sigma_{cognition}$ to Human state.
3. **Mask Rotation**: $f_M(M_{attentive}, \sigma_{cognition})$ switches user to $M_{busy}$.
4. **Degraded Response**: $f_H(M_{busy}, r_{next})$ produces an error or skip.
5. **Protocol Outcome**: $\mathcal{P}$ receives error $\to$ Transition to $Stage_{failed}$.

## 5. Formal Properties

- **Liveness (Attentive Completion)**:
  $$\forall s \in \mathcal{S}, \text{Mask}(s) = \text{Attentive} \implies \text{reachable}(\text{Done})$$
- **Safety (Stressor Causality)**:
  $$\forall r \in R, \text{complexity}(r) = \text{Hard} \implies \exists \sigma \in \Sigma$$
- **Protocol Vulnerability**:
  $$\exists \mathcal{P} \text{ such that } \forall s \text{ reachable from } \mathcal{P}, \text{Mask}(s) = \text{Busy} \implies \neg \text{reachable}(\text{Success})$$

## 6. Composable Experiments & Complexity Control

The machinery of §2 is **declared at full breadth** (6+ masks, 10 stressors) but must never be **instantiated** at full breadth: the human state $S_{H,i} = \langle M_i, \Sigma_i \rangle$ with $\Sigma_i \subseteq \{\sigma_1,\dots,\sigma_{10}\}$ is a *powerset*, so a single participant already ranges over $|M| \cdot 2^{10} = 6{,}144$ states, and $N$ participants over $6{,}144^{N}$. This section makes the machinery *composable*: an experiment selects a small subset of masks and stressors, and the state space stays linear in what it actually uses.

### 6.0 Sources of explosion

| Source | In §2 as written | Cost |
|---|---|---|
| Powerset stressor set | $\Sigma_i \subseteq \{\sigma_1,\dots,\sigma_{10}\}$ | $2^{10}$ per human |
| Mask stored beside stressors | $S_{H,i} = \langle M_i, \Sigma_i\rangle$ | $\times |M|$ |
| Multiple humans (product) | $N$ participants | $(\,|M|\cdot 2^{|\Sigma|}\,)^{N}$ |
| Reversible transitions | $f_M$ bidirectional, $\Sigma$ add/remove | cycles ⇒ no partial-order pruning |

The powerset and the product over humans dominate; the rest is secondary.

### 6.1 Experiment profiles (parameterization)

An **experiment** is not the whole system $\mathcal{S}$ but a *profile* that restricts it:
$$\mathcal{E} = \langle\, C,\ \mathcal{M},\ \mathcal{S}_\sigma \,\rangle, \qquad \mathcal{M} \subseteq \text{Masks},\ \ \mathcal{S}_\sigma \subseteq \{\sigma_1,\dots,\sigma_{10}\}$$
where $C$ is one concrete ceremony hosting $\mathcal{P}$. The machinery is **parameterized over** $\mathcal{E}$: only the masks in $\mathcal{M}$, the stressors in $\mathcal{S}_\sigma$, and the $f_M$ edges *between members of $\mathcal{M}$ triggered by members of $\mathcal{S}_\sigma$* are instantiated. The "full" machinery is the union $\bigcup_k \mathcal{E}_k$ over profiles — but the union is **never built**; each run materializes one profile.

### 6.2 Derived-mask collapse

Make the mask a *function of the stressor state*, not an independent stored dimension. Redefine $f_M$ to depend on $\Sigma$ alone (§3.2 already does, modulo the prior-mask argument):
$$M = f_M(\Sigma), \qquad S_{H,i} \;\equiv\; \langle \Sigma_i \rangle.$$
The mask is then *computed at the moment of response* inside $f_H$, never persisted. This removes the $\times|M|$ factor entirely (6,144 → 1,024 per human, before §6.3).

### 6.3 Single active / monotone stressor

Replace the powerset by one of two bounded encodings:

- **(a) Single active stressor.** $\Sigma_i$ holds *at most one* stressor: $\sigma \in \{\bot, \sigma_1, \dots, \sigma_k\}$ — state size $k{+}1$, not $2^k$.
- **(b) Monotone severity.** A non-decreasing level $\ell \in \{0,1,\dots,L\}$ with a threshold; stressors only *accumulate*, never clear, within a run.

Either choice makes the reachable space a **DAG**: stressors accumulate only, masks degrade only (Attentive → Busy → …, no recovery in the base machinery). Recovery (§7 of the plan) is an explicit *later* profile, modeled by a separate positive mitigation fact — never by removing a stressor — so monotonicity is preserved.

### 6.4 Narrow interface

The only coupling from $\mathcal{P}$ into $\mathcal{H}$ is the request **complexity** $\in \{\text{Easy}, \text{Hard}\}$ consumed by $f_U$ (§3.1). Hold that as the *sole* interface. As long as the contract is "Hard request $\Rightarrow$ one stressor event," the four layers compose lazily and the product $\mathcal{P} \times \mathcal{H} \times \mathcal{U} \times \mathcal{N}$ is never instantiated as a monolith.

### 6.5 Per-experiment composition

If two stressors act on disjoint masks / disjoint actions, their experiments are **orthogonal**: prove the §5 Protocol-Vulnerability property on each $\langle 1\ \text{mask},\ 1\ \text{stressor}\rangle$ experiment independently and compose. Cost becomes **additive** in the catalogue, not multiplicative:
$$\sum_k |\text{experiment}_k| \quad\text{instead of}\quad \prod_k 2^{|\mathcal{S}_{\sigma,k}|}.$$
Bound participants too: analyze **one** honest human under the Dolev–Yao adversary rather than parameterizing over unbounded humans.

### 6.6 Phase-0 as the first profile

The agreed bootstrap experiment is exactly the smallest profile:
$$\mathcal{E}_0 = \big\langle\, C_0\ (\text{Alex–Blake KDF}),\ \{\text{Attentive}, \text{Busy}\},\ \{\sigma_1\ \text{HighCognitiveLoad}\} \,\big\rangle$$
with a single $f_M$ edge (Attentive→Busy) and one honest stressed party. Human state: **2** reachable masks, derived, single stressor — flat. Adding masks/stressors to the *catalogue* leaves $\mathcal{E}_0$ untouched; each new construct is a *new* profile/experiment, kept small by §6.1–§6.5.

### 6.7 Tamarin realization (for when $C_0$ lands)

- **Stressor** = linear fact `!Stressor(h, σ)` gated by a restriction allowing at most one active per human — no set/powerset in the fact space.
- **Mask** = an **action-fact label** computed inside the rule (§6.2), not a persistent stored fact — no $\times|M|$ and no extra sources.
- **Profile setup** rule emits *only* the masks/stressors the experiment names; disabled ones generate no rules ⇒ fewer partial deconstructions and less branching.
- **Monotone** degradation via linear facts consumed once ⇒ bounded, acyclic, terminating proof search.

### 6.8 Realization status (2026-06-22)

§6 is **implemented** in `tamarin_model/` as profiles $\mathcal{E}_0$ (Experiment 01), plus $\mathcal{E}_2 = \langle C_0{+}\text{UI}, \{\text{Attentive},\text{Habituated}\}, \{\sigma_8\}\rangle$ (Experiment 02) and $\mathcal{E}_3 = \langle C_0, \{\text{Attentive},\text{Careless}\}, \{\sigma_2\}\rangle$ (Experiment 03), atop the Experiment-00 baseline. All four entry-point theories prove under Tamarin 1.12 (22 lemmas). Confirmations and one refinement to §6.7:

- **Derived mask (§6.2)** holds as written — the mask is an action-fact label, not stored. Two practical findings: (i) the *stored* `St_H` style provably **loops** Tamarin's sources solver (it can source the mask from the rule consuming it), which is the concrete reason §6.2 is mandatory, not just an optimization; (ii) the §6.3 "single active stressor" is most simply enforced by capping the *trigger action* (`OneStressPerParty` etc.) rather than the `!Stressor` fact itself.
- **Refinement to "Profile setup".** Disabled masks/stressors must be *physically excluded from the include set*, not merely left unfired: an included rule whose LHS fact no producer supplies is a **hard wellformedness failure**. This forces `f_H` files to be **action-scoped** (`<mask>_<action>.spthy`) so each experiment can include a *closed* subset — see `usability_extension_plan.md` Appendix A.
- **Single instance.** A `OneInstancePerHuman` restriction (keyed on `Start(p)`) realizes the "one honest human" of §6.5 at the instance level.
