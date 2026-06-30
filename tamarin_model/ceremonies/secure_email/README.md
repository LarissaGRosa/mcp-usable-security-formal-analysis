# `secure_email` — ceremony C1 (two pathways, both parties masked)

A second toy ceremony for the ceremony-mask framework, modelling **how a human sends a secure
email** as described in `secure-email-generic-guide.html` (Proton / Mailfence / mailbox.org reduce
to the same methods over TLS + OpenPGP). It reuses the `core/` human layer (masks, stressors,
current-mask transitions) **verbatim**; only the crypto and the password-sharing masks are new.

## What it models

One sender (**Alex**) and one recipient (**Blake**), both routed through the mask machinery
(multi-party goal — either can be degraded). The recipient is initialised in one of two
mutually-exclusive flavours, which is the guide's *"choose how to send"* branch:

| Pathway | Recipient | Crypto | Human weak point (from the guide) |
|---|---|---|---|
| **PGP** (Method 2) | keyed (`!RecipientKey`) | `aenc(m, pk(skB))` | **skipped fingerprint verification** → encrypt to a substituted key |
| **Password** (Method 3) | keyless (`!Keyless`) | `senc(m, pw)` | **password not sent out-of-band** → in-band leak / misdelivery |

Both pathways live in **one theory**; `OneInstancePerHuman` picks one per trace, and the same
masks/stressors apply to each. The out-of-band side channel is the private fact `Oob(...)` the
Dolev-Yao adversary cannot read; "leaking" means putting the secret on `Out`.

### The human decisions (degraded by the reused masks)

- **VERIFY_KEY** (PGP) — `attentive_verify` accepts only a genuine fingerprint; `naive_verify`
  (under σ6 Abstraction) accepts a **tampered** one (`Mistake`) → message encrypted to the adversary.
- **SHARE_PW** (password) — `attentive_share` → out-of-band; `careless_share` (σ2
  ExternalDistraction) → **in-band leak** (`LeakPw`, silent compromise, recipient still reads);
  `busy_share` (σ3 TimePressure) → **wrong-recipient slip** (`MisdeliveredPw`, leak + recipient
  locked out). Because `pw_pathway` poses a SHARE_PW request for **both** the sender (compose) and
  the recipient (a phishing "confirm your password" page), the **recipient** is degradable too.

## Profiles

- **S0** (`S0_secure_email.spthy`) — stressors are **declared** (σ6 Abstraction on the key check,
  σ2/σ3 on the password share). 9 lemmas, ~3 s.
- **S1** (`S1_interface.spthy`) — the **sending interface generates the stressors**: each composer
  step records the objective operation it performs and the core *inferred* detectors read its tag
  (the analyzer direction). 7 lemmas, ~3 s. See *Interface steps → stressors* below.

## Files

```
secure_email/
├── S0_secure_email.spthy          # profile S0 entry-point (declared stressors)
├── S1_interface.spthy             # profile S1 entry-point (interface-generated stressors)
├── protocol/
│   ├── crypto.spthy               # builtins: asymmetric- + symmetric-encryption
│   ├── init.spthy                 # sender + keyed/keyless recipient + key publication
│   ├── pgp_pathway.spthy          # PGP producers: fetch genuine/tampered candidate key (S0)
│   ├── pw_pathway.spthy           # password producer: senc compose + SHARE_PW prompt (S0)
│   ├── deliver.spthy              # SHARED outcomes: aenc send, recipient decrypt, recipient phishing
│   ├── compose_ui.spthy           # S1: composer steps posing objective !Op/!Decision + trigger facts
│   ├── stress_alex.spthy          # enable sender as a stress target
│   └── stress_blake.spthy         # enable recipient as a stress target
├── bundles/
│   ├── human_common.spthy         # mask_state + answered_once + stress_alex
│   ├── pgp_phase.spthy            # S0: verify masks + σ6 Abstraction (declared)
│   ├── pw_phase.spthy             # S0: share masks + σ2 ExternalDistraction + σ3 TimePressure(share)
│   └── interface_inferred.spthy   # S1: verify+share+confirm masks + the four INFERRED detectors
├── experiments/S0_secure_email.spthy   # S0 lemmas
└── experiments/S1_interface.spthy      # S1 lemmas
```

