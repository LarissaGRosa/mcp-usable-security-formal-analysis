#!/usr/bin/env python3
"""
MCP + Pirandellian Masks — State Machine Simulation

Enumerates all traces through the MCP-LLM-IDE pipeline for each
combination of Mask × LLM Behavior, checking the safety property:

  "An MCP write affecting files outside the original prompt scope
   must not execute."

This script complements the Tamarin formal proofs with a readable,
self-contained simulation for the conference paper.

Usage:
    python3 mcp_simulation.py
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


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

class Mask(Enum):
    ATTENTIVE = "Attentive"
    CARELESS  = "Careless"
    NAIVE     = "Naive"

class LLMBehavior(Enum):
    IN_SCOPE  = "In-Scope (honest)"
    OUT_SCOPE = "Out-of-Scope (hallucination)"

class SafetyVerdict(Enum):
    SAFE     = "✅ SAFE"
    VIOLATED = "❌ VIOLATED"
    BLOCKED  = "🛡️ BLOCKED by Friction"


# ─── Trace Recorder ─────────────────────────────────────────────────

@dataclass
class TraceStep:
    state: State
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


# ─── Main ────────────────────────────────────────────────────────────

def run_all():
    separator = "=" * 70
    
    for phase_name, simulate_fn in [
        ("PHASE 1: BASE MODEL (Unmitigated)", simulate_phase1),
        ("PHASE 2: MITIGATED MODEL (Contextual Friction)", simulate_phase2),
    ]:
        print(f"\n{separator}")
        print(f"  {phase_name}")
        print(separator)
        
        results = []
        
        for mask in Mask:
            for llm in LLMBehavior:
                trace, verdict = simulate_fn(mask, llm)
                results.append((mask, llm, verdict))
                
                print(f"\n{'─' * 60}")
                print(f"  Mask: {mask.value:10s} | LLM: {llm.value}")
                print(f"  Verdict: {verdict.value}")
                print(f"{'─' * 60}")
                print(fmt_trace(trace))
        
        # Summary table
        print(f"\n{'─' * 60}")
        print(f"  SUMMARY: {phase_name}")
        print(f"{'─' * 60}")
        print(f"  {'Mask':<12} {'LLM Behavior':<30} {'Verdict'}")
        print(f"  {'─'*12} {'─'*30} {'─'*20}")
        for mask, llm, verdict in results:
            print(f"  {mask.value:<12} {llm.value:<30} {verdict.value}")
    
    # Final comparison
    print(f"\n{separator}")
    print("  CROSS-PHASE COMPARISON: Safety Property")
    print(f"  \"Out-of-scope writes must not execute\"")
    print(separator)
    print(f"  {'Mask':<12} {'Phase 1':<25} {'Phase 2'}")
    print(f"  {'─'*12} {'─'*25} {'─'*25}")
    for mask in Mask:
        _, v1 = simulate_phase1(mask, LLMBehavior.OUT_SCOPE)
        _, v2 = simulate_phase2(mask, LLMBehavior.OUT_SCOPE)
        print(f"  {mask.value:<12} {v1.value:<25} {v2.value}")
    print()


if __name__ == "__main__":
    run_all()
