# AILeash / sebbi.pro witness evidence map

Updated: 2026-09-17
Goal Task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

Purpose: reconcile prior observations with the Evidence Custody Seam Appendix A R4 and Justin Dobson witness-topology claims without promoting unverified claims.

Status vocabulary:

- `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` — public unauthenticated response was directly observed through an external fetch surface; proves only what that response carried on its face.
- `USER_PROVIDED_PUBLIC_RESPONSE` — user directly supplied the JSON returned by a public endpoint; proves only the content of that supplied response unless independently replayed.
- `SOURCE_INSPECTED` — public source code or repository text was inspected; establishes published implementation/source material, not authentic runtime execution.
- `COUNTERPART_REPORTED` — asserted by Richard Whitney, Justin Dobson, AILeash/sebbi.pro, MIR, or another interested/operator-controlled source without independent reproduction of the exact claim.
- `USER_PROVIDED_PUBLIC_PROFILE` — user supplied a screenshot/public-profile view; useful for context but not independent identity verification.
- `NOT_ESTABLISHED` — evidence presently insufficient for promotion.

## Reconciliation matrix

| Claim | Current status | Evidence / observation | Bound conclusion |
|---|---|---|---|
| sebbi.pro exposes an unauthenticated chain verification route | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `https://sebbi.pro/api/verify-chain` returned a JSON chain result with `valid`, block count, tip, and `Chain intact` message. | The public route answers without credentials and reports its own chain status. This is not independent reconstruction of the whole chain by this task. |
| sebbi.pro exposes a public witness tip route | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | On 2026-09-17, `https://sebbi.pro/x/witness/tip` returned a current sebbi.pro tip and explicit anchoring limitations. | The public route exists and publishes a bounded current-head claim for sebbi.pro itself. |
| sebbi.pro exposes a public peer/witness roster | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | On 2026-09-17, `https://sebbi.pro/x/witness/peers` returned six peers with status, liveness, reachability, name-binding, and endpoint fields. | Public witness observations are queryable. Roster membership is explicitly not membership/endorsement/identity proof. |
| flavorflowstrategy.uk publishes a concrete current witness tip | `USER_PROVIDED_PUBLIC_RESPONSE` | User supplied the JSON from `https://www.flavorflowstrategy.uk/witness.json`: `chain=flavorflowstrategy.uk`, `tip=27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`, `updated_at=2026-08-13T13:11:06Z`. | A concrete peer/tip pair now exists for the next attest replay. Because the response is user-supplied and not independently replayed by this task, classify it as user-provided public evidence. |
| The attempted sebbi.pro attest call tested the actual flavorflow tip | `NOT_ESTABLISHED` / invalid attempt | The supplied request used the literal placeholder `tip=PASTE_TIP`; the returned JSON echoed `tip="paste_tip"` and said no record was held. | This negative response says nothing about the real tip `27846a6a...6653`. It MUST NOT be treated as a negative witness finding for flavorflowstrategy.uk. |
| `self-consistent` is intentionally weaker than third-party verification | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `/x/witness/peers` legend states both halves came from the submitter and that `self-consistent` is NOT verification by AILeash or a third party. | Directly supports the epistemic-boundary behavior described in Appendix A R4. |
| submission is not Bitcoin confirmation | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `/x/witness/tip` and `/x/witness/peers` explicitly state OpenTimestamps submission is not confirmation; `/x/ots/status` distinguishes pending proofs and confirmed-upgrade state. | The service publicly exposes the limitation; no Bitcoin confirmation is inferred from submission. |
| Current OTS service state is published with pending/confirmed distinction | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | On 2026-09-17 `/x/ots/status` reported service-side proof counts and that the latest proof was `pending` with no Bitcoin block height. | The latest proof is explicitly not Bitcoin evidence. Service-reported confirmation counts do not independently verify a specific proof against Bitcoin. |
| sebbi.pro publishes a public OTS anchor list | `USER_PROVIDED_PUBLIC_RESPONSE` | User supplied `/x/ots/list` JSON containing 50 newest anchor rows, each with exact `stamp_id`, `tip`, timestamp, `ots_written`, `proof_on_disk`, and proof route. | The response establishes a concrete list of candidate stamp IDs and proof URLs. It does not state which listed proofs are confirmed. |
| The attempted OTS proof call tested a real stamp ID | `NOT_ESTABLISHED` / invalid attempt | The supplied request used the literal placeholder `ts=STAMP_ID`; sebbi.pro returned `{"ok":false,"error":"bad_stamp_id"}`. | This response does not test any listed proof and MUST NOT be interpreted as proof unavailability or proof failure. |
| AILeash publishes an unauthenticated single-tip witness-attestation route | `SOURCE_INSPECTED` | Public source describes `GET /x/witness/attest?peer=&tip=` as “did we witness this, and when”; `.well-known/ai.txt` publishes the route template. | Route existence and intended semantics are source-supported. |
| AILeash publishes raw OpenTimestamps proof retrieval | `SOURCE_INSPECTED` | Public `modules/ots.py` exposes `GET /x/ots/list` and `GET /x/ots/proof`; the proof response is defined to include recorded tip, proof SHA-256, raw `.ots` bytes as base64, state, Bitcoin block heights, and standard-client verification steps. | The implementation exposes a mechanism sufficient in principle for independent OTS verification. |
| Appendix A R4: a live tip was queried and returned observed status, first-seen time, and chain position in one unauthenticated call | `COUNTERPART_REPORTED` | Richard Whitney reported the positive test after the operator pointed him to the read route; v0.2/v0.3 Appendix A carries the result. | Do not promote until a valid exact peer/tip request is independently retained or reproduced. The current placeholder attempt is not such a test. |
| Public AILeash ordering-test declares mutual witnessing live both directions with an external peer chain hourly since 2026-08-01 | `COUNTERPART_REPORTED` plus `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` for the declaration itself | `/.well-known/ordering-test.json` publicly returned a declaration of mutual witnessing. | We independently observed the declaration, not the full two-way hourly history. |
| Public witness page says AILeash operates one chain and does not run the network | `COUNTERPART_REPORTED` plus public declaration observed | Public sebbi.pro witness page makes that statement and publishes open witness routes. | Operator/network independence remains a topology/control-domain claim requiring external corroboration for conformance scoring. |
| Justin Dobson is the operator/owner associated with AILeash/sebbi.pro | `USER_PROVIDED_PUBLIC_PROFILE` + `SOURCE_INSPECTED` self-declaration | User-provided LinkedIn screenshots identify Justin Dobson and AILeash/sebbi.pro; public repository self-descriptions name Justin Antony Dobson/Monop Content. | Strong contextual linkage, but operator-controlled/self-profile material is not independent identity verification. |
| Justin Dobson's star-versus-graph and collusion/simultaneous-failure analysis is an implementation-informed contribution | `COUNTERPART_REPORTED` with source-text provenance | Evidence Custody Seam v0.3/v0.4 credits Justin in place. | Preserve the attribution and architecture insight; do not infer network topology facts not directly evidenced. |
| A witness count alone proves independence | `NOT_ESTABLISHED` / rejected by current seam text | v0.3/v0.4 replaces witness count with an independence/control/failure-domain figure. | Node/member count must not be promoted to an independence claim. |
| AILeash witness topology currently satisfies the v0.4 collusion/failure-domain metric at a particular numeric value | `NOT_ESTABLISHED` | Public peer list shows endpoints and status, but does not by itself prove ownership/control/failure-domain independence among all peers. | No numeric resilience figure is assigned by StegVerse from roster membership alone. |
| Bitcoin anchoring of a specific Appendix A commitment is independently verified | `NOT_ESTABLISHED` | The user supplied a valid `/x/ots/list` response but did not yet retrieve one listed real stamp through `/x/ots/proof?ts=<numeric_stamp_id>` and independently verify its raw `.ots` bytes. | Preserve as unverified until a specific proof artifact is retrieved and checked with standard OpenTimestamps verification against Bitcoin. |
| The clean-room 784-record / 30-commitment Section 5 run was independently reproduced by StegVerse | `NOT_ESTABLISHED` | Appendix A reports the run and syscall trace; no retained StegVerse-side reproduction artifact is in this reconciliation lane. | Treat as counterpart implementation evidence, not StegVerse-verified conformance. |

