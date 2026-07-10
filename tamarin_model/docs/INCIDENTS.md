# Incident validation — modeled outcomes vs the real world (ROADMAP #10)

The model's value rests on its outcomes being *real* failure modes, not artifacts of the formalism. Each
modeled human-factors outcome below maps to a documented real-world incident or usability study, and to the
lemma that exhibits it and the mitigation we proved removes it. This grounds the analysis and is the
evidence base behind [`RFC_GUIDANCE.md`](RFC_GUIDANCE.md). (Anchors are cited by name/year; they are
illustrative real-world validation, not an exhaustive CVE list.)

| Modeled outcome | Real-world anchor | Lemma (reachable) | Proven mitigation |
|---|---|---|---|
| **σ₈ Habituation / adversary-induced urgency → auto-approve injected MFA prompt** | **MFA-fatigue / push-bombing account takeovers**: Uber breach (Sept 2022); 0ktapus / Scattered Spider campaigns (Group-IB, 2022); Lapsus$. Vendors responded with **number matching** (Microsoft Authenticator, 2023). | `P2_autoapprove_injected_reachable`, `P8_adv_autoapprove_reachable` | number matching — `P6_shutout_blocks_injected` |
| **σ₈ Habituation generalizes → click through the key check** | **Warning habituation transfers across similar dialogs** (Anderson & Vance, CHI 2015); two routine button confirms habituate and the user stops inspecting. | `S1_habituation_clickthrough` | remove the redundant confirmation (the chain **needs** the two-confirm exposure) |
| **σ₆ Abstraction / σ₂ skipped check → accept a DY-substituted key** | **PGP key-verification failures** — Whitten & Tygar, "Why Johnny Can't Encrypt" (USENIX Security 1999); users skip/mishandle fingerprint checks, enabling key-substitution MITM. | `P2_mistake_reachable`, `P3_mistake_reachable`, `S1_abstraction_naive_substitution`, `S1_distraction_skipcheck` | low-effort compare (`P7_no_mistake`) / device-side compare (`P6_no_tampered_mistake`) |
| **Emergent phishing reply → recipient re-discloses the password** | **Credential phishing** — the dominant initial-access vector (Verizon DBIR); the request arrives over the OPEN mail channel (a malicious participant, no lure rule in the model). | `S2_recipient_phish_emergent` (Load-degraded recipient misdelivers) | the recipient check — share only with the actual correspondent (`S2_attentive_defeats_phish`) |
| **σ₆ / σ₈ on security warnings → click-through** | **TLS/SSL warning fatigue**: Sunshine et al., "Crying Wolf" (USENIX Security 2009); Akhawe & Felt, "Alice in Warningland" (USENIX Security 2013) — high click-through on incomprehensible / habituated warnings. | (same Abstraction / Habituation onsets) | low-effort, non-habituating warning (the interface lever, `P7`) |
| **σ₄ MisleadingTerminology (Pathway B) → Attentive user sets an unsafe policy** | **AWS S3 "Authenticated Users"** — the label means *any* AWS account (effectively public); a long line of public-bucket data exposures traced to this misreading. | `P5_misleading_attentive_mistake` | clear terminology (the task-side fix; `P5` shows the mistake needs the misleading label) |
| **σ₁ HighCognitiveLoad → slip computes a wrong key, ceremony completes** | The general principle that **humans cannot perform crypto by hand reliably** (manual key/nonce handling errors) — the motivation for "don't make the user the calculator." | `P1_slip_reachable` | detect-and-halt key confirmation (`P6_no_slip_completion`) |
| **σ₉ fatigue (in-band leak) / σ₁ σ₃ (misdelivery) → password mishandled** | **Misdirected email & in-band secret sends** — misdirected email is repeatedly a leading reported breach cause (e.g. UK ICO data-incident statistics); sending a password in the same thread as the content. | `S2_alertvolume_inband_silent`, `S2_load_busy_misdelivery`, `S2_deadline_pressure_misdelivery` | out-of-band channel (`S0_secrecy_absolute`, helper `H_pw_stays_oob`) |
| **#4 population — a step safe for experts is unsafe for novices** | **Expertise gaps in security-task usability** — novices fail tasks experts pass (the recurring finding across usable-security user studies). | `P1_slip_reachable` (novice) vs `P9_no_slip` (expert) | design for the least-skilled population / lower the demand for everyone |

## What this establishes

- **Every modeled failure is a real failure.** The reachability lemmas reproduce documented incidents and
  study findings; they are not formalism artifacts.
- **The mitigations match what industry actually adopted.** Number matching (against MFA fatigue) is the
  clearest case: the model independently derives the exact lever the real world converged on, and proves
  it removes the outcome. (The retired belief-state worked example did the same for FIDO2 origin binding
  against phishing — design in git history, ROADMAP #5.)
- **It closes the loop.** Real incident → modeled outcome (reachable) → proven lever → RFC requirement
  ([`RFC_GUIDANCE.md`](RFC_GUIDANCE.md)). A new incident class is added by encoding its human outcome and
  re-running the generator.
