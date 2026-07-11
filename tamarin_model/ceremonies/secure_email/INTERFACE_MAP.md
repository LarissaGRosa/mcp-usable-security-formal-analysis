# secure_email — INTERFACE MAP

Authoritative screen inventory for the full-interface model (Steps 4–5). One row per numbered
marker in `../../../secure_email_interface.html` (pins **1–16** compose, **1–9** password page,
**1–8** inbox; the letter prefix here is this map's per-screen namespace). Markers on the same
screen are **co-present by construction** — the co-present column lists only the *performed* peers.
Each row is tagged **performed** (a mask-gated f_H prompt whose committed `!StepData` an effect rule
reads) or **exposure-only** (a posed `!Prompt` that density detectors count but no answer drives —
lesson 15a/15b).

Action classes: `transcribe` (field entry — Step 2), `compute`, `compare`, `share`, `authorize`,
`confirm`, `decide` (core/masks.spthy). "cue" = a `!Displayed`/`!ControlDesign` signal, not a prompt.

## Screen A — sender compose window (Alex)

Posed once off `AlexInit` by `IF_screen_composer` (+ `IF_screen_pgp` / `IF_screen_pw` sub-panels),
once-bounded via a `PoseComposer` event + restriction.

| # | Marker | action | performed? | `!Displayed` observables | must precede |
|---|---|---|---|---|---|
| A1 | Window controls | — | exposure | — | — |
| A2 | To field (chips) | `transcribe` | performed | `<'Blake'>` intended correspondent | send |
| A3 | Per-recipient lock indicator | cue (not a prompt) | — | feeds A7: keyed vs keyless recipient | A7 |
| A4 | Cc/Bcc toggle | `decide` | exposure | — | — |
| A5 | Subject + "not encrypted" reminder | `transcribe` | performed | `<'generic-subject'>`; reminder = `!ControlDesign('transcribe-subject','clear')` lever | send |
| A6+A7 | Encryption selector + 3-method menu | `decide` | performed | the A3 cue `<recipient-key-state>` | pathway prompts |
| A8 | Message password | `compute` | performed | correct passphrase | share, send |
| A9 | Show/hide password | mitigation lever (`IF_REVEAL`) | — | enables self-check `compare <typed,intended>` | — |
| A10 | Hint field | `transcribe` | performed | `<vague-hint>` | send |
| A11 | Expiration | `decide` | exposure | — | — |
| A12 | Attach | — | exposure | — | — |
| A13 | Sign · attach my key | `confirm` | performed | `<own-key, own-key>` | Blake's encrypted reply |
| A14 | Body editor | — | exposure (carries m) | — | send |
| A15 | Send | `authorize` | performed | — | delivery |
| A16 | Discard | safe-fail affordance (Fearful abort target) | — | — | — |

Method decision (A6/A7) replaces the old `IF_pick_pgp`/`IF_pick_pw`: Attentive `handle` respects the
A3 cue (keyless correspondent → PW); a `misroute` (OUTCOME_CARELESS_MISROUTE) picks "Standard (TLS
only)" = named unsafe outcome `PlaintextAtProvider(m)` (NOT `Out` — preserves breach ⇔ mistake).

## Screen B — recipient password page (Blake)

Reached via the mailed link, so a link-`confirm <claimed-origin, expected-origin>` (the guide's "can
resemble phishing"; the page's sender card is the claimed origin) guards entry. Posed by
`IF_screen_blake_pw`, once-bounded.

| # | Marker | action | performed? | observables | must precede |
|---|---|---|---|---|---|
| (link) | Page origin | `confirm` | performed | `<claimed-origin, expected-origin>` | pw entry |
| B1 | Password field | `transcribe` | performed | `<oob-pw>` received out-of-band | unlock |
| B2 | Show/hide | mitigation lever (as A9) | — | — | — |
| B3 | Show hint | — | exposure | — | — |
| B4 | Unlock | `authorize` | performed | — | read, reply |
| B5 | Download attachment | — | exposure | — | — |
| B6+B7 | Reply box + Send reply | `decide` | performed | route: secure page vs regular mail | — |
| B8/B9 | Expiration notice / language | — | exposure | — | — |

Credulous confirm + entry ⇒ `PwEnteredAtImpostor('Blake')` ⇒ `Out(pw)`. A `misroute` on B6/B7 =
reply via regular mail instead of the secure page ⇒ `Out(reply-secret)`.

## Screen C — recipient end-to-end inbox (Blake)

Posed by `IF_screen_blake_pgp`, once-bounded.

| # | Marker | action | performed? | observables | must precede |
|---|---|---|---|---|---|
| C1/C2 | Encryption / signature badges | `confirm` | exposure | — | — |
| C3 | Trusted-key indicator → fingerprint view | `compare` | performed | `<sender-key, oob-reference>` | trusting the reply path |
| C4/C5 | Body / encrypted attachment | — | exposure (m arrives) | — | — |
| C6 | Reply | `decide` | performed | — | — |
| C7 | Forward | `decide` | performed | re-encrypts only "if a key exists" — misroute surface | — |
| C8 | Overflow menu | — | exposure | — | — |

Fearful freeze on the decrypt authorize = the guide's abandonment case (safe-fail). A `misroute` on
C7 = Forward to a keyless third party ⇒ `ForwardedOutside('Blake')` ⇒ `Out(m)` — a recipient-side
breach of "only Alex and Blake know m" even when every sender step was perfect.

## Single-correspondent abstraction

The mock shows two recipient chips (keyed `alice`, keyless `bob`); the model keeps the
single-correspondent abstraction — `'Blake'` is the intended chip and the keyless/keyed state is the
A3 cue A7's decide must respect (Attentive picks PW for a keyless correspondent; degraded picks TLS
or a mismatched PGP recipient).

## Density surfaces (real, replacing the ambient stubs)

- σ2 (any two co-present `!Prompt`): every screen.
- σ8 (two `confirm`): A13 + C1/C2 (Blake) — real confirms.
- σ9 (three `decide`): B6 reply-route + C6 + C7.
- σ1/σ3 (compute `'hi'` + `!UnderDeadline`): A8 passphrase.
- σ_ADDITIVE (two co-present `'med'` `transcribe`): A5 subject + A10 hint (or A2 + A5).
- σ10 (`!Failed`): Busy-slip on any `transcribe`/passphrase.
