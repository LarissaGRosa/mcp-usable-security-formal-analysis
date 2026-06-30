# Incident validation — modeled outcomes vs the real world (ROADMAP #10)

The model's value rests on its outcomes being *real* failure modes, not artifacts of the formalism. Each
modeled human-factors outcome below maps to a documented real-world incident or usability study, and to the
lemma that exhibits it and the mitigation we proved removes it. This grounds the analysis and is the
evidence base behind [`RFC_GUIDANCE.md`](RFC_GUIDANCE.md). (Anchors are cited by name/year; they are
illustrative real-world validation, not an exhaustive CVE list.)

| Modeled outcome | Real-world anchor | Lemma (reachable) | Proven mitigation |
|---|---|---|---|
| **σ₈ Habituation / adversary-induced urgency → auto-approve injected MFA prompt** | **MFA-fatigue / push-bombing account takeovers**: Uber breach (Sept 2022); 0ktapus / Scattered Spider campaigns (Group-IB, 2022); Lapsus$. Vendors responded with **number matching** (Microsoft Authenticator, 2023). | `P2_autoapprove_injected_reachable`, `P8_adv_autoapprove_reachable`, `Fido_injected_auth_reachable` | number matching — `P6_shutout_blocks_injected`, `FidoHardened_no_injected_auth` |
| **#5 belief-state phishing → Attentive user shares with a spoofed peer** | **Credential phishing** — the dominant initial-access vector (Verizon DBIR, year on year). | `PhishWeak_breach_reachable` (Attentive, no degradation) | **verified identity / origin binding** — `PhishStrong_no_phish`. *Strong real-world validation:* WebAuthn/FIDO2 is "phishing-resistant" precisely because the credential is bound to the **verified origin** — exactly our strong-identity interface preventing the false belief. |
| **σ₆ Abstraction → accept a tampered key fingerprint** | **PGP key-verification failures** — Whitten & Tygar, "Why Johnny Can't Encrypt" (USENIX Security 1999); users skip/mishandle fingerprint checks, enabling key-substitution MITM. | `P2_mistake_reachable`, `P3_mistake_reachable`, `S0_leak_pgp_reachable` | low-effort compare (`P7_no_mistake`) / device-side compare (`P6_no_tampered_mistake`) |
| **σ₆ / σ₈ on security warnings → click-through** | **TLS/SSL warning fatigue**: Sunshine et al., "Crying Wolf" (USENIX Security 2009); Akhawe & Felt, "Alice in Warningland" (USENIX Security 2013) — high click-through on incomprehensible / habituated warnings. | (same Abstraction / Habituation onsets) | low-effort, non-habituating warning (the interface lever, `P7`) |
| **σ₄ MisleadingTerminology (Pathway B) → Attentive user sets an unsafe policy** | **AWS S3 "Authenticated Users"** — the label means *any* AWS account (effectively public); a long line of public-bucket data exposures traced to this misreading. | `P5_misleading_attentive_mistake` | clear terminology (the task-side fix; `P5` shows the mistake needs the misleading label) |
| **σ₁ HighCognitiveLoad → slip computes a wrong key, ceremony completes** | The general principle that **humans cannot perform crypto by hand reliably** (manual key/nonce handling errors) — the motivation for "don't make the user the calculator." | `P1_slip_reachable` | detect-and-halt key confirmation (`P6_no_slip_completion`) |
| **σ₂ Distraction (in-band leak) / σ₃ TimePressure (misdelivery) → password mishandled** | **Misdirected email & in-band secret sends** — misdirected email is repeatedly a leading reported breach cause (e.g. UK ICO data-incident statistics); sending a password in the same thread as the content. | `S0_leak_pw_inband_reachable`, `S0_leak_pw_misdeliver_reachable` | out-of-band channel (`S0_attentive_keeps_secret`) |
| **#4 population — a step safe for experts is unsafe for novices** | **Expertise gaps in security-task usability** — novices fail tasks experts pass (the recurring finding across usable-security user studies). | `P1_slip_reachable` (novice) vs `P9_no_slip` (expert) | design for the least-skilled population / lower the demand for everyone |

## What this establishes

- **Every modeled failure is a real failure.** The reachability lemmas reproduce documented incidents and
  study findings; they are not formalism artifacts.
- **The mitigations match what industry actually adopted.** Number matching (against MFA fatigue) and
  FIDO2 origin binding (against phishing) are the two clearest cases: the model independently derives the
  exact lever the real world converged on, and proves it removes the outcome.
- **It closes the loop.** Real incident → modeled outcome (reachable) → proven lever → RFC requirement
  ([`RFC_GUIDANCE.md`](RFC_GUIDANCE.md)). A new incident class is added by encoding its human outcome and
  re-running the generator.
