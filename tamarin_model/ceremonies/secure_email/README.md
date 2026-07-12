# secure_email ceremony

Proton-style secure email between **Alex** (sender) and **Blake** (recipient), in two pathways held in
one theory: **PGP** (public-key, fingerprint-verified) and **password** (passphrase shared out-of-band).
This is the PRIMARY ceremony for testing the stressor machinery, so it is deliberately abstracted down
to the human-factors layer.

## Design invariant: a breach is ALWAYS a human mistake

The email transport is a **private channel**, so the Dolev-Yao adversary (`Out()`) sees a secret **only**
when a human errs through a mask. There is no adversary-controlled keyserver and no open mail channel.
The only `Out()` emissions are:

| rule (`protocol.spthy`) | mistake | outcome |
|---|---|---|
| `IF_send_pgp_leak` | a credulous fingerprint **compare** accepted a non-correspondent | message sent out |
| `PW_deliver_misdeliver` | the address/send step went to the **wrong contact** | message + passphrase out |
| `PW_deliver_inband` | the passphrase was **leaked in-band** (Blake still reads → silent) | message out |

Happy-path email goes to a private `Mailbox`; the passphrase goes on a private `OobPw`. Alex and Blake
are each initiated **once**, and every human step is once-bounded.

## Crypto is abstracted (human-factors focus)

Following the alex_blake_kdf ceremony, keys/fingerprints are opaque handles rather than real
`aenc`/`senc`. The fingerprint offered to Alex is **adversary-mediated** `In(offered)`; the OOB reference
is the correspondent identity `'Blake'`. The Attentive mask **performs** the check (matches
`offered = 'Blake'`); a credulous mask accepts a substitute. Whether the send is safe is **derived** from
the committed recipient (`'Blake'` → private delivery; anything else → `Out`) — there is no
genuine/tampered *rule* branch, which keeps the all-traces search small.

## Addressing / verification are human actions

Choosing *who the message reaches* is a human action, and a degraded mask's response is what misdirects it:

- **PGP** — the fingerprint **compare** (`IF_verify_fp`) is the addressing decision; the accepted
  recipient routes the send (`IF_send_pgp_good` vs `IF_send_pgp_leak`).
- **Password** — the address/send **share** (`IF_btn_send_pw`) is the addressing decision; the share
  outcome (oob / misdeliver / inband-leak) routes the envelope (`PW_deliver_*`).

Protocol effects are folded into the interface rules (no `PReq_`/`P_` split).

## Performance discipline (why it proves fast)

Three points make it fast:

- **Pushed mask (core framework, Approach A)** — each stressor onset produces `!EffectiveMask(P,<its
  mask>)` *directly*, without reading the current mask or composing (no `!Compose`, no `_keep` twin). No
  producer of `!EffectiveMask` reads it, so its source graph is acyclic and refined-sources terminate in
  one step — this is what took the σ2/σ9 profiles from timeouts to seconds. Behaviours still read
  `!EffectiveMask` and act on the prompt (unchanged); the trade-off is a safe over-approximation of
  worst-mask-wins (a stressed human may act as any active mask).
- **Selective load surface** — the ambient exposure prompts (confirm → σ8, decide → σ9, compute+deadline
  → σ1/σ3) are posed only when the profile arms the detector that reads them (`#ifdef`). An unread prompt
  is pure branching that multiplies the all-traces search (lesson 15b).
- **Single-`In` compare, derived verdict** — one `verify` rule with `In(offered)`, tamperedness derived
  (lesson 14). A genuine/tampered *producer branch* doubles the search.

## Profiles

| profile | stressors | headline |
|---|---|---|
| `S0_baseline` | none | both pathways deliver; secrecy is absolute |
| `S1_trio_pgp` | σ6 Abstraction, **σ2** Concurrency | degraded compare → wrong-recipient send |
| `S2_trio_pw` | σ1 Load, σ3 Deadline, **σ9** AlertVolume | degraded address/send → misdeliver or silent in-band leak |
| `S3_trio_mixed` | σ6 Abstraction, **σ8** Habituation, Anxiety | two compare failures + the Fearful freeze (degradation that *helps*) |
| `S4_worstcase` | σ1, σ3, σ6, Anxiety, **σ2** + `PROPERTIES` | reachability + secrecy pair + agnostic attribution over a broad set |
| `S5_cue_phish` | σ_CUE (authority cue) | phishing: a persuasion cue → Naive → credulous compare → leak; the Naive is attributable to the cue |
| `S6_recovery_habituation` | σ8 + recovery | Habituated recovers via a **mode-break**, *not* a warning (matched recovery) |
| `S7_recovery_careless` | σ2 + recovery | Careless recovers via a **warning**, *not* a mode-break (matched recovery) |

**One density detector per profile.** The three *density* detectors — σ2 (concurrency, matches any two
prompts), σ8 (habituation, two `confirm`s), σ9 (alert-volume, three `decide`s) — may not share a
profile: stacking them overruns the all-traces mask-interleaving proof search. So each lives in exactly
one profile (σ2→S1 & S4, σ9→S2, σ8→S3). A single density detector alongside any number of single-prompt
detectors is fine (S4 = 5 detectors, ~2 min). Bold marks each profile's density detector.

**Stressor mechanism families.** A detector reads some slice of the trace/state and maps it to a mask:
*lookup / dose-response* (this step's demand band → σ1/σ3/σ6/anxiety), *density / count* (k co-present
prompts → σ2/σ8/σ9), *additive* (sub-threshold sum), *history* (a prior-state marker → σ10), and
*cue / persuasion* — the same lookup shape but on a persuasion dimension (`!Cue(action, principle,
level)`; authority/urgency/familiarity) → Naive. `SIGMA_CUE` + `CUE_PHISH` is the social-engineering
axis (S5): the attacker's only lever is the cue, and the human mistake stays the sole leak route.

