# Experiment 2, Phase 2 — Namespace Typosquatting: Mitigated Model

## Objective

Modify the Phase 1 typosquatting model to introduce a **two-layer mitigation** — Server Registry and Contextual Friction — that restores the safety property across all three Pirandellian masks. Formally prove that no malicious server can execute under the mitigated architecture.

---

## Motivation

Phase 1 proves that `no_malicious_execution` is violated under **all** masks — including the Attentive mask. This is a stronger result than Experiment 1 (Scope Safety), where the Attentive mask alone was sufficient.

The core problem: **no mask has an internal reference for which server is legitimate.** The mitigation must provide this reference.

The answer is a **two-layer defense**:

1. **Server Registry (Allowlist)** — Provides the missing reference: a pre-configured list of trusted servers.
2. **Contextual Friction** — Intercepts unregistered servers and applies mask-specific countermeasures to ensure rejection.

---

## Modelling Path

### Step 1: Server Registry — The Missing Reference

A new persistent fact `!ServerRegistry($H, $ServerName)` models the Host's allowlist of trusted servers:

```
rule RegisterServer:
    [ !Host($H, ~hostId),
      !Server($ServerName, serverId, toolName, toolDesc) ]
    --[ ServerRegistered($H, $ServerName) ]->
    [ !ServerRegistry($H, $ServerName) ]
```

**Key restrictions** enforce the registry's integrity:

```
// Only legitimate servers can be registered
restriction OnlyLegitimateRegistered:
  "All H serverName #i.
    ServerRegistered(H, serverName) @ #i
    ==> (Ex serverId #j. LegitimateServer(serverName, serverId) @ #j)"

// Same name cannot be both legitimate and malicious
restriction ExclusiveServerType:
  "All name id1 id2 #i #j.
    LegitimateServer(name, id1) @ #i
    & MaliciousServer(name, id2) @ #j
    ==> F"

// Registry lookup is deterministic: registered → registered path only
restriction RegistryExclusive:
  "All H serverName sessionId #i.
    UnregisteredServerDetected(H, serverName, sessionId) @ #i
    ==> not(Ex #j. ServerRegistered(H, serverName) @ #j)"
```

**Real-world analogy:** This models the act of configuring trusted servers in your IDE settings — similar to configuring trusted npm registries or SSH known_hosts.

---

### Step 2: Server Discovery — Two Paths

Discovery now branches based on the registry:

```
              Server responds to handshake
                        │
             ┌──────────┴──────────┐
             │                      │
        In Registry            NOT in Registry
        ($S registered)        (unknown name)
             │                      │
             ▼                      ▼
  HostDiscoverServer_        HostDiscoverServer_
     Registered                Unregistered
             │                      │
             ▼                      ▼
   PendingValidation          FrictionState
   (normal mask flow)         (countermeasures)
```

**PATH A — Registered Server:**
```
rule HostDiscoverServer_Registered:
    [ ..., !ServerRegistry($H, $ServerName), Fr(~sessionId) ]
    --[ RegisteredServerFound($H, $ServerName, ~sessionId) ]->
    [ PendingValidation(...) ]
```
Requires the persistent fact `!ServerRegistry` — only fires for servers the Host explicitly trusts.

**PATH B — Unregistered Server:**
```
rule HostDiscoverServer_Unregistered:
    [ !Host($H, ~hostId), !Server($ServerName, ...), Fr(~sessionId) ]
    --[ UnregisteredServerDetected($H, $ServerName, ~sessionId) ]->
    [ FrictionState(...) ]
```
Fires for any server. The `RegistryExclusive` restriction ensures this path is **not taken** for registered servers.

---

### Step 3: Contextual Friction — Mask-Specific Countermeasures

All three friction rules consume `FrictionState` and produce `[ ]` (empty — safe termination). The critical guarantee is that **no `FrictionState` can ever produce a `TrustedSession`**.

| Mask | Friction Mechanism | Real-World Implementation |
|:---|:---|:---|
| **Careless** | Hard Interrupt | "Accept" button disabled for 5s, flashing red warning. Forces the user to stop and read. |
| **Naive** | Visual Diff | Side-by-side comparison: `FileServer` vs `Fi1eServer`. Highlights the `l` → `1` substitution. |
| **Attentive** | Informational Alert | Banner: "Server not in registry." Redundant for Attentive, but consistent. |

```
rule Friction_Careless_Reject:
    [ FrictionState($H, ..., $ServerName, ...) ]
    --[ CarelessCaughtByFriction($H, ~sessionId),
        ServerRejected($H, $ServerName, ~sessionId) ]->
    [ ]   ← trace terminates here safely

rule Friction_Naive_Reject:
    [ FrictionState($H, ..., $ServerName, ...) ]
    --[ NaiveCaughtByFriction($H, ~sessionId),
        ServerRejected($H, $ServerName, ~sessionId) ]->
    [ ]   ← trace terminates here safely
```

**Why friction always rejects:** The `FrictionState` is a linear fact consumed by the friction rules. There is no rule that converts `FrictionState` into `PendingValidation` or `TrustedSession`. The trace is **structurally** forced to terminate.

---

### Step 4: Normal Flow — Registered Servers

For registered servers, the pipeline is unchanged from Phase 1:

```
PendingValidation → Mask Accept → TrustedSession → ToolInvoke → Execute → Result
```