## Current verification attempt — 2026-09-17

A concrete flavorflowstrategy.uk tip was obtained from its public `witness.json`: `27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`. The subsequent sebbi.pro attest request accidentally retained the placeholder `PASTE_TIP`, so its negative response is an invalid test of the actual tip and is not evidence against the witness claim.

A concrete 50-row OTS anchor list was also obtained. The subsequent proof request accidentally retained the placeholder `STAMP_ID`, producing `bad_stamp_id`; that is an input-validation response, not an OTS verification result.

## Relation to Appendix A R4

Current evidence independently/publicly supports the existence and bounded semantics of the witness surfaces. The strongest Appendix A sentence — that a specific live tip was positively queried and returned whether it was observed, when first seen, and where it sits in the acceptor's chain — remains `COUNTERPART_REPORTED` until the real flavorflow peer/tip pair or another exact pair is submitted without a placeholder and the response retained.

## Relation to v0.4 R4 topology

The public peer list demonstrates visible membership/status and named endpoints, but it does not establish the administrative, ownership, infrastructure, or correlated-failure independence required by v0.4. No resilience score is inferred from peer count alone.

## Promotion rules

- Never promote operator-controlled README, `.well-known` declarations, profile text, or conformance JSON into independent runtime proof by themselves.
- A public endpoint response may be classified only for the fields actually returned.
- Placeholder or malformed requests are input-validation evidence only; they do not establish positive or negative facts about the intended artifact.
- A positive witness claim requires the exact peer/tip pair and retained response or equivalent checkable artifact.
- A Bitcoin-confirmed claim requires independent proof verification; `pending`, calendar acceptance, service-reported confirmation, or a mere proof-list row is not enough by itself.
- Identity, ownership, endorsement, and control-domain independence remain separate claims.
- Missing proof remains missing; it does not imply the event did not happen.
