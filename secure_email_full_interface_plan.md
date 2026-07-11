# Plan — full interfaces under masks, for BOTH ceremonies (concurrent prompts, ordered responses, ceremony-blind core)

> Goal: each ceremony models **every UI interaction that can be on screen at the same time**, poses
> them as **concurrent prompts**, requires the human to **respond in the ceremony's order** through
> whatever **mask the active stressors have set at that moment**, and proves — for **each
> stressor** — the pair: **(C) the ceremony can complete** and **(S) only Alex and Blake know the
> secret** (the message in secure_email; the session key in alex_blake_kdf).
>
> **Design rule zero (agnosticism):** every human action class, stressor, outcome row, and ordering
> mechanism added by this plan lives in `core/` and keys only on `(party, action-class, prompt)` —
> never on a ceremony constant, rule name, or screen. A ceremony contributes ONLY: protocol rules,
> screen rules that pose `!Prompt`/`!Displayed`, effect/advance rules that consume committed
> `!StepData`, and lemmas. The proof of agnosticism is that **both ceremonies consume the same new
> core blocks unchanged** (same standard as the existing σ/mask machinery), plus the step-10 audit.
>
> Hard constraint: every profile proves in **≤ 5 minutes** (repo MEMORY.md lesson 10).

## 0a. Context — the secure_email ceremony

`secure-email-generic-guide.html` reduces secure email (Proton Mail / Mailfence / mailbox.org) to
three methods. Method 1 (TLS) needs no user action; Methods 2 and 3 are the human ceremonies:

- **PGP pathway** — Alex has a key pair; obtains Blake's public key; **verifies the fingerprint
  out-of-band**; enables encrypt+sign in the composer; sends. Blake generates+publishes his key
  and decrypts with his private key. Skipping fingerprint verification is the canonical weak point.
- **Password pathway** — Alex chooses "encrypt with password"; **sets a passphrase + hint** (hint
  must be meaningless to outsiders); **shares the password over a separate channel** (never by
  email); sends. Blake receives a message/secure link — which "can resemble phishing" — gets the
  password out-of-band, **enters it**, reads and replies via the same page.
- **Never protected**: the **subject line** and envelope metadata. A secret typed into the subject
  leaks even when everything else is done right.

The interface is a *screen*, not a script, and `secure_email_interface.html` is its authoritative
mock: three annotated screens with every user-interactable element numbered — **(A) the sender
compose window** (16 markers: To chips with per-recipient lock indicators, subject with a standing
"not encrypted" reminder, encryption selector + 3-method menu, password + hint fields with a
show/hide reveal, expiration, attach, Sign·attach-my-key, body, Send, Discard), **(B) the
recipient password page** (9 markers: password field + reveal, show-hint, Unlock, attachment,
reply box, Send-reply, expiration notice, language), and **(C) the recipient end-to-end inbox
message** (8 markers: encryption + signature badges, trusted-key indicator opening the
fingerprint view, body, attachment, Reply, Forward, overflow). All of a screen's markers are
co-present prompts; the user must answer in the ceremony's order (address before send, verify
before send, unlock before reply). Which answer they give is decided by the mask the stressors in
force at that instant have pushed (`!EffectiveMask` at response time). The mock's design notes
call the **per-recipient lock indicator** the control that "drives the whole decision" — it is the
`!Displayed` cue for the method decision.

## 0b. Context — the alex_blake_kdf ceremony + its INVENTED interface

Today `alex_blake_kdf` is wire-driven: nonces N_A/N_B cross a public Dolev-Yao channel, each party
gets one `compute` prompt (derive `kdf(Na,Nb)` by hand), and the profiles study slips, shutdowns,
recovery and demand levers (P0–P11). It has no *screen* — prompts are posed straight off protocol
state.

