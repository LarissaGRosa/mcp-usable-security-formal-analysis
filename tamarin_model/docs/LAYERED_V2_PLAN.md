# Secure_email LAYERED v2 — implementation plan

**Goal:** one clean five-layer architecture for the secure_email ceremony, literature-grounded
stressor triggering, 3-stressor experiments, every experiment proving in **≤ 5 minutes**.

**Status: PLAN (2026-07-09).** Nothing below is built yet.

---

## 0. The target pipeline (the "original intent" layering)

Every trace reads as this loop, and the trace GRAPH shows it by color:

```
🔵 PROTOCOL          crypto, wire (DY), storage, channels (public / OOB)
      ▲ PReq_* requests            │ results (keys, arrivals, OOB deliveries)
      │                            ▼
🟠 INTERFACE         one rule per control; PROMPTS the user:  !Step(P,pid,action) + !StepData(observables)
      ▲ mask answers               │ prompts + CONTEXT (!UnderDeadline, prompt density)
      │ (Checked/ShareOutcome/     ▼
      │  Granted)          🔴 STRESSOR LAYER   reads the interface's prompts + context (+ 🟣 lexicon)
      │                            │ SetMask(P, mask)
      │                            ▼
🟢 USER              answers each prompt ACCORDING TO THE MASK IT WEARS (mask_state gates)
```

Key point vs today: the stressor layer **reads the interface** (its prompts and their context),
never the protocol; the user answers **prompts**, never wire facts; the protocol reacts only to
interface requests. S3 already implements ~80% of this; v2 makes it the ONLY architecture.

---

## 1. What changes, item by item

### 1.1 PK creation as a modeled sub-ceremony (init)

`Init_Recipient_PGP` (magic `!RecipientKey` + `Out(pk)`) is DELETED. Blake's key exists only if
the ceremony ran: keygen prompt (interface) → `P_keygen` (protocol) → publish prompt →
`P_publish` sends the key **over the public channel** (`Out(pkB)` — the keyserver/email is
DY-territory) and the **fingerprint over the OOB channel** (`OobFp`, the Signal read-out, private).
This is S3's flow, promoted to the standard init for every profile.

### 1.2 Tampering comes from Dolev–Yao, not from a producer branch

`P_fetch_genuine` / `P_fetch_tampered` (and the old `A_fetch_*` / `UI_confirm_key_*` pairs)
collapse into **one rule**:

```
rule P_fetch:  [ PReq_fetch(idA), In(k) ] --[ KeyArrived('Alex') ]-> [ FetchedKey(idA, k) ]
```

The fetched key is *whatever the network delivers*: the DY can forward Blake's published `pkB`
faithfully (happy path) or substitute `pk(skE)` (the MITM). No `Tampered()` producer action —
"tampered" becomes a DERIVED notion (`EncTo(m,k)` with `k ≠ pk(Blake's sk)`), proven by the
structural helper `EncTo(m,k) ⇒ k = pk(own sk) | Mistake`. The human decides at the compare
prompt `<k, OobFp-reference>`: Attentive performs the comparison; a degraded mask
(Naive σ6 / Habituated σ8 click-through / **Careless "skips the check"** — new opt-in row
`outcome_careless_skipcheck.spthy`, Whitten & Tygar 1999: users skip fingerprint verification)
accepts whatever the DY delivered.

### 1.3 pw pathway fully split (user / interface / protocol)

Already done in S3's files; v2 keeps: `set_passphrase` (compute prompt) → `btn_share_signal`
(share prompt; masks pick the channel; effects produce `Oob`/`Out`) → `btn_send` (authorize
prompt; Fearful freezes) → `P_send_pw` (store + notify) → Blake `pw_entry` (transcribe prompt) →
`P_unlock_pw` (link + OOB password). The old one-rule `pw_pathway.spthy`/`compose_ui.spthy` go.

### 1.4 Literature-grounded triggering (the stressor layer reads the interface)

| Stressor | v2 trigger (what the stressor layer reads) | Grounding |
|---|---|---|
| σ1 Load | prompt + lexicon `MentalDemand hi` (task-intrinsic) — **unchanged** | Sweller 1988; NASA-TLX |
| σ3 TimePressure | **NEW `time_pressure_deadline.spthy`**: prompt + `!UnderDeadline(pid)` — a CONTEXT fact the interface emits when a control is presented under a timer (the expiring secure link / send-before-deadline). Time pressure is situational, not task-intrinsic. | Maule & Svenson 1993 (time pressure as situational constraint); TLX Temporal Demand |
| σ2 Distraction | **NEW `distraction_concurrent.spthy`**: TWO distinct prompts pending for one party (k=2 density, any action) — distraction is competing demand, not a free-floating event | Wickens MRT 2008 |
| σ6 Abstraction | prompt + lexicon `Effort hi` — unchanged | Whitten & Tygar 1999 |
| σ8 Habituation | 2 same-class (`confirm`) prompts — unchanged (restriction already renamed so it composes with σ9) | Anderson & Vance CHI 2015 |
| σ9 AlertVolume | 3 `decide` prompts — unchanged | Cvach 2012 |
| Anxiety | `authorize` prompt + `Arousal hi` — unchanged | Yerkes–Dodson 1908 |

New detectors are NEW FILES (old σ2/σ3 stay for alex_blake_kdf, which has no interface-context
concept). Restriction names kept distinct (`InequalityConcurrency`).

