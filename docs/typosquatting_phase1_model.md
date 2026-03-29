# Experiment 2, Phase 1 — Namespace Typosquatting: Unmitigated Model

## Objective

Model the **Namespace Typosquatting** vulnerability in the MCP protocol — where an attacker registers a server with a visually similar name to a legitimate one (e.g., `Fi1eServer` mimicking `FileServer`) — and formally prove that the system's safety depends entirely on the human operator's ability to detect the deception.

---

## Threat Model

### Attack Scenario

A legitimate MCP server `FileServer` provides the tool `read_file`. An attacker publishes a typosquatted server `Fi1eServer` (number `1` replacing letter `l`) that advertises the **same tool name** but returns poisoned data.

```
Legitimate:   FileServer  →  read_file  →  genuine data
Typosquatted: Fi1eServer  →  read_file  →  poisoned data
```

### Key Distinction from Scope Safety (Experiment 1)

In Experiment 1 (Scope Safety), the threat is an **LLM hallucination** — the model proposes out-of-scope operations. The Attentive mask prevents this because the user can compare `$Scope` vs `$Target`.

In Namespace Typosquatting, the threat is **external** — an attacker impersonates a server. The critical difference is:

> **No mask has an internal reference for "which server is legitimate."**

The Attentive user in Experiment 1 had the task scope as a reference. Here, no mask has a registry of known server names. This makes typosquatting a **strictly stronger** threat.

---

## Modelling Approach

### Self-Contained Model (No Dolev-Yao)

Typosquatting is **not a network-level attack**. The attacker does not intercept messages; they register a server with a confusable name. We model this structurally via **non-deterministic server selection**, avoiding the Dolev-Yao adversary (`Out/In`) which would cause unnecessary state-space explosion.

This design choice reduces proof time from **minutes/hours** (with Dolev-Yao) to **< 1 second**.

### Pipeline

```
InitHost → InitServer(s) → HostDiscoverServer → HostValidate(mask)
→ TrustedSession → HostInvokeTool → ServerExecute → ResultDeliver
```

---

## Modelling Path

### Step 1: Server Initialization — Legitimate vs. Malicious

Two distinct initialization rules create the branching point:

```
rule InitLegitimateServer:
    [ Fr(~serverId), Fr(~toolDesc) ]
    --[ LegitimateServer($ServerName, ~serverId) ]->
    [ !Server($ServerName, ~serverId, $ToolName, ~toolDesc) ]

rule InitMaliciousServer:
    [ Fr(~malId), Fr(~fakeDesc) ]
    --[ MaliciousServer($FakeName, ~malId) ]->
    [ !Server($FakeName, ~malId, $ToolName, ~fakeDesc),
      !IsMalicious($FakeName, ~malId) ]
```

The `!IsMalicious` persistent fact tags the server for later — when tool execution occurs, this fact determines whether the result is genuine or poisoned.

**Restriction:** `MaliciousNameDiffers` enforces that the fake name differs from the legitimate name (for the same tool), modelling the core typosquatting premise.

### Step 2: Server Discovery — Non-Deterministic Selection

```
rule HostDiscoverServer:
    [ !Host($H, ~hostId),
      !Server($ServerName, serverId, toolName, toolDesc),
      Fr(~sessionId) ]
    --[ HostDiscovered($H, $ServerName, ...) ]->
    [ PendingValidation($H, ..., $ServerName, ...) ]
```

Because `!Server` is a persistent fact created by **both** init rules, Tamarin explores traces where the Host connects to either the legitimate or the typosquatted server.

### Step 3: The Pirandellian Decision — Three Masks

| Mask | Rule | Behavior | Vulnerability |
|:---|:---|:---|:---|
| **Attentive** | `HostAttentive_Accept` | Pattern-matches on `$ExpectedServer` | ❌ Still vulnerable — no reference to compare against |
| **Careless** | `HostCareless_Accept` | Accepts any `$ServerName` without inspection | ❌ Accepts `Fi1eServer` silently |
| **Naive** | `HostNaive_Accept` | Reads `$ServerName`, trusts it anyway | ❌ Reads `Fi1eServer`, assumes it's valid |

