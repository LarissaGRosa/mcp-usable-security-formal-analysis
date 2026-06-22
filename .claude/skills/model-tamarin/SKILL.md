---
name: model-tamarin
description: >
  Write, model, build, check, lint, prove, and debug Tamarin .spthy protocol /
  security-ceremony files. Use when authoring or editing Tamarin theories —
  multiset-rewrite rules, SAPIC+ processes, lemmas (trace properties),
  restrictions, accountability, or fixing partial deconstructions / sources /
  non-terminating proofs. Ships check.py to run tamarin-prover and report a
  PASS/FAIL verdict per lemma.
---

# Modeling Tamarin (.spthy) files

This skill helps you author Tamarin theories for the Ceremony-Mask framework and
**verify them with the real prover** instead of eyeballing syntax. The harness is
[.claude/skills/model-tamarin/check.py](.claude/skills/model-tamarin/check.py): it
runs `tamarin-prover`, parses the `summary of summaries` block, and prints a
PASS/FAIL line per lemma with a wall-clock timeout (Tamarin proofs can run
forever — see [Sources & precomputation](#sources--precomputation)).

The reference below is distilled from the Tamarin manual chapters 3–9. **Verify
syntax by running `check.py`, not by trusting prose** — Tamarin's well-formedness
checker catches most mistakes in <1s. Paths in this file are relative to the repo
root (`stronger_usability_masks/`).

Verified with Tamarin **1.12.0** + Maude **3.5.1** on Ubuntu 22.04 (x86_64), headless.

---

## Prerequisites

Tamarin ships as a prebuilt static-ish Linux binary; you do **not** need the
Haskell toolchain. Maude is its only runtime dependency.

```bash
# Maude 3.5.1 (the rewriting engine Tamarin shells out to). Extract the WHOLE zip
# next to the binary — Tamarin needs the bundled prelude*.maude files at runtime.
which maude || (cd /tmp && curl -sL -o maude.zip \
  https://github.com/maude-lang/Maude/releases/download/Maude3.5.1/Maude-3.5.1-linux-x86_64.zip \
  && unzip -o maude.zip -d "$HOME/.local/bin" && chmod +x "$HOME/.local/bin/maude")

# Tamarin 1.12.0 prebuilt linux64 binary
cd /tmp && curl -sL -o tamarin.tar.gz \
  https://github.com/tamarin-prover/tamarin-prover/releases/download/1.12.0/tamarin-prover-1.12.0-linux64-ubuntu.tar.gz \
  && tar xzf tamarin.tar.gz -C /tmp \
  && install -m 755 /tmp/tamarin-prover "$HOME/.local/bin/tamarin-prover"

export PATH="$HOME/.local/bin:$PATH"
tamarin-prover --version        # prints versions and ends with "checking installation: OK."
```

> On this machine Maude was already at `~/.local/bin/maude`; only the Tamarin
> download was needed. `tamarin-prover --version` runs the install self-check —
> if it can't find `maude` on PATH it says so there.

---

## Check / prove a theory (agent path) — START HERE

`check.py` is the harness. Default mode **lints** (load + well-formedness, no
proving, ~0.2s); `--prove` actually discharges the lemmas.

```bash
export PATH="$HOME/.local/bin:$PATH"
S=.claude/skills/model-tamarin

# Lint: parse + well-formedness only. Fast. Run this after EVERY edit.
python3 $S/check.py $S/examples/first_example.spthy

# Prove every lemma (PASS only if all verified)
python3 $S/check.py --prove $S/examples/first_example.spthy

# Prove a single lemma by name/prefix (others reported as "skip")
python3 $S/check.py --lemma Client_session_key_secrecy $S/examples/first_example.spthy

# Cap runtime so a non-terminating proof can't hang you (default 300s)
python3 $S/check.py --prove --timeout 120 $S/examples/first_example.spthy

# Hard cases: pick a heuristic or an oracle (see Sources section)
python3 $S/check.py --prove --heuristic C $S/examples/first_example.spthy
python3 $S/check.py --prove --oracle ./my.oracle $S/examples/first_example.spthy
```

Verified output for `--prove first_example.spthy`:

```
LEMMA                                    KIND          VERDICT
------------------------------------------------------------------------
ok   Client_session_key_secrecy          all-traces    verified (5 steps)
ok   Client_session_key_honest_setup     exists-trace  verified (5 steps)

PASS
```

Verdict marks: `ok` verified · `FAIL` falsified (or incomplete in full-prove
mode) · `skip` unselected/lint · prints `PASS`/`FAIL` and exits `0`/`1`.
A falsified lemma prints `falsified - found trace (N steps)` and exits 1.

**Raw prover** (what check.py wraps): `tamarin-prover FILE --prove`. For a visual
proof tree, `tamarin-prover interactive FILE` serves a GUI at
`http://127.0.0.1:3001` — useless headless; the CLI is the agent path.

Runnable, verified example fixtures live in
[.claude/skills/model-tamarin/examples/](.claude/skills/model-tamarin/examples/):
`first_example.spthy` (rules + secrecy lemma) and `process_example.spthy` (SAPIC+).

---

## Theory skeleton

```
theory MyProtocol
begin

builtins: hashing, asymmetric-encryption     // optional, comma-separated
functions: kdf/2                               // optional custom symbols
equations: ...                                 // optional custom equations
macros: m(x) = h(<x,x>)                         // optional global lets

// rules, restrictions, lemmas, or a `process:` block go here

end                                            // REQUIRED — omitting it gives
                                               // "unexpected end of input"
```

---

## Terms & built-in theories (manual ch. 4)

Messages are symbolic terms: constants, fresh names, or `f(t1,…,tn)`. Pairing is
built in: `<x,y>` = `pair(x,y)`, with `fst`/`snd`; `<a,b,c>` nests rightward.

| Sort / form | Written | Meaning |
|---|---|---|
| public constant | `'name'` | known to everyone incl. adversary |
| fresh | `~x` | unique random value (from `Fr(~x)`) |
| public var | `$A` | agent id / public value |
| temporal | `#i` | a timepoint (lemmas only) |
| nat | `%n` / `n:nat` | small counter (needs `natural-numbers`) |
| plain | `x` | any message, rule-instantiation-bound |

Declare your own: `functions: f/2, g/1 [private]` (private = adversary can't
apply it). `equations: dec(enc(m,k),k) = m` — **every RHS variable must appear on
the LHS**; keep equations subterm-convergent or proofs may not terminate.
Reserved (don't redeclare): `mun one exp mult inv pmult em`.

| builtin | gives you | key equation |
|---|---|---|
| `hashing` | `h/1` | — |
| `symmetric-encryption` | `senc/2 sdec/2` | `sdec(senc(m,k),k)=m` |
| `asymmetric-encryption` | `aenc/2 adec/2 pk/1` | `adec(aenc(m,pk(sk)),sk)=m` |
| `signing` | `sign/2 verify/3 pk/1 true` | `verify(sign(m,sk),m,pk(sk))=true` |
| `revealing-signing` | `revealSign revealVerify getMessage` | reveals `m` |
| `diffie-hellman` | `^ * inv/1 1` | `(x^y)^z = x^(y*z)`, `x^1=x` |
| `bilinear-pairing` | DH + `pmult em` | `em(p,q)=em(q,p)` |
| `xor` | `⊕`/`XOR` `zero` | `x⊕x=zero`, `x⊕zero=x` |
| `multiset` | `++` (AC union) | — |
| `natural-numbers` | `%+ %1`, `⊏` ordering | — |

`aenc{x,y}pkB` is sugar for `aenc(<x,y>, pkB)`.

---

## Rules & facts (manual ch. 5)

A rule is **`[ premises ] --[ actions ]-> [ conclusions ]`** (use `-->` when there
are no action facts). Facts model state; **action facts** (the middle) are the
only thing lemmas can see.

```
rule Client_1:
    [ Fr(~k), !Pk($S, pkS) ]                 // consume fresh + read pubkey
  --[ Sent($S, ~k) ]->                        // action fact for lemmas
    [ Client_1($S, ~k), Out(aenc(~k, pkS)) ]  // store state + send to network
```

Special facts (built in): **`Fr(~x)`** fresh value (LHS only) · **`In(m)`** receive
from adversary (LHS only) · **`Out(m)`** send to adversary (RHS only) ·
**`K(m)`** adversary knowledge (lemmas only).

- **Linear** facts (`Client_1(...)`) are consumed when matched — model
  one-shot/threaded state. **Persistent** facts (`!Ltk(...)`, leading `!`) are
  never consumed — model long-term keys / reusable knowledge.
- Fact names start uppercase and must be used **consistently**: same name ⇒ same
  arity, case, persistence everywhere, or well-formedness fails (you'll see
  "Fact arity issues").
- Multi-step protocols thread a state fact carrying a fresh thread id `~tid` so
  later rules recover earlier values.
- `let x = h(t) in [ … ]` binds inside a rule; `macros:` shares bindings across
  all rules/lemmas (no forward references).

---

## Lemmas & property logic (manual ch. 7)

```
lemma name [attr, …]:
  "guarded first-order formula over action facts"
```

Guarded fragment, sorts incl. timepoints: quantifiers `All` / `Ex`; connectives
`&` `|` `==>` `not`; `F(args) @ #i` (action fact at timepoint); ordering `#i < #j`;
equality `#i = #j` or `x = y`; falsum `F`. **Guardedness**: a quantified var must
appear in an action constraint right after its quantifier — `All`'s body is an
implication, `Ex`'s body is a conjunction.

```
// all-traces (default): holds on every trace
lemma secrecy:
  "not (Ex k #i #j. Secret(k)@i & K(k)@j)"

// exists-trace: at least one trace satisfies it (sanity / reachability)
lemma can_complete [exists-trace]:
  "Ex #i. Finish()@i"

// typical authentication / injective-agreement shape
lemma unique:
  "All x #i #j. Once(x)@i & Once(x)@j ==> #i = #j"
```

Attributes: `[reuse]` (proven first, reused by later lemmas — great for helper
facts) · `[use_induction]` (force induction when simplification loops) ·
`[sources]` (a sources lemma, proven by induction during precomputation) ·
`[hide_lemma=L]` · `[left]`/`[right]`/`[diff_reuse]` (diff/observational-equiv
mode).

### Restrictions — constrain the traces Tamarin considers

Add an action fact in a rule, then a restriction that filters traces. Standard
patterns (copy verbatim):

```
restriction Equality:  "All x y #i. Eq(x,y)@i ==> x = y"
restriction Inequality:"All x #i. Neq(x,x)@i ==> F"
restriction OnlyOnce:  "All #i #j. OnlyOnce()@i & OnlyOnce()@j ==> #i = #j"
restriction Unique:    "All x #i #j. Unique(x)@i & Unique(x)@j ==> #i = #j"
```

E.g. emit `--[ Eq(verify(sig,m,pk), true) ]->` to force a signature check.

---

## Processes — SAPIC+ (manual ch. 6)

An alternative to hand-written rules: write one `process:` block; Tamarin
translates it to rules. Constructs: `new n;` (fresh) · `in(x);` / `out(t);`
(default public channel, or `in(c,x)`/`out(c,t)`) · `if c then P else Q` ·
`let pat = t in P else Q` (destructors/pattern-match; else on failure) ·
`event F;` (→ action fact `F` for lemmas) · `P | Q` (parallel) · `!P`
(replication) · `0` (stop) · stateful `insert k,v` / `lookup k as x in … else …`
/ `delete k` / `lock t` / `unlock t`.

```
theory ProcExample begin
builtins: symmetric-encryption
process:
  new ~k;
  ( in(m); event Got(m); out(senc(m, ~k)) )
lemma can_run: exists-trace "Ex m #i. Got(m)@i"
end
```

This compiles and `can_run` verifies (see `examples/process_example.spthy`). You
can mix rules and a process, but the manual advises against it. Export to other
backends with `-m proverif|deepsec|msr|spthytyped`.

---

## Accountability (manual ch. 8)

Pinpoints *which* party's deviation caused a violation. Define `test`s (named
trace properties whose free vars name the blamed party), then a `lemma … account(s)
for "φ"`. A party is dishonest when `Corrupted(A)` is in the trace.

```
test leak_manager:  "Ex data #i. LeakManager(m, data)@i"
lemma acc:
  leak_manager, leak_employees account for
    "All data #i. Database(data)@i ==> not Ex #j. LeakData(data)@j"
```

Each accountability lemma expands to `6n+1` standard lemmas (n = #tests), all of
which must verify. Run with the same `tamarin-prover FILE --prove`.

---

## Sources & precomputation (manual ch. 9)

Before proving, Tamarin computes *sources* (where each premise fact can come
from). When it can't pin a fact's origin you get **partial deconstructions**
("X partial deconstructions left") — these cause looping / non-termination.

Fixes, in order of preference:
1. **Sources lemma** `lemma types [sources]: "…"` — relate each received term to
   either adversary knowledge `KU(t)@j` or a specific earlier `Out`, with
   `j < i`. Proven by induction during precomputation, then used to refine
   sources for every other lemma.
2. **`--auto-sources`** — let Tamarin synthesise the sources lemma. Pass it
   through: `python3 check.py --prove file.spthy -- --auto-sources`. No guarantee
   it's sufficient or correct, so re-check.
3. **Modeling tricks** — add `In(t)` on the LHS for publicly-derivable terms;
   pattern-match instead of destructors; tag terms with fresh/public sorts.

When proof search loops anyway, change the **goal-ranking heuristic** with
`--heuristic=` (default `s`): letters `s/S` smart, `c/C` consecutive, `i/I`
induction-friendly, `o/O` oracle, `p/P` (case sensitivity flips
loop-breaker/non-loop-breaker priority). For full control write an **oracle**
script and use `--heuristic=O --oraclename=FILE` (check.py: `--oracle FILE`).
Other knobs: `-c/--open-chains` (default 10), `-s/--saturation` (default 5),
`--precompute-only` to inspect deconstructions without proving.

---

## Gotchas (things I actually hit this session)

- **Missing `end`** → `"file" (line N): unexpected end of input … expecting …`.
  Every theory and every `process:` theory must close with `end`.
- **Fact arity/case clash** is the #1 well-formedness failure: using `St(~x)` in
  one rule and `St(~x,~y)` in another. Tamarin prints "Fact arity issues" and
  names both rules. Pick one shape.
- **"Facts occur in the LHS but not in any RHS"** — a typo'd/never-produced fact;
  Tamarin even suggests the rule you probably meant. A warning, but usually a real
  bug (a rule that can never fire).
- **`--prove` *and* `--prove=Name` together** makes Tamarin warn about an empty
  lemma arg. check.py sends exactly one form (that's why `--lemma` doesn't also
  add bare `--prove`).
- **Lint passes but proof never returns** = partial deconstructions. Don't wait —
  `check.py` times out at 300s by default; then add a `[sources]` lemma.
- **`exists-trace` lemma "verified"** means the good trace *exists* (a sanity
  check). It does **not** mean the property holds on all traces — that's the
  default `all-traces` mode. Always pair a sanity `exists-trace` with your
  `all-traces` security lemmas so you don't prove safety vacuously.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `tamarin-prover: command not found` | `export PATH="$HOME/.local/bin:$PATH"` (see Prerequisites) |
| `--version` fails at "checking version" | `maude` not on PATH; install it (Prerequisites) |
| `unexpected end of input` | add the closing `end` |
| `WARNING: … wellformedness checks failed!` | read the named section (arity/case/unbound var); check.py prints it and exits 1 |
| proof hangs / `check.py` TIMEOUT | partial deconstructions → add `[sources]` lemma or `--auto-sources`; or try `--heuristic C`/an oracle |
| `falsified - found trace` | the property is genuinely violated; open `tamarin-prover interactive FILE` to read the attack trace |