### 1.5 Experiments: 3 stressors at a time, ≤ 5 min each

New profile set (REPLACES S0–S3; the old mixed-layer files retire to git history):

| Profile | Stressors | What it shows |
|---|---|---|
| `S0_baseline` | none | both pathways deliver end-to-end through all five layers |
| `S1_trio_verify` | σ6 + σ2ᶜᵒⁿᶜ + σ3ᵈᵉᵃᵈˡ | the verify/share failure surface: substitution, silent leak, misdelivery |
| `S2_trio_density` | σ8 + σ9 + σ1 | the repeat-exposure surface: click-through, alert fatigue, load slip |
| `S3_trio_pressure` | σ1 + σ3ᵈᵉᵃᵈˡ + Anxiety | the pressure surface incl. the Fearful freeze (safe-fail) |
| `S4_worstcase` | all 7 | the §6a canary (current S3, renamed; proven 149 s) |

Anti-explosion toolkit baked into every profile (repo MEMORY.md lesson 15):
1. Human-GATE only the outcome-driving crossings (compare / share / authorize); every other
   control is an exposure-only prompt (density detectors count POSED prompts).
2. Include NO behavior file whose answers drive nothing (no confirm/decide behaviors).
3. Shared `experiments/helpers.spthy`: the three `[reuse]` lemmas (`pw_stays_oob`, `sk_secret`,
   `encto_shape`) included by every profile with a secrecy lemma.
4. All once-bounds; linear branch commits (one method per trace); `OneSetMaskPerMask`.
Budget check: each trio is a strict subset of the proven 149 s worst case → comfortably < 5 min.

### 1.6 Readability: one directory per layer

```
secure_email/
├── README.md
├── S0_baseline.spthy … S4_worstcase.spthy      # profile entry points (includes only)
├── protocol/                                   # 🔵 ONLY blue rules
│   ├── crypto.spthy   keys.spthy (init+keygen+publish+fetch)   mail.spthy (send/store/deliver/unlock)
├── interface/                                  # 🟠 ONLY orange rules (one rule per control)
│   ├── sender_pgp.spthy   sender_pw.spthy   recipient.spthy   context.spthy (!UnderDeadline)
│   └── effects.spthy      (share/keychecked adapters — the sanctioned boundary)
├── bundles/                                    # one include per stressor (🔴 detector + its 🟣 rows)
│   ├── s1_load.spthy  s2_concurrent.spthy  s3_deadline.spthy  s6_abstraction.spthy
│   ├── s8_habituation.spthy  s9_alertvolume.spthy  anxiety.spthy
│   └── human_common.spthy (mask_state + answered_once + outcome matrix + targeting)
└── experiments/                                # lemmas only (+ helpers.spthy)
```

A profile file then reads as its own summary: crypto → protocol/* → interface/* → human_common →
3 stressor bundles → experiments.

---

## 2. Build order (each step ends green)

1. **Core additions** (no existing profile touched): `time_pressure_deadline.spthy`,
   `distraction_concurrent.spthy`, `outcome_careless_skipcheck.spthy`.
2. **Layer files**: build `protocol/` + `interface/` from S3's mock files + the 1.1/1.2 changes
   (single DY fetch, deadline context on the pw controls).
3. **S0_baseline** + helpers; prove.
4. **Three trios**; prove each ≤ 5 min (chains redistributed from today's S3 lemma set, one per
   stressor, plus the secrecy pair in each trio).
5. **S4_worstcase** (rename of today's S3 onto the new files); prove.
6. Retire the old files (`pgp_pathway`, `pw_pathway`, `compose_ui`, `deliver`, `trustkey_ui`,
   `expiry_ui`†, old `init`, old S0–S2 entries+experiments) — git history keeps them.
7. Full sweep (P0–P9 + new S0–S4); README rewrite; MEMORY/docs updates.

† `expiry_ui`/set-policy (Pathway B) has no control in the mock: either drop from secure_email
  (P5/P7 keep the Pathway-B story) or add an expiration control to one trio. Default: drop.

## 3. Decisions (user, 2026-07-09)

- **D1 — REPLACE.** Old S0–S3 and the mixed-layer files retire to git history; v2 is the only
  secure_email architecture.
- **D2 — trios BY PATHWAY:** `S1_trio_pgp` {σ6 Abstraction, σ8 Habituation, σ2 Concurrency} on
  the key-verification surface; `S2_trio_pw` {σ1 Load, σ3 Deadline, σ9 AlertVolume} on the
  password surface (incl. the recipient side); `S3_trio_mixed` {σ6, σ3, Anxiety} spanning both
  pathways + the Fearful freeze.
- **D3 — phishing EMERGES from the modeling** (not a hard-coded lure): the email channel is open
  and unauthenticated (`In(<'pwreq', to, replyTo>)` — anyone, including the DY, can send mail
  claiming any reply-to), and a MALICIOUS PARTICIPANT `Eve` is a first-class `!Party` with
  `!Corrupt` (her OOB inbox is adversary-readable: `Oob(_,'Eve',x) → Out(x)`). The interface
  renders an incoming password request as an ordinary reply/share prompt. Consequence: the SHARE
  class joins the observables discipline — `!StepData(P, rid, <replyTo, correspondent, pw>)`;
  Attentive matches replyTo = correspondent (shares back only to the person the ceremony was
  with), degraded masks don't look. A spoofed display name still delivers to the REAL
  correspondent (harmless); the leak requires a degraded recipient — attribution is preserved.
