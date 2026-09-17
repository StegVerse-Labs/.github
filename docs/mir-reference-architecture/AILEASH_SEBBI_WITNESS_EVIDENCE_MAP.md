# AILeash / sebbi.pro witness evidence map

Updated: 2026-09-17
Goal Task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

Purpose: reconcile prior observations with the Evidence Custody Seam Appendix A R4 and Justin Dobson witness-topology claims without promoting unverified claims.

Status vocabulary:

- `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` — public unauthenticated response was directly observed through an external fetch surface; proves only what that response carried on its face.
- `SOURCE_INSPECTED` — public source code or repository text was inspected; establishes published implementation/source material, not authentic runtime execution.
- `COUNTERPART_REPORTED` — asserted by Richard Whitney, Justin Dobson, AILeash/sebbi.pro, MIR, or another interested/operator-controlled source without independent reproduction of the exact claim.
- `USER_PROVIDED_PUBLIC_PROFILE` — user supplied a screenshot/public-profile view; useful for context but not independent identity verification.
- `NOT_ESTABLISHED` — evidence presently insufficient for promotion.

## Reconciliation matrix

| Claim | Current status | Evidence / observation | Bound conclusion |
|---|---|---|---|
| sebbi.pro exposes an unauthenticated chain verification route | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `https://sebbi.pro/api/verify-chain` returned a JSON chain result with `valid`, block count, tip, and `Chain intact` message. | The public route answers without credentials and reports its own chain status. This is not independent reconstruction of the whole chain by this task. |
| sebbi.pro exposes a public witness tip route | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `https://sebbi.pro/x/witness/tip` returned tip, height, seal time, witness version, observe-route guidance, and an explicit anchoring limitation. | The public route exists and publishes a bounded current-head claim. |
| sebbi.pro exposes a public peer/witness roster | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `https://sebbi.pro/x/witness/peers` returned five peers in the observed response and explicit semantics for current/stale/silent, self-consistent, reachability, name binding, signed lane, and anchoring. | Public witness observations are queryable. Roster membership is explicitly not membership/endorsement/identity proof. |
| `self-consistent` is intentionally weaker than third-party verification | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `/x/witness/peers` legend states both halves came from the submitter and that `self-consistent` is NOT verification by AILeash or a third party. | Directly supports the epistemic-boundary behavior described in Appendix A R4. |
| submission is not Bitcoin confirmation | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `/x/witness/tip` and `/x/witness/peers` explicitly state OpenTimestamps submission is not confirmation; `/x/ots/status` distinguishes pending proofs and confirmed-upgrade state. | The service publicly exposes the limitation; no Bitcoin confirmation is inferred from submission. |
| AILeash publishes an unauthenticated single-tip witness-attestation route | `SOURCE_INSPECTED` | Public source describes `GET /x/witness/attest?peer=&tip=` as “did we witness this, and when”; `.well-known/ai.txt` publishes the route template. | Route existence and intended semantics are source-supported. This task has not yet retained a positive runtime response for the exact live tip described in Appendix A. |
| Appendix A R4: a live tip was queried and returned observed status, first-seen time, and chain position in one unauthenticated call | `COUNTERPART_REPORTED` | Richard Whitney reported the positive test after the operator pointed him to the read route; v0.2/v0.3 Appendix A carries the result. | Do not promote to independently reproduced until the exact peer/tip or retained response is obtained and replayed/verified. |
| Public AILeash ordering-test declares mutual witnessing live both directions with an external peer chain hourly since 2026-08-01 | `COUNTERPART_REPORTED` plus `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` for the declaration itself | `/.well-known/ordering-test.json` publicly returned `supported=true`, `demonstrable_publicly=true`, endpoint `/x/witness/peers`, and the hourly-since-Aug-1 statement. | We independently observed the declaration, not the full two-way hourly history. |
| Public witness page says AILeash operates one chain and does not run the network | `COUNTERPART_REPORTED` plus public declaration observed | Public sebbi.pro witness page makes that statement and publishes open witness routes. | Operator/network independence remains a topology/control-domain claim requiring external corroboration for conformance scoring. |
| Justin Dobson is the operator/owner associated with AILeash/sebbi.pro | `USER_PROVIDED_PUBLIC_PROFILE` + `SOURCE_INSPECTED` self-declaration | User-provided LinkedIn screenshots identify Justin Dobson and AILeash/sebbi.pro; public repository self-descriptions name Justin Antony Dobson/Monop Content. | Strong contextual linkage, but operator-controlled/self-profile material is not independent identity verification. |
| Justin Dobson's star-versus-graph and collusion/simultaneous-failure analysis is an implementation-informed contribution | `COUNTERPART_REPORTED` with source-text provenance | Evidence Custody Seam v0.3/v0.4 credits Justin in place. | Preserve the attribution and the architecture insight; do not infer network topology facts not directly evidenced. |
| A witness count alone proves independence | `NOT_ESTABLISHED` / rejected by current seam text | v0.3/v0.4 replaces witness count with an independence/control/failure-domain figure. | Node/member count must not be promoted to an independence claim. |
| AILeash witness topology currently satisfies the v0.4 collusion/failure-domain metric at a particular numeric value | `NOT_ESTABLISHED` | Public peer list shows endpoints and status, but does not by itself prove ownership/control/failure-domain independence among all peers. | No numeric resilience figure is assigned by StegVerse from roster membership alone. |
| Bitcoin anchoring of a specific Appendix A commitment is independently verified | `NOT_ESTABLISHED` | Public `/x/ots/status` exposes proof files, attempts, pending/upgrade state, and bounded notes, but this task has not independently verified a specific `.ots` proof against Bitcoin. | Preserve `COUNTERPART_REPORTED`/public-status only until independent proof verification succeeds. |
| The clean-room 784-record / 30-commitment Section 5 run was independently reproduced by StegVerse | `NOT_ESTABLISHED` | Appendix A reports the run and syscall trace; no retained StegVerse-side reproduction artifact is in this reconciliation lane. | Treat as counterpart implementation evidence, not StegVerse-verified conformance. |

## Relation to Appendix A R4

Current public evidence independently supports three bounded parts of Appendix A R4:

1. an unauthenticated public witness surface exists;
2. the public witness data explicitly distinguishes `self-consistent` from independent verification;
3. the anchoring text explicitly distinguishes submission from confirmation.

The strongest sentence in Appendix A — that a specific live tip was positively queried and returned whether it was observed, when first seen, and where it sits in the acceptor's chain — remains `COUNTERPART_REPORTED` in this map until the exact positive response is independently retained or reproduced.

## Relation to v0.4 R4 topology

The public peer list demonstrates visible membership/status and named endpoints, but it does not establish the administrative, ownership, infrastructure, or correlated-failure independence required by v0.4. The map therefore does not convert five listed peers into a resilience score. A star, mesh, or mixed graph must be evaluated from actual cross-witness edges plus independently attributable control/failure domains.

## Promotion rules

- Never promote operator-controlled README, `.well-known` declarations, profile text, or conformance JSON into independent runtime proof by themselves.
- A public endpoint response may be `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE`, but only for the fields actually returned.
- A positive witness claim requires the exact peer/tip pair and retained response or equivalent checkable artifact.
- A Bitcoin-confirmed claim requires independent proof verification; `pending`, calendar acceptance, or service-reported confirmation is not enough by itself.
- Identity, ownership, endorsement, and control-domain independence remain separate claims.
- Missing proof remains missing; it does not imply the event did not happen.
