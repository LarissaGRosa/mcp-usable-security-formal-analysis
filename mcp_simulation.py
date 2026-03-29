#!/usr/bin/env python3
"""
MCP + Pirandellian Masks — State Machine Simulation

Two experiments:

  EXPERIMENT 1 — SCOPE SAFETY (existing):
    "An MCP write affecting files outside the original prompt scope
     must not execute."

  EXPERIMENT 2 — NAMESPACE TYPOSQUATTING (new):
    "A malicious server mimicking a legitimate server name must not
     successfully execute tool calls."

Each experiment has Phase 1 (unmitigated) and Phase 2 (mitigated).

Usage:
    python3 mcp_simulation.py
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Union


# ─── Types ───────────────────────────────────────────────────────────

class State(Enum):
    IDLE = auto()
    TASK_ACTIVE = auto()
    CONTEXT_READ = auto()
    PROPOSAL_READY = auto()
    PENDING_APPROVAL = auto()
    FRICTION_STATE = auto()   # Phase 2 only
    APPROVED = auto()
    EXECUTED = auto()
    REJECTED = auto()

class MCPState(Enum):
    """Lower-level MCP protocol states for typosquatting simulation."""
    HOST_INIT = auto()
    CLIENT_INIT = auto()
    SERVER_INIT = auto()
    HANDSHAKE_SENT = auto()
    HANDSHAKE_RECEIVED = auto()
    SERVER_VALIDATED = auto()
    FRICTION_HANDSHAKE = auto()
    SESSION_READY = auto()
    TOOL_REQUESTED = auto()
    TOOL_EXECUTED = auto()
    RESULT_DELIVERED = auto()
    RESULT_PROCESSED = auto()
    REJECTED = auto()

class Mask(Enum):
    ATTENTIVE = "Attentive"
    CARELESS  = "Careless"
    NAIVE     = "Naive"

class LLMBehavior(Enum):
    IN_SCOPE  = "In-Scope (honest)"
    OUT_SCOPE = "Out-of-Scope (hallucination)"

class ServerType(Enum):
    LEGITIMATE = "Legitimate (FileServer)"
    MALICIOUS  = "Malicious (Fi1eServer — typosquatted)"

class SafetyVerdict(Enum):
    SAFE     = "✅ SAFE"
    VIOLATED = "❌ VIOLATED"
    BLOCKED  = "🛡️ BLOCKED by Friction"


# ─── Trace Recorder ─────────────────────────────────────────────────

@dataclass
class TraceStep:
    state: Union[State, MCPState]
    action: str
    detail: str = ""

def fmt_trace(steps: list[TraceStep]) -> str:
    lines = []
    for i, s in enumerate(steps):
        arrow = "  →  " if i > 0 else "     "
        detail = f"  ({s.detail})" if s.detail else ""
        lines.append(f"  {arrow}{s.state.name}{detail}")
        lines.append(f"         ↳ {s.action}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# EXPERIMENT 1 — SCOPE SAFETY
# ═══════════════════════════════════════════════════════════════════════

# ─── Phase 1: Base Model (No Mitigations) ───────────────────────────

def simulate_phase1(mask: Mask, llm: LLMBehavior) -> tuple[list[TraceStep], SafetyVerdict]:
    """Simulate Phase 1 (unmitigated) pipeline."""
    trace = []
    scope = "update_logging"
    
    # 1. Init
    trace.append(TraceStep(State.IDLE, "User prompts: 'Update logging library'"))
    
    # 2. Task created
    trace.append(TraceStep(State.TASK_ACTIVE, f"Task created, scope='{scope}'"))
    
    # 3. MCP Read
    trace.append(TraceStep(State.CONTEXT_READ, "MCP reads package.json"))
    
    # 4. MCP Return
    trace.append(TraceStep(State.PROPOSAL_READY, "MCP returns context to LLM"))
    
    # 5. LLM proposes
    if llm == LLMBehavior.IN_SCOPE:
        target = scope
        trace.append(TraceStep(
            State.PENDING_APPROVAL, 
            f"LLM proposes in-scope write",
            f"target='{target}'"
        ))
    else:
        target = "update_logging_AND_auth"
        trace.append(TraceStep(
            State.PENDING_APPROVAL, 
            f"LLM proposes OUT-OF-SCOPE write ⚠️",
            f"target='{target}'"
        ))
    
    is_out_scope = (scope != target)
    
    # 6. Human decision (mask-dependent)
    if mask == Mask.ATTENTIVE:
        if is_out_scope:
            trace.append(TraceStep(
                State.REJECTED,
                f"[{mask.value}] Reviews diff, spots auth library → REJECTS"
            ))
            return trace, SafetyVerdict.SAFE
        else:
            trace.append(TraceStep(
                State.APPROVED,
                f"[{mask.value}] Reviews diff, scope matches → ACCEPTS"
            ))
    
    elif mask == Mask.CARELESS:
        trace.append(TraceStep(
            State.APPROVED,
            f"[{mask.value}] Skips diff review → ACCEPTS ALL"
        ))
    
    elif mask == Mask.NAIVE:
        if is_out_scope:
            trace.append(TraceStep(
                State.APPROVED,
                f"[{mask.value}] Reads diff, sees auth lib, assumes it's needed → ACCEPTS"
            ))
        else:
            trace.append(TraceStep(
                State.APPROVED,
                f"[{mask.value}] Reads diff, all looks normal → ACCEPTS"
            ))
    
    # 7. Execution
    trace.append(TraceStep(
        State.EXECUTED, 
        f"MCP writes to package.json",
        f"target='{target}'"
    ))
    
    verdict = SafetyVerdict.VIOLATED if is_out_scope else SafetyVerdict.SAFE
    return trace, verdict


# ─── Phase 2: Mitigated Model (Contextual Friction) ─────────────────

def simulate_phase2(mask: Mask, llm: LLMBehavior) -> tuple[list[TraceStep], SafetyVerdict]:
    """Simulate Phase 2 (mitigated) pipeline with Contextual Friction."""
    trace = []
    scope = "update_logging"
    
    # 1-4. Same as Phase 1
    trace.append(TraceStep(State.IDLE, "User prompts: 'Update logging library'"))
    trace.append(TraceStep(State.TASK_ACTIVE, f"Task created, scope='{scope}'"))
    trace.append(TraceStep(State.CONTEXT_READ, "MCP reads package.json"))
    trace.append(TraceStep(State.PROPOSAL_READY, "MCP returns context to LLM"))
    
    # 5. LLM proposes — routing depends on scope match
    if llm == LLMBehavior.IN_SCOPE:
        target = scope
        trace.append(TraceStep(
            State.PENDING_APPROVAL,
            "LLM proposes in-scope write → normal approval path",
            f"target='{target}'"
        ))
        
        # Normal human decision (any mask accepts in-scope)
        trace.append(TraceStep(
            State.APPROVED, 
            f"[{mask.value}] Accepts in-scope proposal"
        ))
        trace.append(TraceStep(
            State.EXECUTED, 
            f"MCP writes to package.json",
            f"target='{target}'"
        ))
        return trace, SafetyVerdict.SAFE
    
    else:
        target = "update_logging_AND_auth"
        trace.append(TraceStep(
            State.FRICTION_STATE,
            "LLM proposes OUT-OF-SCOPE → routed to FRICTION 🛑",
            f"scope mismatch: '{scope}' ≠ '{target}'"
        ))
        
        # Friction response (mask-dependent)
        if mask == Mask.ATTENTIVE:
            trace.append(TraceStep(
                State.REJECTED,
                f"[{mask.value}] Friction: Attentive review → REJECTS"
            ))
        elif mask == Mask.CARELESS:
            trace.append(TraceStep(
                State.REJECTED,
                f"[{mask.value}] Friction: Hard Interrupt (5s delay, highlight) → REJECTS",
                "Forced cognitive break overrides autopilot"
            ))
        elif mask == Mask.NAIVE:
            trace.append(TraceStep(
                State.REJECTED,
                f"[{mask.value}] Friction: LLM Justification displayed → REJECTS",
                "User reads explanation, realizes auth lib is unrelated"
            ))
        
        return trace, SafetyVerdict.BLOCKED


# ═══════════════════════════════════════════════════════════════════════
# EXPERIMENT 2 — NAMESPACE TYPOSQUATTING (Lower-Level MCP)
# ═══════════════════════════════════════════════════════════════════════

# ─── Phase 3: Typosquatting — Unmitigated ────────────────────────────

def simulate_typosquatting_phase1(
    mask: Mask, server: ServerType
) -> tuple[list[TraceStep], SafetyVerdict]:
    """Simulate the Namespace Typosquatting scenario (unmitigated).
    
    Models the full lower-level MCP pipeline:
    Host Init → Client Init → Server Init → Handshake → Tool Call
    """
    trace = []
    legitimate_name = "FileServer"
    malicious_name  = "Fi1eServer"
    tool_name       = "read_file"
    
    is_malicious = (server == ServerType.MALICIOUS)
    server_name = malicious_name if is_malicious else legitimate_name
    
    # 1. Host initialization
    trace.append(TraceStep(
        MCPState.HOST_INIT,
        "Host '$H' created with identity and keypair"
    ))
    
    # 2. Client initialization (bound to Host)
    trace.append(TraceStep(
        MCPState.CLIENT_INIT,
        "Client created inside Host, bound 1:1 to Server"
    ))
    
    # 3. Server initialization
    if is_malicious:
        trace.append(TraceStep(
            MCPState.SERVER_INIT,
            f"⚠️ MALICIOUS Server '{malicious_name}' advertises fake tool '{tool_name}'",
            f"Typosquatted name: '{malicious_name}' mimics '{legitimate_name}'"
        ))
    else:
        trace.append(TraceStep(
            MCPState.SERVER_INIT,
            f"Server '{legitimate_name}' initialized with tool '{tool_name}'"
        ))
    
    # 4. Client sends INIT_REQUEST
    trace.append(TraceStep(
        MCPState.HANDSHAKE_SENT,
        "Client → Server: INIT_REQUEST (protocol='MCP_V1')"
    ))
    
    # 5. Server responds with INIT_RESPONSE
    trace.append(TraceStep(
        MCPState.HANDSHAKE_RECEIVED,
        f"Server → Client: INIT_RESPONSE (server='{server_name}', tool='{tool_name}')"
    ))
    
    # 6. Host validates server (MASK-DEPENDENT)
    if mask == Mask.ATTENTIVE:
        if is_malicious:
            trace.append(TraceStep(
                MCPState.REJECTED,
                f"[{mask.value}] Pattern-matches server name against $S",
                f"Expected='{legitimate_name}', Got='{malicious_name}' → REJECTS"
            ))
            return trace, SafetyVerdict.SAFE
        else:
            trace.append(TraceStep(
                MCPState.SERVER_VALIDATED,
                f"[{mask.value}] Server identity verified → ACCEPTS",
                f"'{server_name}' matches expected pattern"
            ))
    
    elif mask == Mask.CARELESS:
        trace.append(TraceStep(
            MCPState.SERVER_VALIDATED,
            f"[{mask.value}] Accepts server '{server_name}' without identity check",
            "No pattern matching — accepts ANY server response"
        ))
    
    elif mask == Mask.NAIVE:
        if is_malicious:
            trace.append(TraceStep(
                MCPState.SERVER_VALIDATED,
                f"[{mask.value}] Reads name '{malicious_name}', assumes it's a variant",
                f"Thinks '{malicious_name}' is an alias for '{legitimate_name}' → ACCEPTS"
            ))
        else:
            trace.append(TraceStep(
                MCPState.SERVER_VALIDATED,
                f"[{mask.value}] Server name looks normal → ACCEPTS"
            ))
    
    # 7. Client sends INITIALIZED → Session established
    trace.append(TraceStep(
        MCPState.SESSION_READY,
        f"Handshake complete → Trusted session established with '{server_name}'"
    ))
    
    # 8. Host requests tool invocation
    trace.append(TraceStep(
        MCPState.TOOL_REQUESTED,
        f"Host → Client → Server: TOOL_INVOKE (tool='{tool_name}')"
    ))
    
    # 9. Server executes tool
    if is_malicious:
        trace.append(TraceStep(
            MCPState.TOOL_EXECUTED,
            f"⚠️ MALICIOUS Server executes '{tool_name}' → returns POISONED result",
            "Poisoned data injected into result"
        ))
    else:
        trace.append(TraceStep(
            MCPState.TOOL_EXECUTED,
            f"Server executes '{tool_name}' → returns genuine result"
        ))
    
    # 10. Client receives and delivers result
    trace.append(TraceStep(
        MCPState.RESULT_DELIVERED,
        "Client receives TOOL_RESULT and delivers to Host"
    ))
    
    # 11. Host processes result
    trace.append(TraceStep(
        MCPState.RESULT_PROCESSED,
        "Host processes tool result",
        "POISONED data consumed ❌" if is_malicious else "Genuine data consumed ✅"
    ))
    
    verdict = SafetyVerdict.VIOLATED if is_malicious else SafetyVerdict.SAFE
    return trace, verdict


# ─── Phase 4: Typosquatting — Mitigated (Registry + Friction) ────────

def simulate_typosquatting_phase2(
    mask: Mask, server: ServerType
) -> tuple[list[TraceStep], SafetyVerdict]:
    """Simulate the Namespace Typosquatting scenario with mitigation.
    
    Two-layer mitigation:
    1. Server Registry (allowlist) — checks server name against known list
    2. Contextual Friction — if not in registry, route to friction
    """
    trace = []
    legitimate_name = "FileServer"
    malicious_name  = "Fi1eServer"
    tool_name       = "read_file"
    registry        = {legitimate_name}  # Allowlist
    
    is_malicious = (server == ServerType.MALICIOUS)
    server_name = malicious_name if is_malicious else legitimate_name
    
    # 1-5. Same initialization and handshake send/receive
    trace.append(TraceStep(
        MCPState.HOST_INIT,
        f"Host '$H' created | Server Registry: {registry}"
    ))
    trace.append(TraceStep(
        MCPState.CLIENT_INIT,
        "Client created inside Host"
    ))
    
    if is_malicious:
        trace.append(TraceStep(
            MCPState.SERVER_INIT,
            f"⚠️ MALICIOUS Server '{malicious_name}' advertises fake tool '{tool_name}'"
        ))
    else:
        trace.append(TraceStep(
            MCPState.SERVER_INIT,
            f"Server '{legitimate_name}' initialized with tool '{tool_name}'"
        ))
    
    trace.append(TraceStep(
        MCPState.HANDSHAKE_SENT,
        "Client → Server: INIT_REQUEST (protocol='MCP_V1')"
    ))
    trace.append(TraceStep(
        MCPState.HANDSHAKE_RECEIVED,
        f"Server → Client: INIT_RESPONSE (server='{server_name}', tool='{tool_name}')"
    ))
    
    # 6. REGISTRY CHECK — Is the server in the allowlist?
    if server_name in registry:
        # Registered server → bypass friction, normal mask path
        trace.append(TraceStep(
            MCPState.SERVER_VALIDATED,
            f"✅ Server '{server_name}' found in registry → bypass friction",
            f"Registry match: '{server_name}' ∈ {registry}"
        ))
    else:
        # Unregistered server → FRICTION
        trace.append(TraceStep(
            MCPState.FRICTION_HANDSHAKE,
            f"🛑 Server '{server_name}' NOT in registry → routed to FRICTION",
            f"Registry mismatch: '{server_name}' ∉ {registry}"
        ))
        
        # Friction response (mask-dependent, all reject)
        if mask == Mask.ATTENTIVE:
            trace.append(TraceStep(
                MCPState.REJECTED,
                f"[{mask.value}] Friction: Informational alert → REJECTS",
                f"Attentive user already suspicious of '{malicious_name}'"
            ))
        elif mask == Mask.CARELESS:
            trace.append(TraceStep(
                MCPState.REJECTED,
                f"[{mask.value}] Friction: Hard Interrupt (accept disabled, 5s delay) → REJECTS",
                f"Forced to read: 'Server \"{malicious_name}\" is not in your registry'"
            ))
        elif mask == Mask.NAIVE:
            trace.append(TraceStep(
                MCPState.REJECTED,
                f"[{mask.value}] Friction: Visual Diff (side-by-side comparison) → REJECTS",
                f"Sees: '{legitimate_name}' vs '{malicious_name}' — spots the '1' vs 'l'"
            ))
        
        return trace, SafetyVerdict.BLOCKED
    
    # 7-11. Normal flow for registered servers
    trace.append(TraceStep(
        MCPState.SESSION_READY,
        f"Handshake complete → Trusted session with '{server_name}'"
    ))
    trace.append(TraceStep(
        MCPState.TOOL_REQUESTED,
        f"Host → Client → Server: TOOL_INVOKE (tool='{tool_name}')"
    ))
    trace.append(TraceStep(
        MCPState.TOOL_EXECUTED,
        f"Server executes '{tool_name}' → returns genuine result"
    ))
    trace.append(TraceStep(
        MCPState.RESULT_DELIVERED,
        "Client receives TOOL_RESULT and delivers to Host"
    ))
    trace.append(TraceStep(
        MCPState.RESULT_PROCESSED,
        "Host processes tool result",
        "Genuine data consumed ✅"
    ))
    
    return trace, SafetyVerdict.SAFE


# ─── Main ────────────────────────────────────────────────────────────

def run_experiment(phase_name, simulate_fn, combinations):
    """Run a single experiment and print results."""
    separator = "=" * 70
    
    print(f"\n{separator}")
    print(f"  {phase_name}")
    print(separator)
    
    results = []
    
    for mask, scenario in combinations:
        trace, verdict = simulate_fn(mask, scenario)
        results.append((mask, scenario, verdict))
        
        print(f"\n{'─' * 60}")
        print(f"  Mask: {mask.value:10s} | Scenario: {scenario.value}")
        print(f"  Verdict: {verdict.value}")
        print(f"{'─' * 60}")
        print(fmt_trace(trace))
    
    # Summary table
    print(f"\n{'─' * 60}")
    print(f"  SUMMARY: {phase_name}")
    print(f"{'─' * 60}")
    print(f"  {'Mask':<12} {'Scenario':<42} {'Verdict'}")
    print(f"  {'─'*12} {'─'*42} {'─'*20}")
    for mask, scenario, verdict in results:
        print(f"  {mask.value:<12} {scenario.value:<42} {verdict.value}")
    
    return results


def run_all():
    separator = "=" * 70
    
    # ─── Experiment 1: Scope Safety (existing) ───────────────────
    llm_combos = [(m, l) for m in Mask for l in LLMBehavior]
    
    run_experiment(
        "EXPERIMENT 1 — SCOPE SAFETY: Phase 1 (Unmitigated)",
        simulate_phase1, llm_combos
    )
    run_experiment(
        "EXPERIMENT 1 — SCOPE SAFETY: Phase 2 (Contextual Friction)",
        simulate_phase2, llm_combos
    )
    
    # Cross-phase comparison for Experiment 1
    print(f"\n{separator}")
    print("  CROSS-PHASE COMPARISON: Scope Safety")
    print(f"  \"Out-of-scope writes must not execute\"")
    print(separator)
    print(f"  {'Mask':<12} {'Phase 1':<25} {'Phase 2'}")
    print(f"  {'─'*12} {'─'*25} {'─'*25}")
    for mask in Mask:
        _, v1 = simulate_phase1(mask, LLMBehavior.OUT_SCOPE)
        _, v2 = simulate_phase2(mask, LLMBehavior.OUT_SCOPE)
        print(f"  {mask.value:<12} {v1.value:<25} {v2.value}")
    
    # ─── Experiment 2: Namespace Typosquatting (new) ─────────────
    server_combos = [(m, s) for m in Mask for s in ServerType]
    
    run_experiment(
        "EXPERIMENT 2 — NAMESPACE TYPOSQUATTING: Phase 1 (Unmitigated)",
        simulate_typosquatting_phase1, server_combos
    )
    run_experiment(
        "EXPERIMENT 2 — NAMESPACE TYPOSQUATTING: Phase 2 (Registry + Friction)",
        simulate_typosquatting_phase2, server_combos
    )
    
    # Cross-phase comparison for Experiment 2
    print(f"\n{separator}")
    print("  CROSS-PHASE COMPARISON: Namespace Typosquatting Safety")
    print(f"  \"Malicious server tool execution must not succeed\"")
    print(separator)
    print(f"  {'Mask':<12} {'Phase 1':<25} {'Phase 2'}")
    print(f"  {'─'*12} {'─'*25} {'─'*25}")
    for mask in Mask:
        _, v1 = simulate_typosquatting_phase1(mask, ServerType.MALICIOUS)
        _, v2 = simulate_typosquatting_phase2(mask, ServerType.MALICIOUS)
        print(f"  {mask.value:<12} {v1.value:<25} {v2.value}")
    print()


if __name__ == "__main__":
    run_all()