**Matched recovery.** Returning to Attentive must fit the degrade's driver, so recovery is per-mask: a
re-engagement **warning** recovers Careless (salience) but not Habituated (warnings habituate); a
forcing-function **mode-break** recovers Habituated (resets automaticity) but not Careless. Each
`Recover_*` rule (`core/knobs.spthy`, opt-in via `RECOVERY_WARNING` / `RECOVERY_MODEBREAK`) reads the
specific degrade mask and emits `SetMask(P,'Attentive')`; the `MASK_RECOVERY` restrictions
(`core/framework.spthy`) make that event deactivate the degrade. S6/S7 prove each mask recovers *only*
via its matched intervention; a mask with no matched recovery armed simply never returns.

Prove one with:

```bash
export PATH="$HOME/.local/bin:$PATH"
python3 .claude/skills/model-tamarin/check.py --prove tamarin_model/ceremonies/secure_email/S0_baseline.spthy
```

## Layers

`base.spthy` fixes the flags constant across profiles (compare / share / authorize behaviours, the
degraded-click row, the novice lexicon) and assembles the layers in order:
`framework → protocol → demands → masks → stressors → knobs → properties → lemmas`. Each profile
`#define`s its stressors, then `#include "base.spthy"`, then its own lemmas.

---

## Prover budget & timings

**Hard requirement: every theorem proves in under 3 minutes.** Run capped — the box has no swap, so an
unbounded proof must abort rather than OOM the machine:

```bash
export MAUDE_LIB=/usr/share/maude        # else tamarin cannot find prelude.maude (false FAILs)
python3 .claude/skills/model-tamarin/check.py --prove --timeout 178 \
        ceremonies/secure_email/S4_worstcase.spthy -- +RTS -M6G -RTS
```

| Profile | pathway | stressors (mask) | time | lemmas |
|---|---|---|---|---|
| `S0_baseline` | PGP+PW | — | 5s | 8 |
| `S1_trio_pgp` | PGP | σ6 (Naive) + σ2 (Careless) + skipcheck + **premature** | 14s | 11 |
| `S2_trio_pw` | PW | σ1 + σ3 (Busy) → misdeliver | 33s | 10 |
| `S3_trio_mixed` | PGP | σ6 + σ8 + anxiety on **Blake** (Naive/Habituated/Fearful) | 25s | 11 |
| `S4_worstcase` | PGP | σ6 + σ2 + anxiety + every outcome row + `PROPERTIES` | 27s | 15 |
| `S5_cue_phish` | PGP | σ_CUE (Naive) | 3s | 10 |
| `S6_recovery_habituation` | PGP | σ8 + recovery (Blake) | 11s | 9 |
| `S7_recovery_careless` | PGP | σ2 + recovery | 67s | 9 |
| `S8_transcribe` | PGP | σ2 (Careless) → subject leak + TLS misroute | 6s | 10 |
| `S9_transcribe_slip` | PGP | σ_ADDITIVE (Busy) → field slip (safe-fail) | 5s | 9 |
| `S10_pw_inband_leak` | PW | σ2 (Careless) → in-band leak (silent) | 33s | 10 |

## What keeps it in budget (learned the hard way)

These are not style preferences — each one was the difference between a proof and a non-terminating
search. Break any of them and the theory stops proving.

1. **Gate the PATHWAY per profile** (`PATH_PGP` / `PATH_PW`). With both pathways compiled in, every
   theory carried the whole two-pathway/two-party surface and only ONE stressor fitted in 3 min.
   Compiled alone a pathway is half the surface — the σ6+σ2 trio went from **>3 min to 13s**.
2. **Density detectors read a SINGLE marker**, never "any N of M `!Demand`". σ2 reads `!Copresent(P)`,
   σ9 reads `!CopresentDecide(P)`. The "any two/three of N" form is an O(N²)/O(N³) lookup that explodes
   the source saturation once a real screen poses many co-present controls.
3. **Exposure-only controls emit `!Demand` WITHOUT a `Prompt`.** Density *counts* posed controls; the
   mask *answers* `Prompt`. So a control that drives no outcome (badges, Reply, overflow, reply-route) is
   counted for free — performing it is pure branching (lesson 15b).
4. **Keep every `Prompt` producer SHALLOW** — posed off `AlexInit` or the persistent `!AlexScreen` anchor,
   never off a deep linear chain. (Audited: every screen rule reads only init/persistent/`Fr`/`In`.)
5. **The send EFFECT joins ONE free-valued `!StepData`** (the recipient, from the compare). A second one
   opened source chains that never closed.
6. **Prove the boundary list ONCE as `[reuse]`** (`H_leak_routes`). The per-profile T6 then costs 8 steps
   instead of 261.
7. **Busy is the expensive mask** (its slips mint fresh terms). `SIGMA_ADDITIVE` is the cheap route to it
   (S9: 93s under σ1 → **5s** under σ_ADDITIVE). Where a story needs Busy AND Careless, SPLIT it by mask
   (S8/S9 for transcribe, S2/S10 for the share) rather than raise the timeout.

## See also

- [`INTERFACE_MAP.md`](INTERFACE_MAP.md) — the screen/control inventory (design), with an as-built caveat.
- [`../../docs/DIVERGENCES.md`](../../docs/DIVERGENCES.md) — **where the build departed from the plan, why,
  and what is weaker as a result.** Read this before citing the model.
- [`../../docs/RFC_GUIDANCE.md`](../../docs/RFC_GUIDANCE.md) — the generated, proof-backed requirements.