This plan gives it one (invented, per the user's brief): a **companion messenger interface for
manual key establishment**. Alex and Blake each run a messenger-style app; every protocol value is
**manually transcribed and sent by the human**, and every receipt is **confirmed via the
interface**. The channel the app provides is **private** (like secure_email's `Mailbox`): the DY
adversary reads a value only when a human mistake exports it — this is what makes the (S) goal
("only Alex and Blake know `sk`") non-vacuous, since `kdf/2` is a free symbol and a DY who ever
learns *both* nonces computes the key. The existing public-wire profiles (P0–P11) stay untouched
as the slip/shutdown/demand testbed; the invented interface is a new profile family (K-profiles)
over the same protocol layer.

Four symmetric screens per party:

1. **"Send your code"** — own nonce displayed; the human **types it into the message field**
   (`transcribe`) and **picks the chat / presses Send** (`share`, observables
   `<recipient, correspondent, nonce>`). Typo (Busy slip) ⇒ the partner derives a different key;
   wrong chat (Busy misdeliver) ⇒ nonce exported; pasting into a public channel (Careless
   inband-leak) ⇒ nonce exported.
2. **"Incoming code"** — received nonce displayed next to the partner's out-of-band read-back
   (`compare`, `<received, readback>`); a credulous compare accepts an adversary-substituted
   nonce (the MITM route).
3. **"Calculate"** — the manual derivation (`compute`, displayed correct `kdf(Na,Nb)`) plus
   **typing the result into the key field** (`transcribe`). Co-present: two `'med'` fields — the
   additive-load surface (Sweller, σ_ADDITIVE).
4. **"Confirm key"** — key read-back comparison (`compare`) + **"start session"** (`authorize`).
   The FINISH_CONFIRMED shutdown keeps reading the interface's `!Displayed` correct value
   (lesson 19 trap: never compare the human's commit against itself).

Model status quo and gaps (both ceremonies):

| # | Gap | Today |
|---|---|---|
| G1 | Co-presence partly **artificial** (secure_email's `IF_confirm_surface`/`IF_decide_surface`; kdf's `IF_NONCE_ACK` exposure stubs) | real controls not all posed |
| G2 | **Field-type controls** (To, subject, hint, pw-entry, nonce/key entry) unmodelled — no `transcribe` class in core | transcription slip/leak routes absent |
| G3 | **Response order** only implicit (linear joins); a degraded out-of-order answer (Send before verify) cannot happen, so order is not a provable usability property | order enforced, never violated |
| G4 | Recipient/second-party screens thin | Blake's mistakes under-modelled |
| G5 | No uniform per-stressor pair **(C) completion ∧ (S) only-A&B-know** | attribution lemmas only |
| G6 | alex_blake_kdf has **no interface** at all in the screen sense; its wire is public so (S) is unstatable there | K-profiles + private-messenger variant needed |

## The 10 steps

Steps 1–3 are core/docs (ceremony-blind by construction); 4–5 apply them to secure_email; 6 to
alex_blake_kdf; 7–10 are the lemma spine, profile matrices, budget, and audit — for both. Each
step ends with the full sweep green (`check.py --prove`, both ceremonies).

---

### Step 1 — Interface inventories: screen maps + response-order DAGs (docs only)

One `INTERFACE_MAP.md` per ceremony (authoritative for steps 4–6), cross-checked with
`tools/step_analyzer.py`. Each row: screen · control · **action class** · co-present-with ·
must-precede. Mark **performed** vs **exposure-only** prompts (lesson 15a).

**secure_email** (one row per numbered marker in `secure_email_interface.html`; markers on the
same screen are co-present by construction, so the co-present column lists only the *performed*
peers):

*Screen A — sender compose window (Alex):*

| # | Marker | action | `!Displayed` observables | must precede |
|---|---|---|---|---|
| A1 | Window controls | (exposure) | — | — |
| A2 | To field (chips) | `transcribe` | `<'Blake'>` intended correspondent | send |
| A3 | Per-recipient lock indicator | (cue, not a prompt) | feeds A7's observables: keyed vs keyless recipient | A7 |
| A4 | Cc/Bcc toggle | (exposure `decide`) | — | — |
| A5 | Subject + "not encrypted" reminder | `transcribe` | `<'generic-subject'>`; the reminder is a `!ControlDesign` lever | send |
| A6+A7 | Encryption selector + 3-method menu | `decide` | the A3 cue `<recipient-key-state>` | pathway prompts |
| A8 | Message password | `compute` | correct passphrase | share, send |
| A9 | Show/hide password | (mitigation lever) | enables the self-check `compare <typed, intended>` | — |
| A10 | Hint field | `transcribe` | `<vague-hint>` | send |
| A11 | Expiration | `decide` (exposure) | — | — |
| A12 | Attach | (exposure) | — | — |
| A13 | Sign · attach my key | `confirm` | `<own-key, own-key>` | Blake's encrypted reply |
| A14 | Body editor | (exposure; carries m) | — | send |
| A15 | Send | `authorize` | — | delivery |
| A16 | Discard | (safe-fail affordance: Fearful's abort target) | — | — |

*Screen B — recipient password page (Blake); reached via the mailed link, so a link-`confirm`
(`<claimed-origin, expected-origin>` — the guide's "can resemble phishing") guards entry:*

| # | Marker | action | observables | must precede |
|---|---|---|---|---|
| B1 | Password field | `transcribe` | `<oob-pw>` received out-of-band | unlock |
| B2 | Show/hide | (mitigation lever, as A9) | — | — |
| B3 | Show hint | (exposure) | — | — |
| B4 | Unlock | `authorize` | — | read, reply |
| B5 | Download attachment | (exposure) | — | — |
| B6+B7 | Reply box + Send reply | `decide` (route: secure page vs regular mail) | — | — |
| B8/B9 | Expiration notice / language | (exposure) | — | — |

*Screen C — recipient end-to-end inbox (Blake):*

| # | Marker | action | observables | must precede |
|---|---|---|---|---|
| C1/C2 | Encryption / signature badges | (exposure `confirm`) | — | — |
| C3 | Trusted-key indicator → fingerprint view | `compare` | `<sender-key, oob-reference>` | trusting the reply path |
| C4/C5 | Body / encrypted attachment | (exposure; m arrives) | — | — |
| C6 | Reply | `decide` | — | — |
| C7 | Forward | `decide` | re-encrypts only "if a key exists" — the misroute surface | — |
| C8 | Overflow menu | (exposure) | — | — |

The mock shows **two** recipient chips (keyed alice, keyless bob); the model keeps the
single-correspondent abstraction — 'Blake' is the intended chip, and the keyless/keyed state is
the A3 cue that A7's decide must respect (Attentive picks PW for a keyless correspondent;
degraded picks TLS or mismatched PGP).

**alex_blake_kdf** (the §0b invented messenger; both parties symmetric):

| Screen | Control | action | co-present with | must precede |
|---|---|---|---|---|
| K1 send-code | Nonce entry field | `transcribe` | chat picker, send | send |
| K1 | Chat picker + Send | `share` | nonce field | partner K2 |
| K2 incoming | Received-nonce vs OOB read-back | `compare` | accept button | K3 |
| K3 calculate | Manual kdf derivation | `compute` | key field | key field |
| K3 | Key entry field | `transcribe` | derivation | K4 |
| K4 confirm | Key read-back comparison | `compare` | start-session | start-session |
| K4 | Start session | `authorize` | comparison | session |

Real density surfaces replace the synthetic ones (σ8 = two real `confirm`s, σ9 = three real
`decide`s, σ2 = any two co-present controls, σ_ADDITIVE = two co-present `'med'` fields).

### Step 2 — Core: the `transcribe` action class (ceremony-blind)

New f_H class in `core/masks.spthy` behind `#ifdef MASK_TRANSCRIBE`, same contract as every class —
reads `!Prompt(P,tid,'transcribe')` + `!Displayed(P,tid,<intended>)` + `!EffectiveMask` +
`!OutcomePolicy(mask,'transcribe',outcome)`; no ceremony vocabulary:

- Attentive `correct` → commits the intended value (`!StepData(P,tid,intended)`).
- Busy `slip` → commits a fresh wrong value + `!Failed(P)` (feeds σ10). *One* generic action fact
  (`Slip(P)`, reused) — what a wrong To-address vs a typo'd nonce *means* is the ceremony's effect
  rule's business.
- Careless `inband-leak` → generic action `TranscribeLeak(P,tid)` and commits the displayed value;
  **the ceremony's effect rule decides what leaks where** (secret into subject / pw into hint /
  key into chat). Core never emits `Out`.
- Rows in `Seed_outcome_policy` (`core/framework.spthy`); lexicon rows
  `!Demands('transcribe', MentalDemand|TemporalDemand, 'med')` in `core/demands.spthy` — a field
  is a `'med'` step, so a *single* field can't fire σ1, but two co-present fields feed
  σ_ADDITIVE. `compute`/`compare`/`share` stay `'hi'`.

No ceremony arms the flag yet ⇒ sweep unchanged. AUTHORING_GUIDE §3 gains the class row.

### Step 3 — Core: screen-posing pattern + generic order-violation row

Two ceremony-blind pieces:

- **Screen-posing pattern (a documented convention, not core code):** one interface rule per
  *screen* poses all of that screen's prompts off ONE shallow source, once-bounded
  (`ScreenShown(P,screen)` + restriction). Rationale: σ2's two-`!Prompt` source product stays a
  product of shallow sources; co-presence becomes real instead of stubbed. Goes in
  AUTHORING_GUIDE (with the σ2 budget note) — the pattern is what both step-4/6 ceremonies
  instantiate.
- **`#ifdef OUTCOME_PREMATURE` (core/masks.spthy):** the generic out-of-order lever, mirroring
  `OUTCOME_DEGRADED_CLICK`. A degraded (non-Attentive, non-Fearful) `authorize` grant additionally
  emits the generic action `PrematureGrant(P,aid)` and a linear `GrantedUnchecked(P,aid)` fact.
  Ceremony-blind: core doesn't know what the grant was supposed to wait for. **The ceremony**
  adds one effect rule that consumes `GrantedUnchecked` *without* its upstream join and routes the
  consequence (`Out(m)` / unsafe session) — that rule is where "the order was violated" gets its
  meaning. Attentive can never take the premature route (its grant emits only `Granted`).
- **`#ifdef OUTCOME_CARELESS_MISROUTE` (core/masks.spthy):** the routing analog for `decide` —
  a Careless (or Habituated) decide may pick the *wrong route* instead of stalling: generic
  outcome row `('Careless','decide','misroute')` + rule emitting `Misroute(P,did)` and
  `DecisionMisrouted(P,did)`. Ceremony-blind; the ceremony's effect rule says what the wrong
  route *is* (Forward to a keyless third party, reply via regular mail, TLS-only send). Needed
  because today's Careless `fatigue` is a safe-fail stall — it cannot express the mock's C7
  Forward mistake or the plain-send default.

### Step 4 — secure_email: sender screens (composer + pathway), concurrent

Replace the ambient surfaces (G1) with the real screen A in `protocol.spthy`:

- `IF_screen_composer` poses To (`transcribe`, `!Displayed <'Blake'>` — A2), subject
  (`transcribe`, `<'generic-subject'>` — A5), method (`decide` — A6/A7, with the A3 cue as its
  observables `<recipient-key-state>`), Send (`authorize` — A15) — all at once off `AlexInit`,
  once-bounded; `ComposerState` carries the pids. The method decision replaces
  `IF_pick_pgp`/`IF_pick_pw`: Attentive `handle` respects the cue (keyless correspondent → PW);
  a `misroute` (step 3 row) picks "Standard (TLS only)" = the named unsafe outcome
  `PlaintextAtProvider(m)` (NOT `Out` — preserves breach ⇔ mistake for the DY lemmas while a
  lemma can still forbid it). Fearful's abort target is A16 Discard (safe-fail, draft deleted).
- `IF_screen_pgp` (the composer in PGP mode): `In(offered)` fetch + `compare <offered,'Blake'>`
  (the key/fingerprint view) + Sign·attach-my-key `confirm` (A13, `<own-key, own-key>` —
  skipping it doesn't leak, it blocks the encrypted *reply* leg, i.e. a completion property).
  The send **effect** joins, in order: committed To + `Granted` + `!KeyChecked` + committed
  recipient (existing good/leak routing stays). Premature variant (step 3) skips the verify
  join ⇒ `SendPremature('Alex')` + `Out(m)`.
- `IF_screen_pw` (the composer's password panel): passphrase (`compute` — A8) + hint
  (`transcribe` — A10) + expiration (`decide`, exposure — A11) posed together; `share` keeps its
  triple observables. Effects: hint `TranscribeLeak` ⇒ pw travels in-band (same class as
  `PW_deliver_inband`); subject `TranscribeLeak` ⇒ `Out(m)` at send (metadata is cleartext);
  Busy-slip passphrase ⇒ Blake's unlock fails ⇒ `!Failed('Blake')` (feeds σ10; safe-fail).
- **A9/B2 show-password lever** (`IF_REVEAL`, a demand/mitigation seed): with the reveal
  affordance the typed value becomes checkable — model as the interface additionally posing a
  self-check `compare <typed, intended>` whose Attentive answer catches the slip before send
  (the UI-level analog of FINISH_CONFIRMED). Baseline (no reveal) vs hardened (reveal) is an RFC
  pair (step 10).
- **A5's standing reminder** is a `!ControlDesign('transcribe-subject','clear')` seed: the
  hardened composer keeps the subject's demand at `'lo'`/blocks the subject `TranscribeLeak`
  row; the un-reminded baseline doesn't — the second RFC pair.

σ1/σ3 now fire from **real** demand (the `compute` `'hi'` rows + `!UnderDeadline` on the modal),
not from a stub. Retire `IF_confirm_surface`/`IF_decide_surface`/compute stubs once the real
screens cover σ8/σ9/σ1+σ3.

### Step 5 — secure_email: recipient screens + order wiring

- `IF_screen_blake_pw` (screen B): link-`confirm` (`<claimed-origin, expected-origin>` — the
  guide's "can resemble phishing"; the page's sender card is the claimed origin) + pw-entry
  `transcribe` (B1) + Unlock `authorize` (B4) + reply-route `decide` (B6/B7), posed together;
  the entry effect requires a non-dismissed confirm and Unlock requires the committed entry
  (order). Careless dismiss = safe-fail (never reads). Credulous confirm + entry ⇒
  `PwEnteredAtImpostor('Blake')` ⇒ `Out(pw)`. A `misroute` on the reply decide = replying via
  regular mail instead of the secure page ⇒ `Out(reply-secret)` — the reply leaves the boundary.
- `IF_screen_blake_pgp` (screen C): trusted-key `compare` (C3, `<sender-key, oob-reference>` —
  the recipient-side fingerprint verification the old model lacked) + open/decrypt `authorize` +
  Reply/Forward `decide` (C6/C7), co-present. Fearful freeze on the authorize = the guide's
  abandonment case (safe-fail). A `misroute` on C7 = **Forward to a keyless third party** ⇒
  `ForwardedOutside('Blake')` ⇒ `Out(m)` — the recipient-side breach of "only Alex and Blake
  know m" even when every sender step was perfect.
- Blake keeps his stress enable; density detectors now see his real screens (B and C give Blake
  genuine multi-prompt density: σ2 any-two, σ9's decides = B6 reply-route + C6 + C7).

### Step 6 — alex_blake_kdf: the invented messenger interface (K-profiles)

New `#ifdef`-gated screen rules in the ceremony's `protocol.spthy` implementing §0b, arming ONLY
existing/step-2 core classes (`transcribe`/`share`/`compare`/`compute`/`authorize`) — zero new
core rules, which is the agnosticism proof in practice:

- **Private messenger wire** (`KDF_WIRE_PRIVATE`, alternative to `KDF_WIRE`): the sent nonce goes
  to a private `Chat(correspondent, nonce)` fact routed by the `share` outcome — `oob`→delivered,
  `misdeliver`→`Out(nonce)`, `inband-leak`→delivered + `Out(nonce)` (same envelope pattern as
  `PW_deliver_*`). The K-profiles use this wire so (S) is statable; **P0–P11 keep the public
  wire** and their existing lemmas, untouched.
- `IF_screen_k1` (per party): nonce-entry `transcribe` (`!Displayed <ownNonce>`) + chat/send
  `share` (`<correspondent, correspondent, committedNonce>`); the send effect consumes the
  *committed* transcription (a slip ships the typo).
- `IF_screen_k2`: received-vs-readback `compare` — the read-back reference travels on the private
  OOB (correspondent's true nonce); credulous accept of an `In`-mediated substitute = the MITM
  `Mistake`.
- `IF_screen_k3`: `compute` (displayed `kdf(Na,Nb)`) + key-entry `transcribe`, co-present (the
  additive-load surface).
- `IF_screen_k4`: key read-back `compare` + start-session `authorize`; FINISH_CONFIRMED shutdown
  unchanged (reads `!Displayed`). Premature variant: degraded grant starts the session without
  the K4 compare join ⇒ `SessionUnconfirmed` (+ the MITM consequence when K2 was also degraded).
- Both parties symmetric (`STRESS_ALEX`/`STRESS_BLAKE` as today); every screen once-bounded.

### Step 7 — The lemma spine: (C) ∧ (S), templates in core, instantiated per ceremony

- **Templates** (comment templates in `core/properties.spthy`, next to T1–T4): **T5 completion
  under onset** (exists-trace: onset ∧ finish ∧ no-unsafe) and **T6 only-correspondents** (all-
  traces: `Secret(x) & K(x) ⇒ ⟨enumerated mistake disjunction⟩`, plus the reader/holder
  restriction lemma). Generic invariant added under `#ifdef PROPERTIES`:
  `UP_premature_requires_degrade` (`PrematureGrant(p,a) ⇒ Ex m≠Attentive. SetMask(p,m) before`).
- **secure_email instantiation** (`lemmas.spthy` + profiles): extend `H_pw_stays_oob` with the
  hint/entry disjuncts; `H_leak_routes [reuse]` = the ONE enumerated boundary list
  (`Mistake | LeakPw | MisdeliveredPw | TranscribeLeak-routed | SendPremature |
  PwEnteredAtImpostor | ForwardedOutside | PlaintextAtProvider-forbidden`); per profile:
  `Sx_only_correspondents_know` (T6), `Sx_read_only_blake` (`Read(p,m) ⇒ p='Blake'`),
  `Sx_completes_under_<σ>` (T5). Completion for the PGP pathway includes the reply leg when A13
  was confirmed (`Sx_reply_completes`: Alex's Sign·attach-key confirm ⇒ a trace where Blake's
  encrypted reply arrives — the reciprocity property the guide calls out).
- **alex_blake_kdf instantiation** (K-profiles): structural helper
  `H_sk_requires_both_nonces [reuse]` (`K(kdf(Na,Nb)) ⇒ (K(Na) & K(Nb)) | key-transcribe-leak`) —
  the compositional payoff: leaking ONE nonce is provably insufficient. Then
  `Kx_only_correspondents_know_sk` (T6 over the K-profile mistake list) +
  `Kx_completes_under_<σ>` (T5: onset ∧ both `Finish` ∧ equal keys ∧ no-unsafe) +
  `Kx_agreement` (both finish ⇒ same `sk` unless a named mistake).
- Discipline (lesson 15): never prove a T6 and its attentive-keeps-secret contrapositive; keep
  exists-trace chains K-free on deep pathways; fallback if T5's negated-unsafe conjunct wanders —
  drop it and derive cleanliness from T6, recording which form each profile uses.
- Keep one **onset coverage** exists-trace per armed stressor (lesson 16) and one **failure
  chain** per stressor (control → onset → mask → mistake/order-violation → `K(secret)`).

### Step 8 — Profile matrices: every stressor × both ceremonies

One density detector per profile (existing rule); each profile carries onset coverage + the
(C)+(S) pair + one chain, ≤5 min.

**secure_email** (re-cut S0–S7, add S8):

| Profile | Stressors (density bold) | New coverage |
|---|---|---|
| S0_baseline | — | both pathways complete; secrecy absolute; order respected |
| S1_trio_pgp | σ6, **σ2**, skip-check | pair + premature-send chain (σ2 → Careless → out-of-order) |
| S2_trio_pw | σ1, σ3, **σ9** + misroute row | pair + hint-leak & wrong-To chains; σ9 on real decides → Careless misroute (Forward / plain reply) |
| S3_trio_mixed | σ6, **σ8**, anxiety | pair + trust-modal click-through on real confirms |
| S4_worstcase | σ1 σ3 σ6 anxiety **σ2** + PROPERTIES | pair + agnostic attribution |
| S5_cue_phish | σ_CUE | pair + recipient link-confirm phish |
| S6/S7 recovery | σ8 / σ2 + matched recovery | unchanged headline + the pair |
| **S8_transcribe** | σ10 (+σ1) | subject-leak chain; pw-slip → `!Failed` → σ10 → Careless |

**alex_blake_kdf**: P0–P11 unchanged (public-wire testbed). New K-profiles:

| Profile | Stressors (density bold) | Headline |
|---|---|---|
| K0_baseline | — | four screens complete both parties; `sk` secrecy absolute; agreement |
| K1_send_code | σ1, σ3 | nonce-typo slip → shutdown catches (safe-fail) vs misdeliver → `Out(nonce)` |
| K2_mitm | σ6, **σ2** | credulous incoming-compare accepts substituted nonce → MITM chain → `K(sk)` |
| K3_additive | σ_ADDITIVE (+σ10) | two co-present `'med'` fields → Busy → key-entry slip; repeat-fail |
| K4_confirm | **σ8**, anxiety + OUTCOME_PREMATURE | premature start-session skips key-confirm; Fearful freeze safe-fail |
| K5_worstcase | broad set + PROPERTIES | (C)+(S) pair + `UP_premature_requires_degrade` |

If a worst case overruns budget: split per pathway/screen pair rather than raising the timeout.

### Step 9 — Performance pass (both ceremonies)

Time every profile (`check.py --prove --timeout 300`); apply, in order: shallow-source audit
(every `!Prompt` producer reads only init/session facts; no effect rule poses prompts);
once-bounds on every `ScreenShown` + human step (lesson 5); `[reuse]` K-helpers before the
secrecy pair (lesson 15c); per-lemma `[heuristic=C]` for a single wanderer; exposure-only prompts
behind `#ifdef` where the arming profile's detectors don't read them (15b); one proof per
contrapositive pair. Gate: all ≤5 min; timing tables into both ceremony READMEs.

### Step 10 — Sweep, RFC pairs, docs, agnosticism audit

- Full sweep: alex_blake_kdf P0–P11 + K0–K5 + secure_email S0–S8.
- **Agnosticism audit** (the user's invariant, made mechanical): (a) `grep -nE
  "'(Alex|Blake|composer|subject|hint|pgp|pw|nonce|chat)'" tamarin_model/core/` returns nothing;
  (b) every `MASK_*`/`SIGMA*`/`OUTCOME_*` flag is armed by **both** ceremonies or listed with a
  reason; (c) the step-2/3 blocks are consumed by both ceremonies unchanged. Record the audit as
  a checklist in AUTHORING_GUIDE §8.
- New lever pairs for `tools/rfc_requirements.json` + `rfc_gen.py`, each anchored to a mock
  marker: *send disabled until verify* (makes `SendPremature` unreachable ⇒ MUST); *subject-line
  reminder* (A5 `!ControlDesign` blocks the subject leak ⇒ SHOULD); *show-password reveal* (A9/B2
  self-check catches the transcribe slip ⇒ SHOULD); *forward-guard* (C7 re-encrypt-or-block makes
  `ForwardedOutside` unreachable ⇒ MUST); *confirm-before-session forcing function* (kdf K4 ⇒
  MUST — the same lever proven in a second ceremony, which is the RFC-grade generality claim).
- Docs: both INTERFACE_MAPs linked from READMEs; AUTHORING_GUIDE gains `transcribe`, the
  one-rule-per-screen pattern, and OUTCOME_PREMATURE; repo MEMORY.md gains the new lessons;
  retire stale ambient-surface prose.

---

## Risks & mitigations

- **σ2 blow-up under real co-presence** (biggest risk): every screen rule multiplies σ2's
  two-prompt source product. Mitigation: one-rule-per-screen (single shallow source), once-bounds,
  σ2 armed in few profiles; fallback = split worst cases.
- **K-profiles double the party surface** (both humans fully screened): keep `OneInstancePerHuman`,
  arm one party's stress per profile where the story allows (as P-profiles do with STRESS_ALEX).
- **exists-trace T5 with negated unsafe conjunct** may wander: fallback form recorded in step 7.
- **transcribe-slip vs share-misdeliver overlap**: distinct outcomes (`Slip`-routed wrong value vs
  `MisdeliveredPw`/`Out`-routed wrong channel) so attribution stays 1:1 with controls.
- **Plain-send branch** must not break `S0_secrecy_absolute`: `PlaintextAtProvider` is a named
  outcome, not `Out`.
- **Core creep**: the temptation to put the premature-send *effect* in core (it needs ceremony
  joins) — resist; core provides only the `GrantedUnchecked` lever (step 3), effects stay in the
  ceremony. The step-10 grep keeps this honest.
