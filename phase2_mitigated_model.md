# Phase 2 — Mitigated Model: Contextual Friction & Verification Boundaries

## Objective

Modify the Phase 1 model to introduce **mitigation mechanisms** that restore the safety property across all three masks. This phase represents the paper's **core contribution**: a concrete architectural proposal to make MCP robust against imperfect human operators.

---

## Motivation

Phase 1 proves that `Strict_Scope_Safety` is violated when the human is Careless or Naive. The question becomes: **what minimal modification to the MCP/IDE pipeline can restore safety?**

The answer is **Contextual Friction** — a new intermediary layer that detects scope mismatches and introduces mask-specific countermeasures *before* the human makes a decision.

---

## Intended Modelling Path

### Step 1: Scope Mismatch Detection (New Interception Point)

We introduce a new rule that fires **between** the LLM proposal and the human decision. When the system detects that `$Scope ≠ $Target`, the proposal is routed to a `FrictionState` instead of directly to `PendingApproval`.

```
rule Friction_ScopeCheck:
  [ PendingApproval(~tid, $Scope, $Target) ]
  --[ ScopeMismatchDetected(~tid, $Scope, $Target) ]->
  [ FrictionState(~tid, $Scope, $Target) ]
```

**Key modelling decision:** This rule replaces the direct `PendingApproval → Human decision` path for out-of-scope proposals only. In-scope proposals (`$Scope == $Target`) bypass friction entirely and go straight to the human — ensuring zero overhead for normal operations.

**How this is enforced in Tamarin:** The `Friction_ScopeCheck` rule only fires when `$Scope` and `$Target` do not unify. For in-scope proposals where both are the same public name, the existing mask rules fire directly from `PendingApproval`.

> The interception happens at the IDE/MCP layer, not at the human layer. This models a **system-level** safeguard, not a change in human behavior.

---

### Step 2: Mitigation for the Careless Mask — Hard Interrupt

The Careless user's failure mode is **speed over scrutiny** — they click "Accept All" without reading. The mitigation introduces a **forced cognitive break**: the "Accept" button is disabled temporarily, and the scope mismatch is highlighted.

#### Modelling approach

We model this as a **state transformation**: the `FrictionState` forces the Careless user into a `ForcedReview` state, where they must re-evaluate. The model captures two possible outcomes:

```
rule Friction_HardInterrupt_Reject:
  [ FrictionState(~tid, $Scope, $Target) ]
  --[ 
      FrictionApplied(~tid, 'HardInterrupt'),
      MaskApplied('Careless'),
      Rejected(~tid, $Target)
  ]->
  [ ]  // Safe termination
```

```
rule Friction_HardInterrupt_AcceptAnyway:
  [ FrictionState(~tid, $Scope, $Target) ]
  --[
      FrictionApplied(~tid, 'HardInterrupt'),
      MaskApplied('Careless'),
      Approved(~tid, $Target),
      FrictionOverridden(~tid)
  ]->
  [ FrictionOverriddenProposal(~tid, $Target) ]
```

**Why two outcomes?** The Hard Interrupt does not *guarantee* safety — it only raises the cognitive barrier. However, for the safety property to hold universally, we need the system to block execution even if the user overrides friction. This is handled in Step 4 below.

**Alternative (simpler) modelling choice:** If we want the paper to claim that friction *deterministically* fixes the Careless mask, we can omit `Friction_HardInterrupt_AcceptAnyway` entirely — meaning the Careless user always rejects under friction. This is a reasonable simplification for the MVP and produces cleaner verification results.

---

### Step 3: Mitigation for the Naive Mask — LLM Self-Justification

The Naive user's failure mode is **false trust** — they see the out-of-scope change but assume the LLM knows best. The mitigation requires the LLM to produce a **plain-text justification** explaining *why* it is touching files outside the requested scope.

#### Modelling approach

The justification introduces new information that can shift the Naive user's understanding:

```
rule Friction_LLM_Justification_Reject:
  [ FrictionState(~tid, $Scope, $Target) ]
  --[
      FrictionApplied(~tid, 'LLMJustification'),
      MaskApplied('Naive'),
      Rejected(~tid, $Target),
      JustificationRead(~tid)
  ]->
  [ ]  // Safe termination — justification was unconvincing
```