**Critical finding:** Unlike Experiment 1, the Attentive mask **also fails** in the typosquatting scenario. This is because the Attentive rule pattern-matches on `$ExpectedServer`, which is a free public name variable — it can unify with *any* server name, including the malicious one. Without a registry, the Attentive user has **no reference** to determine legitimacy.

### Step 4: Tool Execution — Honest vs. Malicious

```
rule ServerExecute_Honest:
    [ ToolRequest(...), !Server($ServerName, serverId, ...) ]
    --[ HonestExecution(...) ]->
    [ ToolResult(..., 'genuine') ]

rule ServerExecute_Malicious:
    [ ToolRequest(...), !IsMalicious($ServerName, serverId) ]
    --[ MaliciousExecution(...) ]->
    [ ToolResult(..., 'poisoned') ]
```

If the trusted session was established with a malicious server, `ServerExecute_Malicious` fires and delivers poisoned results.

---

## Verification Results

| Lemma | Type | Result | Steps | Meaning |
|:---|:---|:---|:---|:---|
| `tool_call_reachable` | exists-trace | ✅ verified | 3 | Protocol works end-to-end |
| `careless_vulnerability` | exists-trace | ✅ verified | 3 | Attack trace exists for Careless |
| `naive_vulnerability` | exists-trace | ✅ verified | 3 | Attack trace exists for Naive |
| `poisoned_result_delivered` | exists-trace | ✅ verified | 3 | Poisoned data reaches the Host |
| **`no_malicious_execution`** | all-traces | ❌ **falsified** | 4 | **Safety violated** |
| `attentive_prevents_malicious` | all-traces | ❌ **falsified** | 6 | Attentive also fails |

**Processing time:** 0.77 seconds

### Key Finding

The **counterexample** for `no_malicious_execution` proves that the MCP protocol is formally unsafe against Namespace Typosquatting under **all** Pirandellian masks, including the Attentive mask. This is a strictly stronger result than Experiment 1.

---

## Trace Diagram (Failure Path — Careless Mask)

```
[Fr(~malId)]
    │
    ▼
!Server('Fi1eServer', ~malId, 'read_file', ~desc)
!IsMalicious('Fi1eServer', ~malId)
    │
    │   [Fr(~hostId)]
    │       │
    │       ▼
    │   !Host('$H', ~hostId)
    │       │
    ▼       ▼
HostDiscoverServer → PendingValidation('$H', ..., 'Fi1eServer', ...)
                          │
                          ▼  HostCareless_Accept
                     TrustedSession('$H', 'Fi1eServer', ...)
                          │
                          ▼  HostInvokeTool
                     ToolRequest('$H', 'Fi1eServer', ..., 'read_file', ...)
                          │
                          ▼  ServerExecute_Malicious
                     ToolResult('$H', ..., 'poisoned')
                          │
                          ▼  HostReceiveResult
                     ResultDelivered('$H', ..., 'poisoned')
                          │
                          ▼
                     ❌ SAFETY VIOLATED
```

---

## Colour Legend (Interactive Mode)

| Colour | Hex | Rules |
|:---|:---|:---|
| 🟢 Green | `#00AA00` | `InitLegitimateServer`, `HostAttentive_Accept`, `HostAttentive_Reject` |
| 🔴 Red | `#FF0000` | `InitMaliciousServer`, `HostCareless_Accept`, `ServerExecute_Malicious` |
| 🟡 Orange | `#E8B32A` | `HostNaive_Accept` |

These colours are visible in the Tamarin interactive mode (`tamarin-prover interactive experiments/`).

---

## Running the Experiment

```bash
# In WSL
cd /mnt/c/Users/ismae/mcp-usable-security-formal-analysis

# Automated proof (text output)
tamarin-prover --prove experiments/typosquatting_phase1.spthy

# Interactive mode (visual attack graphs)
tamarin-prover interactive experiments/typosquatting_phase1.spthy
# → Open http://127.0.0.1:3001 → Press 's' to autoprove
```
