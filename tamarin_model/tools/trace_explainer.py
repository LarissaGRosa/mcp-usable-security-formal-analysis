#!/usr/bin/env python3
"""
trace_explainer.py -- explain and ILLUSTRATE a theorem's trace in mask terms (ceremony-agnostic).

Given a profile .spthy and a lemma name, runs tamarin-prover with --output-json to obtain the
FOUND TRACE (an exists-trace lemma that verified, or an all-traces lemma that was falsified --
i.e. a counterexample), then narrates the trace in the core/ vocabulary:

  * WHAT changed the human's mask   -- every SetMask(P,m) node: the detector rule that fired and
    the trigger facts it read (!Demand prompts, !Demands lexicon rows, !Copresent, !UnderDeadline,
    !Cue, !Failed, ...);
  * HOW the masked human performed  -- every RespMask(P,m) node: the action class (the consumed
    Prompt), what the interface DISPLAYED vs what the human COMMITTED (!StepData), the outcome
    labels (Slip / Mistake / LeakPw / ...), and whether the behaviour deviated from Attentive
    (the Mask(P,'Attentive',m) deviation marker);
  * the EFFECTS                     -- which ceremony rules consumed the committed value or the
    outcome tokens, what reached the public network (Out) and the adversary (!KU / K);
  * a TIMELINE                      -- the whole trace as one readable line per event, tagged with
    the repo layer glyphs (blue protocol / orange interface / red stressor / green mask).

--illustrate FILE.md additionally writes a Markdown report whose first section is a mermaid
sequence diagram of the trace (lanes: interface, each human, ceremony, adversary; mask changes
as red notes on the human's lane) -- it renders in the VS Code Markdown preview and on GitHub.

It is ceremony-AGNOSTIC: the analysis keys ONLY on core/ facts (SetMask, RespMask, Mask, Prompt,
!Demand, !Displayed, !StepData, !EffectiveMask, the outcome labels). Ceremony rules are narrated
from their own names and facts, never from a hard-coded list, so any ceremony built on core/
(alex_blake_kdf, secure_email, future ones) works unchanged.

Usage (from the repo root):
    python3 tamarin_model/tools/trace_explainer.py PROFILE.spthy --lemma NAME [--timeout 178]
    python3 tamarin_model/tools/trace_explainer.py PROFILE.spthy --lemma NAME --illustrate out.md
    python3 tamarin_model/tools/trace_explainer.py --json saved_trace.json     # skip the prover

The prover run follows the repo budget (MEMORY.md lesson 25): MAUDE_LIB defaults to
/usr/share/maude and the RTS heap is capped (+RTS -M6G -RTS); default timeout 178 s.

Exit codes: 0 explained (or property verified with nothing to explain) | 1 prover error /
lemma not found / timeout | 2 usage.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from collections import defaultdict, deque

# ---------------------------------------------------------------- core glossaries
# Masks and outcome labels live in core/ (masks.spthy, stressors.spthy, framework.spthy) and are
# shared by every ceremony -- this is what makes the explainer ceremony-agnostic. Unknown labels
# are still reported (raw), so a new core outcome degrades to a plain mention, never a miss.
MASKS = {
    "'Attentive'":  "baseline: performs the step as designed (checks references before accepting)",
    "'Busy'":       "cognitively loaded: slips -- commits a fresh WRONG value, or auto-approves",
    "'Careless'":   "disengaged: stalls (safe-fail), skips checks, leaks in-band, or misroutes",
    "'Naive'":      "over-trusting: accepts ANY offered artifact without checking (credulous)",
    "'Fearful'":    "anxious: freezes / actively refuses to proceed (abort)",
    "'Habituated'": "warning-fatigued: clicks through confirmations without reading (auto-approve)",
}
OUTCOMES = {  # action label -> (severity, phrase); severity: BAD > SAFE > OK
    "Slip":             ("BAD",  "committed a fresh WRONG value in place of the intended one"),
    "Mistake":          ("BAD",  "accepted / set something unsafe"),
    "LeakPw":           ("BAD",  "sent the secret IN-BAND (readable channel)"),
    "MisdeliveredPw":   ("BAD",  "sent the secret to the WRONG recipient"),
    "TranscribeLeak":   ("BAD",  "typed the value into a field that EXPORTS it"),
    "AutoApprove":      ("BAD",  "approved without verifying the claim"),
    "PrematureGrant":   ("BAD",  "granted BEFORE the upstream check completed"),
    "Misroute":         ("BAD",  "advanced down the WRONG route"),
    "Timeout":          ("SAFE", "stalled / dismissed -- the step did not complete (safe-fail)"),
    "Abort":            ("SAFE", "actively refused to proceed (safe-fail)"),
    "LeakAverted":      ("SAFE", "answered carelessly but the field design averted the leak"),
    "Verify":           ("OK",   "performed the comparison"),
    "Verified":         ("OK",   "verified the claim before approving"),
    "Accept":           ("OK",   "accepted the artifact"),
    "Authorized":       ("OK",   "granted the authorization"),
    "Handled":          ("OK",   "handled the decision"),
    "Typed":            ("OK",   "entered a value"),
    "ShareOOB":         ("OK",   "shared over the out-of-band channel"),
    "SetPolicy":        ("OK",   "set the policy"),
}
SEV_MARK = {"BAD": "!!", "SAFE": "~", "OK": ""}
# trigger-context facts a stressor detector reads (premise name -> renderer)
TRIGGERS = {
    "!Demand":        lambda t: f"the interface posed prompt {t[1]} ({t[2]})",
    "!Demands":       lambda t: f"lexicon: a {t[0]} step rates {t[1]}={t[2]}",
    "!AtLeast":       lambda t: f"level {t[0]} reaches the {t[1]} threshold",
    "!Copresent":     lambda t: "the screen showed >=2 co-present controls",
    "!CopresentDecide": lambda t: "the screen showed >=3 co-present DECIDE controls",
    "!UnderDeadline": lambda t: f"prompt {t[0]} is under a deadline",
    "!Urgent":        lambda t: f"prompt {t[0]} was made to look urgent (adversary-induced)",
    "!Cue":           lambda t: f"a persuasion cue on {t[0]}: {t[1]}={t[2]}",
    "!Failed":        lambda t: f"{t[0]} had a prior failure",
}
SEED_PREFIXES = ("Seed_", "Init_", "Enable_")   # core setup rules, collapsed in the narrative
GLYPH = {"seed": "\U0001F7E3", "interface": "\U0001F7E0", "stressor": "\U0001F534",
         "mask": "\U0001F7E2", "ceremony": "\U0001F535", "adversary": "⚫"}


# ---------------------------------------------------------------- prover
def run_prover(path, lemma, timeout, heuristic=None):
    tam = shutil.which("tamarin-prover")
    if not tam:
        sys.exit("ERROR: tamarin-prover not on PATH (export PATH=\"$HOME/.local/bin:$PATH\").")
    jpath = tempfile.mktemp(suffix=".json", prefix="trace_")
    cmd = [tam, os.path.basename(path), f"--prove={lemma}", f"--output-json={jpath}"]
    if heuristic:
        cmd.append(f"--heuristic={heuristic}")
    cmd += ["+RTS", "-M6G", "-RTS"]
    env = dict(os.environ)
    env.setdefault("MAUDE_LIB", "/usr/share/maude")
    print("$ " + " ".join(cmd), file=sys.stderr)
    try:  # run from the theory's directory so relative #include paths resolve
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=os.path.dirname(os.path.abspath(path)), env=env)
    except subprocess.TimeoutExpired:
        sys.exit(f"TIMEOUT after {timeout}s -- proof did not terminate (MEMORY.md lesson 25).")
    out = p.stdout + p.stderr
    m = re.search(rf"^\s*({re.escape(lemma)}\S*)\s*\((all-traces|exists-trace)\):\s*(.+?)\s*$",
                  out, re.M)
    if not m:
        print(out[-1500:], file=sys.stderr)
        sys.exit(f"ERROR: no verdict for lemma '{lemma}' (typo? not in this profile?).")
    return m.group(1), m.group(2), m.group(3), jpath


# ---------------------------------------------------------------- trace graph
class Node:
    def __init__(self, j):
        self.id = j["jgnId"]
        self.label = j["jgnLabel"]
        self.type = j.get("jgnType", "")
        meta = j.get("jgnMetadata") or {}
        unpack = lambda fs: [(f["jgnFactName"], f["jgnFactShow"],
                              [t.get("jgnShow", t.get("jgnConst", "?")) for t in f["jgnFactTerms"]])
                             for f in (fs or [])]
        self.prems, self.acts, self.concs = (unpack(meta.get(k))
                                             for k in ("jgnPrems", "jgnActs", "jgnConcs"))

    def act(self, name):   return [f for f in self.acts if f[0] == name]
    def prem(self, name):  return [f for f in self.prems if f[0] == name]
    def conc(self, name):  return [f for f in self.concs if f[0] == name]

    @property
    def kind(self):
        if self.type != "isProtocolRule":                       return "adversary"
        if self.act("SetMask"):                                 return "stressor"
        if self.act("RespMask"):                                return "mask"
        if self.label.startswith(SEED_PREFIXES):                return "seed"
        if any(f[0] in ("Prompt", "!Demand") for f in self.concs): return "interface"
        return "ceremony"

    @property
    def party(self):
        for f in self.acts + self.concs:
            if f[0] in ("SetMask", "RespMask", "Prompt", "!EffectiveMask", "!Demand"):
                return f[2][0]
        return None

    @property
    def prompt_action(self):
        pr = self.prem("Prompt")
        return pr[0][2][2] if pr else "?"


class Trace:
    def __init__(self, g):
        self.label = g.get("jgLabel", "")
        self.nodes = {n.id: n for n in (Node(j) for j in g["jgNodes"])}
        self.flows = []                       # (src node, conc idx, dst node, prem idx)
        order_edges = defaultdict(set)        # producer -> consumers (all relations)
        port = re.compile(r"^(#[\w.]+?)(?::([cp])(\d+))?$")
        for e in g["jgEdges"]:
            s, d = port.match(e["jgeSource"]), port.match(e["jgeTarget"])
            if not (s and d) or s.group(1) not in self.nodes or d.group(1) not in self.nodes:
                continue
            order_edges[s.group(1)].add(d.group(1))
            if s.group(2) == "c" and d.group(2) == "p":
                self.flows.append((s.group(1), int(s.group(3)), d.group(1), int(d.group(3))))
        self.order = self._topo(order_edges)

    def _topo(self, edges):
        indeg = {i: 0 for i in self.nodes}
        for s, ds in edges.items():
            for d in ds:
                indeg[d] += 1
        q = deque(sorted(i for i, k in indeg.items() if k == 0))
        out = []
        while q:
            i = q.popleft(); out.append(i)
            for d in sorted(edges.get(i, ())):
                indeg[d] -= 1
                if indeg[d] == 0:
                    q.append(d)
        return out + sorted(set(self.nodes) - set(out))   # cycles (shouldn't happen): append

    def ordered(self, kind=None):
        ns = [self.nodes[i] for i in self.order]
        return [n for n in ns if kind is None or n.kind == kind]

    def consumers(self, nid):
        """[(fact-name, fact-show, consumer Node)] for every conclusion of nid that flows on."""
        out = []
        for s, ci, d, _ in self.flows:
            if s == nid and ci < len(self.nodes[s].concs):
                f = self.nodes[s].concs[ci]
                out.append((f[0], f[1], self.nodes[d]))
        return out

    def descendants(self, nid):
        seen, q = set(), deque([nid])
        kids = defaultdict(set)
        for s, _, d, _ in self.flows:
            kids[s].add(d)
        while q:
            for d in kids.pop(q.popleft(), ()):
                if d not in seen:
                    seen.add(d); q.append(d)
        return seen


# ---------------------------------------------------------------- narration
def fshow(fact):  return fact[1].replace("\n", " ")


def clean(s):
    """mermaid-safe text: pairs <a,b> would be read as HTML, ; ends a statement."""
    return s.replace("<", "⟨").replace(">", "⟩").replace(";", ",")


def summarize(n):
    """One plain-language line per trace event -- shared by the timeline and the diagram."""
    if n.kind == "stressor":
        p, m = n.act("SetMask")[0][2]
        return f"{p}: mask => {m}  (detector {n.label})"
    if n.kind == "mask":
        p, m = n.act("RespMask")[0][2]
        outs = [f"{o[0]}{SEV_MARK[OUTCOMES[o[0]][0]]}" for o in n.acts if o[0] in OUTCOMES]
        txt = f"{p} performs {n.prompt_action} as {m}"
        if n.act("Mask"):
            txt += " (DEVIATION)"
        if outs:
            txt += " => " + ", ".join(outs)
        commit = n.conc("!StepData")
        if commit:
            txt += f"; commits {commit[0][2][2]}"
        return txt
    if n.kind == "interface":
        posed = [f"poses {f[2][2]} to {f[2][0]}" for f in n.conc("Prompt")]
        shown = [f"shows {f[2][2]}" for f in n.conc("!Displayed")]
        if posed or shown:
            return f"{n.label}: " + "; ".join(posed + shown)
        return f"{n.label}: " + "; ".join(fshow(f) for f in n.acts[:2])
    if n.kind == "adversary":
        return (n.label if n.type == "unsolvedActionAtom"
                else f"{n.label}: " + "; ".join(fshow(f) for f in n.acts[:1]) or n.label)
    # seed / ceremony
    outs = [fshow(f) for f in n.concs if f[0] == "Out"]
    keys = [fshow(f) for f in n.acts[:2]]
    bits = keys + ([f"-> PUBLIC network: {o}" for o in outs])
    return f"{n.label}" + (": " + "; ".join(bits) if bits else "")


def explain(trace, out):
    nodes = trace.nodes
    say = out.append

    # --- mask timeline per party -------------------------------------------------
    say("## Mask story (what changed the human node's mask, and why)\n")
    initial = [n for n in nodes.values()
               if n.conc("!EffectiveMask") and not n.act("SetMask")]
    for n in initial:
        for f in n.conc("!EffectiveMask"):
            say(f"- {f[2][0]} starts as {f[2][1]} -- {MASKS.get(f[2][1], 'initial mask')} "
                f"(rule `{n.label}`)")
    changes = [n for n in trace.ordered() if n.act("SetMask")]
    if not changes:
        say("- no SetMask event in this trace: the human's mask NEVER changed "
            "(every step below was performed under the initial mask).")
    for n in changes:
        p, m = n.act("SetMask")[0][2]
        # onset = the detector's own labels; drop SetMask itself and restriction-support
        # actions (Neq/NeqAdd inequality guards), which are proof plumbing, not the story
        onset = [f for f in n.acts if f[0] != "SetMask" and not f[0].startswith("Neq")]
        why = [TRIGGERS[f[0]](f[2]) for f in n.prems if f[0] in TRIGGERS]
        say(f"\n**MASK CHANGE** -- detector `{n.label}` pushed {p}'s mask to {m}"
            + (f" (onset action: {', '.join(fshow(f) for f in onset)})" if onset else ""))
        say(f"  - {m}: {MASKS.get(m, 'a degraded mask')}")
        for w in why:
            say(f"  - because {w}")

    # --- how the masked human performed each step ---------------------------------
    say("\n## Human steps (how the mask performed each prompted action)\n")
    mask_nodes = trace.ordered("mask")
    if not mask_nodes:
        say("- the human performed no prompted step in this trace.")
    for n in mask_nodes:
        p, m = n.act("RespMask")[0][2]
        say(f"**{p} performs {n.prompt_action} as {m}** (rule `{n.label}`)")
        dev = n.act("Mask")
        if dev:
            say(f"  - DEVIATION: acted as {dev[0][2][2]} where {dev[0][2][1]} was expected")
        for f in n.prem("!Displayed"):
            say(f"  - interface displayed: {f[2][2]}")
        for f in n.conc("!StepData"):
            say(f"  - human COMMITTED:     {f[2][2]}")
        for f in n.acts:
            if f[0] in OUTCOMES and f[0] not in ("Verify",):
                sev, phrase = OUTCOMES[f[0]]
                say(f"  - [{sev}] {f[0]}: {phrase}")
        # effects: who consumed what this human produced
        for fname, show, consumer in trace.consumers(n.id):
            verb = ("the adversary derived from" if consumer.kind == "adversary"
                    else f"ceremony rule `{consumer.label}` consumed")
            say(f"  - effect: {verb} {show}"
                + (" -> put on the PUBLIC network" if consumer.conc("Out") else ""))
        say("")

    # --- adversary reach -----------------------------------------------------------
    adv = trace.ordered("adversary")
    ku = [n.label for n in adv if n.type == "unsolvedActionAtom"]
    leaks = [fshow(f) for n in nodes.values() for f in n.concs if f[0] == "Out"]
    if adv or leaks:
        say("## Adversary reach\n")
        for l in leaks:
            say(f"- sent on the public network: {l}")
        if ku:
            say(f"- adversary knowledge used by this trace: {', '.join(ku)}")
        tainted = set()
        for n in mask_nodes + changes:
            if any(nodes[d].kind == "adversary" for d in trace.descendants(n.id)):
                tainted.add(n.label)
        if tainted:
            say(f"- adversary steps depend on human-node output from: "
                f"{', '.join(sorted(tainted))}")
        say("")

    # --- timeline: the whole trace, one readable line per event ---------------------
    say("## Timeline\n")
    say("Layers: " + " ".join(f"{GLYPH[k]} {k}" for k in
                              ("ceremony", "interface", "stressor", "mask", "adversary")) + "\n")
    seeds = trace.ordered("seed")
    if seeds:
        say(f"- {GLYPH['seed']} setup: " + ", ".join(f"`{n.label}`" for n in seeds))
    step = 0
    for n in trace.ordered():
        if n.kind == "seed":
            continue
        step += 1
        say(f"- {step}. {GLYPH[n.kind]} {summarize(n)}")


def mermaid(trace):
    """Sequence diagram of the trace: interface / humans / ceremony / adversary lanes."""
    humans, ids = [], {}
    for n in trace.ordered():
        p = n.party
        if p and n.kind in ("mask", "stressor", "interface") and p not in humans:
            humans.append(p)
    L = ["```mermaid", "sequenceDiagram", "  autonumber", "  participant IF as Interface"]
    for k, p in enumerate(humans):
        ids[p] = f"H{k}"
        L.append(f"  participant H{k} as {p.strip(chr(39))}")
    L.append("  participant CER as Ceremony")
    has_adv = (any(n.kind == "adversary" for n in trace.nodes.values())
               or any(f[0] == "Out" for n in trace.nodes.values() for f in n.concs))
    if has_adv:
        L.append("  participant ADV as Adversary")
    for n in trace.ordered():
        if n.kind == "seed":
            continue
        if n.kind == "interface":
            posed = n.conc("Prompt")
            shown = n.conc("!Displayed")
            for f in posed:
                h = ids.get(f[2][0])
                # pair the displayed observable with ITS prompt (same pid), not the screen's first
                d = next((s for s in shown if s[2][1] == f[2][1]), None)
                txt = f"pose {clean(f[2][2])}" + (f" / shows {clean(d[2][2])}" if d else "")
                if h:
                    L.append(f"  IF->>{h}: {txt}")
            if not posed:
                L.append(f"  Note over IF: {clean(n.label)}")
        elif n.kind == "stressor":
            p, m = n.act("SetMask")[0][2]
            L.append(f"  Note over {ids.get(p, 'IF')}: STRESSOR {clean(n.label)}<br/>mask => {clean(m)}")
        elif n.kind == "mask":
            p, m = n.act("RespMask")[0][2]
            dev = "(!) " if n.act("Mask") else ""
            outs = [o[0] + SEV_MARK[OUTCOMES[o[0]][0]] for o in n.acts if o[0] in OUTCOMES]
            commit = n.conc("!StepData")
            txt = (f"{dev}{clean(n.prompt_action)} as {clean(m)}"
                   + (" => " + ", ".join(outs) if outs else "")
                   + (f" / commits {clean(commit[0][2][2])}" if commit else ""))
            L.append(f"  {ids.get(p, 'IF')}->>CER: {txt}")
        elif n.kind == "ceremony":
            outs = n.conc("Out")
            if outs and has_adv:
                L.append(f"  CER->>ADV: {clean(fshow(outs[0]))} (rule {clean(n.label)})")
            elif n.acts:
                L.append(f"  Note over CER: {clean(n.label)}: {clean(fshow(n.acts[0]))}")
        else:  # adversary
            first = (f": {clean(fshow(n.acts[0]))}"
                     if n.acts and fshow(n.acts[0]) != n.label else "")
            L.append(f"  Note over ADV: {clean(n.label)}{first}")
    L.append("```")
    return L


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("file", nargs="?", help="profile .spthy (a self-contained theory)")
    ap.add_argument("--lemma", help="lemma to prove and explain (required with a .spthy)")
    ap.add_argument("--json", help="explain a saved --output-json trace instead of proving")
    ap.add_argument("--illustrate", metavar="FILE.md",
                    help="also write a Markdown report with a mermaid sequence diagram")
    ap.add_argument("--timeout", type=int, default=178, help="prover wall-clock (default 178)")
    ap.add_argument("--heuristic", help="pass a goal-ranking heuristic to the prover")
    ap.add_argument("--keep-json", action="store_true", help="print the trace-JSON path and keep it")
    args = ap.parse_args()

    header, verdict = [], None
    if args.json:
        jpath = args.json
        header.append(f"# Trace explanation ({os.path.basename(jpath)})\n")
    elif args.file and args.lemma:
        name, kind, result, jpath = run_prover(args.file, args.lemma, args.timeout, args.heuristic)
        verdict = (name, kind, result)
        header.append(f"# {name}  ({kind}): {result}\n")
        if kind == "all-traces" and result.startswith("verified"):
            header.append("Property holds on ALL traces -- there is no trace to explain (nothing "
                          "violates it). To SEE the mask machinery move, explain an exists-trace "
                          "chain lemma of this profile instead.")
            print("\n".join(header))
            return 0
        if result.startswith("falsified") and kind == "all-traces":
            header.append("FALSIFIED: the trace below is a COUNTEREXAMPLE -- the mask story that "
                          "breaks the property.\n")
        elif result.startswith("verified"):
            header.append("exists-trace VERIFIED: the trace below is the demonstrated behaviour "
                          "(this cascade is reachable in the model).\n")
        elif "incomplete" in result:
            sys.exit(f"ERROR: analysis incomplete for '{name}' -- no trace produced.")
    else:
        ap.print_usage()
        return 2

    try:
        graphs = json.load(open(jpath)).get("graphs", [])
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"ERROR: no readable trace JSON at {jpath} ({e}).")
    if not graphs:
        sys.exit("ERROR: the prover produced no trace graph.")

    out, report = list(header), list(header)
    for i, g in enumerate(graphs):
        t = Trace(g)
        if len(graphs) > 1:
            for o in (out, report):
                o.append(f"\n---\n# Trace {i + 1} of {len(graphs)}\n")
        report.append("## Illustration\n")
        report += mermaid(t)
        report.append("")
        narrative = []
        explain(t, narrative)
        out += narrative
        report += narrative
    if args.illustrate:
        with open(args.illustrate, "w") as f:
            f.write("\n".join(report) + "\n")
        print(f"(illustrated report written to {args.illustrate})", file=sys.stderr)
    print("\n".join(out))
    if args.keep_json and not args.json:
        print(f"\n(trace JSON kept at {jpath})", file=sys.stderr)
    elif not args.json:
        os.unlink(jpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
