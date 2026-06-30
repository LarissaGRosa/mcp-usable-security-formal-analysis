#!/usr/bin/env python3
"""
step_analyzer.py -- heuristic !Step / lexicon proposer (ROADMAP #8, the "analyzer direction").

Scans a .spthy protocol and, for each rule, looks for keyword signals that it is a human-interaction step,
then PROPOSES the agnostic annotation: an action tag (compute|compare|confirm|decide|authorize|share), the
!Step fact to add, and the lexicon rows the lookup detectors will need. Rules already carrying !Step are
reported as covered (and cross-checked against the heuristic). It is a *proposer*, not an oracle: it errs
toward recall (flagging candidates), so a designer confirms/rejects -- it should not MISS a human step.

Usage (from the repo root):
    python3 tamarin_model/tools/step_analyzer.py <file-or-dir.spthy> [...]
    python3 tamarin_model/tools/step_analyzer.py tamarin_model/ceremonies/secure_email/protocol
"""
import re, sys, pathlib

# action  <-  keyword signals (regexes, matched against the rule body with comments stripped)
SIGNALS = {
    "compute":   [r"\bkdf\b", r"\bsenc\b", r"sign\(", r"derive", r"passphrase", r"CALC"],
    "compare":   [r"verify", r"fingerprint", r"KeyChecked", r"\bcompare\b", r"VerifyReq", r"confirm_key"],
    "confirm":   [r"Prompt", r"Approve", r"approval", r"\bMFA\b", r"\bpush\b", r"auto_?approve",
                  r"Challenge", r"[Ll]ogin"],
    "decide":    [r"Decision", r"\bdecide\b", r"\bmenu\b", r"choose", r"\bselect\b", r"method"],
    "authorize": [r"AuthReq", r"authoriz", r"\bgrant\b"],
    "share":     [r"SHARE", r"\bshare\b", r"\bOob\b", r"password"],
}
LEXICON = {
    "compute":   ["!Demands('compute','MentalDemand','hi')", "!Demands('compute','TemporalDemand','hi')"],
    "compare":   ["!Demands('compare','Effort','hi')"],
    "authorize": ["!Demands('authorize','Arousal','hi')"],
    "share":     ["!Demands('share','MentalDemand','hi')", "!Demands('share','TemporalDemand','hi')"],
    "confirm":   ["(density: counted by σ8 Habituation; no lexicon row)"],
    "decide":    ["(density: counted by σ9 AlertVolume; no lexicon row)"],
}


def strip_comments(s):
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    return re.sub(r"//[^\n]*", " ", s)


def rules(text):
    parts = re.split(r"\n\s*rule\s+(\w+)\s*:", "\n" + text)
    for i in range(1, len(parts), 2):
        body = re.split(r"\n\s*(?:lemma|restriction|end)\b", parts[i + 1])[0]
        yield parts[i], body


def analyze(path, out):
    text = strip_comments(pathlib.Path(path).read_text())
    n_cov = n_prop = n_agree = 0
    hits = []
    for name, body in rules(text):
        annotated = re.findall(r"!Step\([^,]+,[^,]+,\s*'([\w-]+)'\s*\)", body)
        sig = {a: [p for p in pats if re.search(p, body)] for a, pats in SIGNALS.items()}
        sig = {a: m for a, m in sig.items() if m}
        if not sig and not annotated:
            continue
        hits.append((name, annotated, sig))
    if not hits:
        return (0, 0, 0)
    out.append(f"### {path}")
    for name, annotated, sig in hits:
        proposed = sorted(sig, key=lambda a: -len(sig[a]))
        if annotated:
            n_cov += 1
            ok = "✓ matches heuristic" if set(annotated) & set(proposed) else "⚠ heuristic differs"
            if set(annotated) & set(proposed):
                n_agree += 1
            out.append(f"- `{name}`: COVERED — !Step action `{annotated[0]}` "
                       f"({ok}; signals: {', '.join(proposed) or 'none'})")
        else:
            n_prop += 1
            top = proposed[0]
            why = ", ".join(s.strip(r'\b') for s in sig[top])
            out.append(f"- `{name}`: CANDIDATE `{top}` step (signal: {why})")
            out.append(f"    propose: `!Step(P, sid, '{top}')`"
                       + ("" if top in ("confirm", "decide") else f"  + lexicon {', '.join(LEXICON[top])}"))
            if len(proposed) > 1:
                out.append(f"    (also matched: {', '.join(proposed[1:])} — confirm/reject)")
    return (n_cov, n_prop, n_agree)


def main():
    targets = []
    for a in sys.argv[1:]:
        p = pathlib.Path(a)
        targets += sorted(p.glob("*.spthy")) if p.is_dir() else [p]
    if not targets:
        print(__doc__); return 1
    out, cov, prop, agree = [], 0, 0, 0
    for t in targets:
        c, pr, ag = analyze(str(t), out)
        cov += c; prop += pr; agree += ag
    print("# !Step / lexicon proposals (heuristic)\n")
    print(f"**{cov} rules already annotated ({agree} agree with the heuristic), "
          f"{prop} unannotated candidates proposed.**\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