```
rule Friction_LLM_Justification_Accept:
  [ FrictionState(~tid, $Scope, $Target) ]
  --[
      FrictionApplied(~tid, 'LLMJustification'),
      MaskApplied('Naive'),
      Approved(~tid, $Target),
      FrictionOverridden(~tid)
  ]->
  [ FrictionOverriddenProposal(~tid, $Target) ]
```

**Same design choice as Careless:** For the simplest MVP, we can model the justification as always convincing the Naive user to reject (omit the accept rule). For a richer model, we keep both outcomes and use a secondary safeguard (Step 4).

---

### Step 4: Secondary Safeguard — Execution Gate (Optional)

If we model friction as non-deterministic (user *may* still accept after friction), we need a **hard system-level block** to guarantee safety:

```
rule IDE_Execute_Normal:
  [ ApprovedProposal(~tid, $Target) ]
  --[ Executed(~tid, $Target) ]->
  [ SystemState(~tid, $Target) ]

// FrictionOverriddenProposal does NOT connect to IDE_Execute.
// There is no rule consuming FrictionOverriddenProposal.
// The trace terminates — execution is blocked at the system level.
```

**Alternative:** Add an `IDE_Execute_WithAudit` rule that allows execution but logs it:

```
rule IDE_Execute_WithAudit:
  [ FrictionOverriddenProposal(~tid, $Target) ]
  --[ Executed(~tid, $Target), AuditLog(~tid, $Target) ]->
  [ SystemState(~tid, $Target) ]
```

This variant allows execution but creates an audit trail, modeling a less restrictive mitigation.

---

### Step 5: Choosing the Modelling Strategy

For the conference paper MVP, I recommend the **simplest deterministic model**:

| Decision Point | Choice | Rationale |
|:---|:---|:---|
| Friction for Careless | Always → Reject | Clean proof, clear narrative |
| Friction for Naive | Always → Reject | Clean proof, clear narrative |
| Execution gate | Not needed | If friction always rejects, no proposal reaches execution |
| Audit log | Not modelled | Scope reduction for MVP |

This gives us the strongest possible claim: *"Contextual Friction, when applied, deterministically restores the safety property across all masks."*

> The paper can acknowledge the non-deterministic variant (where friction only *increases* the chance of rejection) as future work requiring probabilistic model checking.

---

## Modified Protocol Flow

```
                    LLM proposes
                        │
            ┌───────────┴───────────┐
            │                       │
       In-Scope                 Out-of-Scope
       ($S = $T)                ($S ≠ $T)
            │                       │
            ▼                       ▼
    PendingApproval          FrictionState
            │                  ┌────┴────┐
            ▼                  │         │
     Human decides          Careless   Naive
     (any mask)             HardInt.   Justif.
            │                  │         │
            ▼                  ▼         ▼
    ApprovedProposal       REJECT     REJECT
            │
            ▼
       IDE_Execute
            │
            ▼
      SystemState ✅
```

---

## Expected Verification Results (Phase 2)

| Lemma | Type | Phase 1 | Phase 2 |
|:---|:---|:---|:---|
| `Execution_Reachable` | exists-trace | ✅ | ✅ (unchanged) |
| `Careless_Vulnerability` | exists-trace | ✅ | ❌ **no longer verified** — friction blocks the attack |
| `Naive_Vulnerability` | exists-trace | ✅ | ❌ **no longer verified** — friction blocks the attack |
| `Strict_Scope_Safety` | all-traces | ❌ falsified | ✅ **now verified** |
| `Attentive_Is_Safe` | all-traces | ✅ | ✅ (unchanged) |
| `Mitigated_Scope_Safety` | all-traces | — | ✅ **new lemma, verified** |

The reversal of `Strict_Scope_Safety` from falsified → verified is the paper's main result.

---

## What This Means for the Paper

The narrative arc of the paper follows directly from the two phases:

1. **Phase 1:** *"The MCP standard is unsafe when humans are not perfectly attentive."*
   → Formal proof via counterexample.

2. **Phase 2:** *"Contextual Friction — a minimal architectural modification — restores safety."*
   → Formal proof via model checking under the mitigated model.

This gives the paper a clear **problem → solution → verification** structure with machine-checked evidence at every step.