New `core/` files added for this ceremony (action-scoped, framework-reusable):
`masks/attentive_share.spthy`, `masks/careless_share.spthy`, `masks/busy_share.spthy`. (σ₃ time
pressure on the share step now uses the shared agnostic `stressors/time_pressure.spthy` — the old
`time_pressure_share.spthy` clone was collapsed into it; see [`../../AGNOSTIC_STRESSOR_INTERFACE.md`](../../AGNOSTIC_STRESSOR_INTERFACE.md).)

## Interface steps → stressors (profile S1)

The guide's "in webmail" composer boxes become explicit steps in `protocol/compose_ui.spthy`. Each
step emits a generic **`!Step(P, sid, action)`** in the agnostic interaction taxonomy, and a `core/`
detector reads it (and, for the lookup detectors, a lexicon row) and infers the stressor — the HCI
judgment lives in `core/lexicon_tlx.spthy`, not in a designer flag or the detector. The step also
poses the same S0 trigger fact, so the real verify/share masks answer it and drive the real
`aenc`/`senc`/`Oob` outcome in `deliver.spthy`.

| Composer step | Objective step posed (Layer 1) | Detector (core/stressors) | Stressor → mask | Outcome |
|---|---|---|---|---|
| **choose_method** (weigh TLS/PGP/password) | `!Step` ×3 `'decide'` | `alert_volume` | σ9 AlertVolume → Careless | in-band password leak |
| **confirm_key** (PGP key/fingerprint) | `!Step(_,_,'compare')` | `abstraction` | σ6 Abstraction → Naive | accept substituted key → encrypt to adversary |
| **set_passphrase** (derive sym key) | `!Step(_,_,'compute')` | `cognitive_load` | σ1 HighCognitiveLoad → Busy | wrong-recipient slip |
| **send** (deadline on the compose step) | `!Step(_,_,'compute')` | `time_pressure` | σ3 TimePressure → Busy | rushed leak |
| **phish_confirm** (recipient side, `deliver.spthy`) | `!Step('Blake',_,'confirm')` | `external_distraction` (S0 only) | σ2 → Careless | recipient re-discloses pw |

The headline lemma `S1_degrade_from_interface_step` proves the analyzer direction: **every mask
degradation in the ceremony is generated by a named preceding interface step** (`UIStep`).

## Lemmas (S0: 9, S1: 7 — all verify, ~3 s each)

- `S0_happy_pgp`, `S0_happy_pw` — each pathway can deliver securely to Blake.
- `S0_only_recipient_reads` — only Blake ever reads the plaintext (no honest misdelivery).
- `S0_attentive_keeps_secret` *(headline +)* — no degraded behaviour ⇒ the secret never leaks.
- `S0_message_secrecy_attribution` *(headline)* — any adversary access is attributable to exactly
  one named weak point: `Mistake` (skipped verification), `LeakPw`, or `MisdeliveredPw`.
- `S0_leak_pgp_reachable`, `S0_leak_pw_inband_reachable`, `S0_leak_pw_misdeliver_reachable`,
  `S0_recipient_leak_reachable` — each failure (including a **recipient-side** phishing leak) is reachable.

Together: **a secure email reaches only the right recipient iff the human stays Attentive at the
critical step**; every breach is confined to the two weak points the guide names — skipped
fingerprint verification (PGP) or an out-of-band password that wasn't (password).

## Run

```
export PATH="$HOME/.local/bin:$PATH"
python3 .claude/skills/model-tamarin/check.py --prove ceremonies/secure_email/S0_secure_email.spthy
python3 .claude/skills/model-tamarin/check.py --prove ceremonies/secure_email/S1_interface.spthy
```
