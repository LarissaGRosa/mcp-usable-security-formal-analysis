# alex_blake_kdf — INTERFACE MAP (invented companion messenger)

Authoritative screen inventory for the K-profile interface (Step 6). This ceremony has **no shipped
screen** — the wire profiles P0–P11 pose `compute` prompts straight off protocol state. This map
defines the *invented* **companion messenger for manual key establishment**: Alex and Blake each run
a messenger app; every protocol value is **manually transcribed and sent by the human**, every
receipt **confirmed via the interface**. The app's channel is **private** (`KDF_WIRE_PRIVATE`, like
secure_email's mailbox): the DY adversary reads a value only when a human mistake exports it — which
is what makes the (S) goal "only Alex & Blake know `sk`" non-vacuous (`kdf/2` is a free symbol; a DY
who learns *both* nonces computes the key).

P0–P11 keep the public wire (`KDF_WIRE`) and their lemmas, untouched. K-profiles are a new family
over the same protocol layer. Four symmetric screens per party.

Action classes armed: `transcribe`, `share`, `compare`, `compute`, `authorize` — **all pre-existing
or Step-2 core classes; zero new core rules** (the agnosticism proof in practice).

| Screen | Control | action | performed? | co-present with | `!Displayed` | must precede |
|---|---|---|---|---|---|---|
| K1 send-code | Nonce entry field | `transcribe` | performed | chat picker, send | `<ownNonce>` | send |
| K1 | Chat picker + Send | `share` | performed | nonce field | `<corr, corr, committedNonce>` | partner K2 |
| K2 incoming | Received-nonce vs OOB read-back | `compare` | performed | accept button | `<received, readback>` | K3 |
| K3 calculate | Manual kdf derivation | `compute` | performed | key field | `<kdf(Na,Nb)>` | key field |
| K3 | Key entry field | `transcribe` | performed | derivation | `<derived-key>` | K4 |
| K4 confirm | Key read-back comparison | `compare` | performed | start-session | `<key, readback>` | start-session |
| K4 | Start session | `authorize` | performed | comparison | — | session |

## Screen semantics / mistake routes

1. **"Send your code"** (K1) — own nonce displayed; human types it (`transcribe`) and picks the
   chat / presses Send (`share`, observables `<recipient, correspondent, nonce>`). Typo (Busy slip)
   ⇒ partner derives a different key (safe-fail via FINISH_CONFIRMED); wrong chat (Busy misdeliver)
   ⇒ `Out(nonce)`; paste into public channel (Careless inband-leak) ⇒ delivered + `Out(nonce)`.
2. **"Incoming code"** (K2) — received nonce next to the partner's OOB read-back (`compare`); a
   credulous compare accepts an `In`-substituted nonce = the MITM route (`Mistake`).
3. **"Calculate"** (K3) — manual derivation (`compute`, displayed correct `kdf(Na,Nb)`) + typing the
   result into the key field (`transcribe`). Two co-present `'med'` fields = the additive-load
   surface (Sweller, `SIGMA_ADDITIVE`).
4. **"Confirm key"** (K4) — key read-back comparison (`compare`) + "start session" (`authorize`).
   The FINISH_CONFIRMED shutdown keeps reading the interface's `!Displayed` correct value — the
   lesson-19 trap: never compare the human's commit against itself. Premature variant
   (OUTCOME_PREMATURE): a degraded grant starts the session without the K4 compare join ⇒
   `SessionUnconfirmed`.

Both parties symmetric (`STRESS_ALEX`/`STRESS_BLAKE`); every screen once-bounded.

## Density surfaces (real, replacing the synthetic ones)

- σ8 = two real `confirm`s (was `IF_NONCE_ACK` stub).
- σ9 = three real `decide`s.
- σ2 = any two co-present controls.
- σ_ADDITIVE = the two co-present `'med'` fields in K3 (derivation + key entry).

---

## As-built (read this before trusting the tables above)

The tables above are the **design** inventory. Several controls were **cut or downgraded** to keep every
theorem inside the 3-minute prover budget, and a few plan items were never built. The authoritative,
honest list of what is and is not modelled — with the reasons — is **`tamarin_model/docs/DIVERGENCES.md`**.

The short version: controls marked *exposure-only* emit `!Demand` **without** a `Prompt` (they are counted
by the density detectors but never performed, which is what makes them free); the A13 sign-attach confirm,
the A10 hint field, the A9/B2 reveal lever and the kdf K2 MITM compare / K3 key-entry field were **not
built**; and the To field is posed but its committed value **drives nothing**.
