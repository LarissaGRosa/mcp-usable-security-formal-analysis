#!/usr/bin/env python3
"""
check.py — drive the Tamarin prover over a .spthy theory and report a clean
verdict, with a wall-clock timeout so non-terminating proofs can't hang you.

This is the harness you use after writing or editing a Tamarin file: it runs
`tamarin-prover`, parses the "summary of summaries" block, and prints a compact
PASS/FAIL table. Exit code is 0 only if every selected lemma is proved (or, in
lint mode, the theory loads and is well-formed).

Modes:
  lint   (default)  -> `tamarin-prover FILE`            load + well-formedness, no proving (fast)
  prove  (--prove)  -> `tamarin-prover FILE --prove`    prove all lemmas

Usage:
  ./check.py THEORY.spthy                 # lint: parse + well-formedness only
  ./check.py --prove THEORY.spthy         # prove every lemma
  ./check.py --prove --lemma L1 THEORY.spthy   # prove only lemmas named/prefixed L1
  ./check.py --prove --timeout 120 THEORY.spthy
  ./check.py --prove --heuristic O --oracle ./my.oracle THEORY.spthy
  ./check.py --prove THEORY.spthy -- --auto-sources   # pass-through extra tamarin flags after --

Exit codes: 0 ok | 1 a lemma failed / timed out / not well-formed | 2 usage / tamarin missing
"""
import argparse, re, shutil, subprocess, sys

# matches e.g.  "  some_lemma (all-traces): verified (5 steps)"
VERDICT = re.compile(
    r"^\s*(?P<name>\S+)\s*\((?P<kind>all-traces|exists-trace)\):\s*(?P<result>.+?)\s*$"
)


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True, description="Check a Tamarin .spthy theory.")
    ap.add_argument("file", help="path to the .spthy theory")
    ap.add_argument("--prove", action="store_true", help="prove lemmas (default: lint only)")
    ap.add_argument("--lemma", action="append", default=[],
                    help="prove only this lemma name/prefix* (repeatable; implies --prove)")
    ap.add_argument("--timeout", type=int, default=300, help="wall-clock seconds (default 300)")
    ap.add_argument("--heuristic", help="goal-ranking heuristic, e.g. s S c C i I o O p P")
    ap.add_argument("--oracle", help="path to an oracle script (sets --heuristic=O if unset)")
    ap.add_argument("extra", nargs="*", help="extra tamarin flags after a literal --")
    args = ap.parse_args()

    tam = shutil.which("tamarin-prover")
    if not tam:
        print("ERROR: tamarin-prover not on PATH. See SKILL.md > Prerequisites.", file=sys.stderr)
        return 2

    cmd = [tam, args.file]
    if args.lemma:                       # prove only the named lemma(s)
        for l in args.lemma:
            cmd.append(f"--prove={l}")
    elif args.prove:                     # prove every lemma
        cmd.append("--prove")
    if args.oracle:
        cmd += ["--heuristic=O", f"--oraclename={args.oracle}"]
    elif args.heuristic:
        cmd.append(f"--heuristic={args.heuristic}")
    # argparse leaves the tokens after `--` in args.extra
    cmd += [a for a in args.extra if a != "--"]

    print("$ " + " ".join(cmd), file=sys.stderr)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"\nTIMEOUT after {args.timeout}s — proof did not terminate.", file=sys.stderr)
        print("  Likely partial deconstructions / unbounded search. See SKILL.md > Sources.",
              file=sys.stderr)
        return 1
    out = p.stdout + p.stderr

    # 1. parse errors (bad syntax)
    perr = re.search(r'^"[^"]+"\s*\(line \d+.*$', out, re.M)
    if perr:
        print("PARSE ERROR:\n  " + perr.group(0))
        ctx = out[perr.end():perr.end() + 400].strip().splitlines()
        for line in ctx[:4]:
            print("  " + line)
        return 1

    # 2. well-formedness failures
    wf_failed = "wellformedness check" in out and "failed" in out
    if wf_failed:
        print("WELL-FORMEDNESS FAILED:")
        m = re.search(r"WARNING: the following wellformedness checks failed!(.*?)(?:\*/|\Z)",
                      out, re.S)
        if m:
            for line in m.group(1).strip().splitlines()[:25]:
                print("  " + line)

    # 3. lemma verdicts
    verdicts = []
    in_summary = False
    for line in out.splitlines():
        if "summary of summaries" in line:
            in_summary = True
            continue
        if in_summary:
            m = VERDICT.match(line)
            if m:
                verdicts.append((m["name"], m["kind"], m["result"]))

    ok = not wf_failed
    full = args.prove and not args.lemma  # "prove everything" mode
    if verdicts:
        print(f"\n{'LEMMA':<40} {'KIND':<13} VERDICT")
        print("-" * 72)
        for name, kind, result in verdicts:
            if result.startswith("verified"):
                mark = "ok  "
            elif result.startswith("falsified"):
                mark = "FAIL"; ok = False
            elif result.startswith("analysis incomplete"):
                # incomplete is expected for lemmas we didn't ask to prove
                # (lint mode, or unselected lemmas in --lemma mode); only a
                # failure when we asked to prove *everything*.
                mark = "FAIL" if full else "skip"
                if full:
                    ok = False
            else:
                mark = "FAIL"; ok = False
            print(f"{mark} {name:<35} {kind:<13} {result}")
    elif not wf_failed:
        # no summary block and no error => loaded, lint clean, no lemmas (or process-only)
        if "analysis incomplete" in out or "processing time" in out:
            print("Theory loaded and is well-formed (no lemmas selected / lint mode).")
        else:
            print("No verdict summary found. Raw tail:")
            print("\n".join(out.splitlines()[-15:]))
            ok = False

    print("\n" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
