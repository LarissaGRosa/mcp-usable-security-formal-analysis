# Phase 1 — Base Model: Unmitigated MCP Pipeline

## Objective

Model the standard MCP interaction pipeline **as it exists today**, with no safety mitigations beyond the human's own cognitive judgment. Demonstrate that the system's safety depends entirely on the human's mask.

---

## Intended Modelling Path

### Step 1: Task Initialization

The model begins when a human types a prompt in the IDE. This creates a **task** with a unique identifier and an **authorized scope** — the set of files/libraries the user explicitly mentioned.

```
Fr(~taskId)  →  Task(~taskId, $Scope)
```

- `~taskId`: a fresh nonce (Tamarin models uniqueness via freshness)
- `$Scope`: a public name representing the user's intent (e.g., `'update_logging'`)

**Why this matters:** The scope is the ground truth against which all proposals are evaluated. It is fixed at task creation and never changes.

---

### Step 2: LLM Proposal — The Branching Point

The LLM consumes the task context (via MCP read) and produces a **write proposal**. This is where the model **non-deterministically** forks into two possible worlds:

#### Path A: In-Scope Proposal (Honest LLM)
```
Task(~tid, $Scope)  →  PendingApproval(~tid, $Scope, $Scope)
```
The proposed target matches the authorized scope exactly. Tamarin enforces this via **pattern unification** — both arguments are the same variable `$Scope`.

#### Path B: Out-of-Scope Proposal (Hallucinating LLM)
```
Task(~tid, $Scope)  →  PendingApproval(~tid, $Scope, $Target)
```
The proposed target `$Target` is a **different** public name (e.g., `'update_logging_and_auth'`). The action label `IsOutScope(~tid)` tags this trace for analysis.

**Key design choice:** We do not model *why* the LLM hallucinates — only that it *can*. Tamarin's non-determinism naturally captures this: both rules are always available, and the prover explores both.

---

### Step 3: The Pirandellian Decision — Three Masks, Three Realities

The `PendingApproval` fact reaches the human. The human's response is determined by their mask:

#### Mask: Attentive
The Attentive user performs **scope verification**. In Tamarin, this is elegantly modeled via premise pattern matching:

- **Accept rule premise:** `PendingApproval(~tid, $Scope, $Scope)` — the Scope and Target variables *must* unify. If the LLM proposed out-of-scope, this rule simply **cannot fire**.
- **Reject rule premise:** `PendingApproval(~tid, $Scope, $Target)` — fires for any mismatch. The conclusion is empty (`[]`), modeling safe termination.

**Result:** Out-of-scope proposals are structurally unreachable from execution.

#### Mask: Careless
The Careless user **does not inspect** the proposal. The rule premise uses `PendingApproval(~tid, $Scope, $Target)` with no equality constraint between `$Scope` and `$Target`. This means the rule fires for **any** proposal, in-scope or not.

**Failure mode:** *Silent* — the user is unaware they approved a dangerous change.

#### Mask: Naive
Structurally identical to Careless at the Tamarin level (same premise pattern), but tagged with `NaiveMistake` instead of `CarelessMistake`. The semantic distinction is critical:

- Careless = failure of **attention** (didn't look)
- Naive = failure of **knowledge** (looked, but misinterpreted)

**Failure mode:** *Authorized* — the user consciously approved based on false trust.

---

### Step 4: Execution

Any `ApprovedProposal` fact is consumed by the `IDE_Execute` rule, producing a `SystemState` with the executed target. There is no further safety check.

```
ApprovedProposal(~tid, $Target)  →  SystemState(~tid, $Target)
```

---

## Expected Verification Results

| Lemma | Type | Expected | Meaning |
|:---|:---|:---|:---|
| `Execution_Reachable` | exists-trace | ✅ verified | The system can complete a normal task |
| `Careless_Vulnerability` | exists-trace | ✅ verified | An attack trace exists via Careless mask |
| `Naive_Vulnerability` | exists-trace | ✅ verified | An attack trace exists via Naive mask |
| `Strict_Scope_Safety` | all-traces | ❌ **falsified** | Out-of-scope execution IS reachable |
| `Attentive_Is_Safe` | all-traces | ✅ verified | The Attentive mask alone preserves safety |

The **counterexample** generated for `Strict_Scope_Safety` is the primary artifact of Phase 1. It is a formal proof that the MCP standard is unsafe under non-Attentive human behavior.

---

## Trace Diagram (Failure Path)

```
[Fr(~tid)]
    │
    ▼
Task(~tid, 'update_logging')
    │
    ▼  LLM_Propose_OutScope
PendingApproval(~tid, 'update_logging', 'update_logging_and_auth')
    │                                    │
    ▼  Human_Careless_Accept             ▼  Human_Naive_Accept
ApprovedProposal(~tid,                 ApprovedProposal(~tid,
  'update_logging_and_auth')             'update_logging_and_auth')
    │                                    │
    ▼  IDE_Execute                       ▼  IDE_Execute
SystemState(~tid,                      SystemState(~tid,
  'update_logging_and_auth')             'update_logging_and_auth')
    │                                    │
    ▼                                    ▼
  ❌ SAFETY VIOLATED                   ❌ SAFETY VIOLATED
```
