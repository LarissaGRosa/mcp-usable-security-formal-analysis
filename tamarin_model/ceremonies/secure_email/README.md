# Ceremony C1 — secure email (LAYERED v2)

Models `secure-email-mock.html` (repo root): Alex sends Blake a secure email by **OpenPGP**
(Method 2) or **password** (Method 3). Built as **five strict layers** — the design in
[`docs/LAYERED_V2_PLAN.md`](../../docs/LAYERED_V2_PLAN.md) — color-coded in the interactive
trace graphs (`tamarin-prover interactive .`):

```
🔵 protocol/   #1f6fd0  crypto, wire (DY), storage, channels (public / OOB), participants
     ▲ PReq_* requests        │ results (KeyReady, FetchedKey, OobFp, MailPwReq, …)
🟠 interface/  #f2994a  one rule per mock control; PROMPTS the user (!Step + observables + context)
     ▲ mask answers           ▼ prompts + context (!UnderDeadline, prompt density)
🔴 stressors   #eb5757  read ONLY the interface's prompts/context (+ 🟣 #9b51e0 lexicon/config rows)
     │ SetMask(P, mask)       ▼
🟢 user        #27ae60  answers each prompt according to the mask it wears (mask_state gates)
```

## What is modeled (and what is NOT hard-coded)

- **The PK sub-ceremony.** Blake's key exists only if the ceremony ran: keygen → publish sends
  the public key over the **public channel** (keyserver = DY territory) and the fingerprint over
  the **OOB channel** (the Signal thread, `OobFp`).
- **Tampering is the adversary's choice.** One fetch rule reads `In(k)`: the DY forwards Blake's
  genuine key or substitutes its own. No genuine/tampered producer branch, no oracle tag; the
  human decides at the compare prompt `<fetched key, OOB fingerprint>`.
- **Phishing EMERGES.** The mail channel is open and unauthenticated (`<'pwreq', to, replyTo>`
  from `In`), and **Eve** is a first-class malicious participant (`!Corrupt`: her OOB inbox is
  DY-readable). A password request renders as an ordinary reply prompt; the share observables are
  `<replyTo, correspondent, pw>` and an **Attentive recipient's check (replyTo = correspondent)
  defeats it** (`S2_attentive_defeats_phish`). Capturing the secret needs a degraded recipient.
- **Verdict-free step data everywhere** (repo `MEMORY.md` lesson 14): compare `<offered, ref>`,
  confirm `<claimed, own>`, share `<recipient, correspondent, payload>` — the Attentive rule
  PERFORMS each check; producers never declare outcomes.

## Stressor triggering (v2, literature-grounded)

| Detector | Reads (from the interface) | Grounding |
|---|---|---|
| σ1 Load → Busy | prompt + lexicon `MentalDemand hi` | Sweller 1988; NASA-TLX |
| σ3 TimePressure v2 → Busy | prompt + **`!UnderDeadline(pid)` context** (the expiring-link timer) — situational, not task-intrinsic | Maule & Svenson 1993; TLX |
| σ2 Distraction v2 → Careless | **two prompts pending** (k=2, any classes) — competing demand | Wickens MRT 2008 |
| σ6 Abstraction → Naive | prompt + lexicon `Effort hi` (the fingerprint compare) | Whitten & Tygar 1999 |
| σ8 Habituation → Habituated | 2 `confirm` prompts (the two routine buttons) | Anderson & Vance CHI 2015 |
| σ9 AlertVolume → Careless | 3 `decide` prompts (the method toggle) | Cvach 2012 |
| Anxiety → Fearful | `authorize` prompt (+ `Arousal hi`): the send button | Yerkes–Dodson 1908 |

Opt-in outcome rows (🟣, one include each): Habituated **click-through** and Careless
**skip-the-check** on the compare; **degraded final click** on the authorize (only Fearful
refuses to send).

## Profiles — 3 stressors at a time (all ≤ 5 min)

| Profile | Stressors | Time | Story |
|---|---|---|---|
| `S0_baseline` | none | ~9 s | five-layer happy paths; **secrecy is absolute** (`S0_secrecy_absolute`) |
| `S1_trio_pgp` | σ6, σ8, σ2 | ~130 s | three degraded routes to accepting the DY-substituted key |
| `S2_trio_pw` | σ1, σ3, σ9 | ~50 s | misdelivery, silent in-band leak, **emergent phishing** on the recipient |
| `S3_trio_mixed` | σ6, σ3, Anxiety | ~13 s | one failure per pathway + the **Fearful freeze** (safe-fail) |
| `S4_worstcase` | all 7 | ~174 s | the §6a state-space canary; every trio is a subset |

Anti-explosion toolkit (repo `MEMORY.md` lesson 15): gate only the outcome-driving crossings
(compare / share / authorize); every other control is an exposure-only prompt (density detectors
count POSED prompts); no behavior file whose answers drive nothing; the shared `[reuse]` helper
trio (`experiments/helpers.spthy`: `H_pw_stays_oob`, `H_sk_secret` `[heuristic=C]`,
`H_encto_shape`); the attribution lemma only (its contrapositive — attentive-keeps-secret — holds
by the same proof and is not proven twice).

## Files

```
secure_email/
├── S0_baseline.spthy … S4_worstcase.spthy   # profile entry points (includes read as a summary)
├── protocol/          🔵 crypto.spthy · keys.spthy (participants+Eve, keygen, publish, DY fetch)
│                         mail.spthy (send/store/unlock, open pwreq channel, corrupt-OOB delivery)
│                         stress_alex.spthy · stress_blake.spthy (🟣 targeting)
├── interface/         🟠 sender.spthy (one rule per composer control, deadline context)
│                         recipient.spthy (Blake's pane + the emergent reply prompt)
│                         effects.spthy (share adapters → channels)
├── bundles/human_common.spthy   # mask gates + one-answer + outcome matrix + lexicon + targeting
└── experiments/       helpers.spthy ([reuse] trio) + one lemma file per profile
```

## Run

```
export PATH="$HOME/.local/bin:$PATH"
python3 .claude/skills/model-tamarin/check.py --prove ceremonies/secure_email/S1_trio_pgp.spthy
tamarin-prover interactive ceremonies/secure_email/    # colored layer graphs at :3001
```