All three masks (Attentive, Careless, Naive) can accept registered servers. Since the registry only contains legitimate servers (enforced by `OnlyLegitimateRegistered`), the `ServerExecute_Malicious` rule can never fire for a registered server.

---

## The Proof Argument

The safety guarantee follows from three invariants:

1. **Registry integrity:** Only legitimate servers can be registered (`OnlyLegitimateRegistered` + `ExclusiveServerType`).
2. **Path exclusivity:** Registered servers go to `PendingValidation`; unregistered go to `FrictionState` (`RegistryExclusive`).
3. **Friction termination:** `FrictionState` can only produce `[ ]` (no outgoing facts to `TrustedSession`).

Therefore:
- Malicious servers are never registered (invariant 1)
- Malicious servers always go to `FrictionState` (invariant 2)
- `FrictionState` always terminates safely (invariant 3)
- Malicious execution is **structurally unreachable** ∎

---

## Verification Results

| Lemma | Type | Expected | Meaning |
|:---|:---|:---|:---|
| `tool_call_reachable` | exists-trace | ✅ verified | Normal flow still works |
| `friction_catches_careless` | exists-trace | ✅ verified | Friction intercepts Careless |
| `friction_catches_naive` | exists-trace | ✅ verified | Friction intercepts Naive |
| `server_registration_reachable` | exists-trace | ✅ verified | Registry mechanism works |
| `poisoned_result_impossible` | all-traces | ✅ verified | No poisoned data reaches Host |
| `careless_attack_blocked` | all-traces | ✅ verified | Careless + malicious = blocked |
| `naive_attack_blocked` | all-traces | ✅ verified | Naive + malicious = blocked |
| **`no_malicious_execution`** | all-traces | ✅ **verified** | **Safety restored** |

### Cross-Phase Comparison

| Lemma | Phase 1 | Phase 2 |
|:---|:---|:---|
| `tool_call_reachable` | ✅ verified | ✅ verified |
| `no_malicious_execution` | ❌ **falsified** | ✅ **verified** |
| `poisoned_result_delivered` | ✅ verified (attack exists) | ✅ verified (attack impossible) |

The **reversal** of `no_malicious_execution` from **falsified → verified** is the central result: the Server Registry + Contextual Friction mitigation formally eliminates the Namespace Typosquatting vulnerability.

---

## Trace Diagram — Mitigated (Friction Catches Careless)

```
[Fr(~malId)]
    │
    ▼
!Server('Fi1eServer', ~malId, 'read_file', ~desc)
!IsMalicious('Fi1eServer', ~malId)
    │
    │   [Fr(~hostId)]                    [Fr(~legitId)]
    │       │                                │
    │       ▼                                ▼
    │   !Host('$H', ~hostId)        !Server('FileServer', ~legitId, ...)
    │       │                                │
    │       │   RegisterServer               │
    │       ▼───────────────────────────────▶│
    │   !ServerRegistry('$H', 'FileServer')  │
    │       │                                │
    ▼       ▼
HostDiscoverServer_Unregistered('Fi1eServer')
    │
    │   'Fi1eServer' ∉ Registry
    │
    ▼
FrictionState('$H', ..., 'Fi1eServer', ...)
    │
    ▼  Friction_Careless_Reject
[ ]  ← SAFE TERMINATION
    │
    ▼
🛡️ ATTACK BLOCKED — No TrustedSession, no execution
```

---

## Trace Diagram — Normal Flow (Registered Server)

```
[Fr(~legitId)]
    │
    ▼
!Server('FileServer', ~legitId, 'read_file', ~desc)
    │
    │   [Fr(~hostId)]
    │       │
    │       ▼
    │   !Host('$H', ~hostId)
    │       │
    │       ▼  RegisterServer
    │   !ServerRegistry('$H', 'FileServer')
    │       │
    ▼       ▼
HostDiscoverServer_Registered('FileServer')
    │
    │   'FileServer' ∈ Registry ✅
    │
    ▼
PendingValidation('$H', ..., 'FileServer', ...)
    │
    ▼  HostCareless_Accept (or any mask)
TrustedSession('$H', 'FileServer', ...)
    │
    ▼  HostInvokeTool
ToolRequest('$H', 'FileServer', ..., 'read_file', ...)
    │
    ▼  ServerExecute_Honest
ToolResult('$H', ..., 'genuine')
    │
    ▼  HostReceiveResult
ResultDelivered('$H', ..., 'genuine')
    │
    ▼
✅ SAFE — Genuine data consumed
```

---

## Colour Legend (Interactive Mode)

| Colour | Hex | Rules |
|:---|:---|:---|
| 🟢 Green | `#00AA00` | `InitLegitimateServer`, `HostDiscoverServer_Registered` |
| 🔴 Red | `#FF0000` | `InitMaliciousServer`, `ServerExecute_Malicious` |
| 🟠 Orange | `#FF6600` | `HostDiscoverServer_Unregistered` (detection point) |
| 🔵 Blue | `#4488CC` | `Friction_Careless_Reject`, `Friction_Naive_Reject`, `Friction_Attentive_Reject` |

---

## Running the Experiment

```bash
# In WSL
cd /mnt/c/Users/ismae/mcp-usable-security-formal-analysis

# Automated proof (text output)
tamarin-prover --prove experiments/typosquatting_phase2.spthy

# Interactive mode (visual graphs — includes mitigation colours)
tamarin-prover interactive experiments/typosquatting_phase2.spthy
# → Open http://127.0.0.1:3001 → Press 's' to autoprove
```
