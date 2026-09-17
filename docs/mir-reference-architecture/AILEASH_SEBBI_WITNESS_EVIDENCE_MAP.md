# AILeash / sebbi.pro witness evidence map

Updated: 2026-09-17
Goal Task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

Purpose: reconcile prior observations with the Evidence Custody Seam Appendix A R4 and Justin Dobson witness-topology claims without promoting unverified claims.

Status vocabulary:

- `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` — public unauthenticated response was directly observed through an external fetch surface; proves only what that response carried on its face.
- `USER_RETAINED_PUBLIC_RESPONSE` — the user directly retrieved and supplied the complete public JSON response for an exact request; proves only the returned fields and does not by itself establish operator identity or control-domain independence.
- `INDEPENDENT_LOCAL_RECONSTRUCTION` — locally reconstructed or recomputed from retained artifact bytes without relying on the operator's interpretation.
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
| exact `flavorflowstrategy.uk` peer tip was obtained | `USER_RETAINED_PUBLIC_RESPONSE` | User retrieved `https://www.flavorflowstrategy.uk/witness.json`, returning chain `flavorflowstrategy.uk`, tip `27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`, updated at `2026-08-13T13:11:06Z`. | Establishes an exact peer/tip pair from the peer's public endpoint. It does not by itself prove who controls that endpoint. |
| sebbi.pro positively attested the exact flavorflow tip in one unauthenticated call | `USER_RETAINED_PUBLIC_RESPONSE` | User queried `/x/witness/attest?peer=flavorflowstrategy.uk&tip=27846a6a94b2ef76687a22d1a51fbc6a6a302fc691e8e1a361dc16b49a576653`. Response returned `witnessed=true`, `first_observed=2026-08-13T13:11:06.564037+00:00`, `last_observed=2026-09-17T08:18:40.589471+00:00`, `times_observed=253`, `sealed_in_our_chain=c76219e876dacc45aea9884a91dafa68c2e5fa31b4d928474181cbd521ea24f3`, and `block_index=560`. | This reproduces the core Appendix A R4 public-read behavior for one exact peer/tip: the acceptor states whether it observed the tip, when first/last observed, observation count, and where the observation was sealed in its own chain. It does not prove peer identity, current liveness, historical completeness, or control-domain independence. |
| the positive flavorflow attestation is current liveness or identity verification | `NOT_ESTABLISHED` | The same response returned `liveness=self-declared`, `reachability=unrecorded`, `name_status=unbound`, `submitted_url=null`, and explicitly states neither liveness nor reachability proves submitter identity. | The positive attestation proves only that the exact tip was handed to sebbi.pro and sealed into its chain under the stated peer label. |
| `self-consistent` is intentionally weaker than third-party verification | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` | `/x/witness/peers` legend states both halves came from the submitter and that `self-consistent` is NOT verification by AILeash or a third party. | Directly supports the epistemic-boundary behavior described in Appendix A R4. |
| submission is not Bitcoin confirmation | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` + `USER_RETAINED_PUBLIC_RESPONSE` | `/x/witness/tip`, `/x/witness/peers`, and the exact witness-attest response explicitly distinguish OpenTimestamps submission from Bitcoin confirmation. | No Bitcoin confirmation is inferred from submission or witness acceptance. |
| exact raw OTS artifact for stamp `1789455657` was retained | `USER_RETAINED_PUBLIC_RESPONSE` | User retrieved `/x/ots/proof?ts=1789455657`, returning tip/digest `510837825c194c303eedfaeb0528d0fc6dfe4e6bbf1e5534ef8bb34edccd0224`, `proof_bytes=721`, `proof_sha256=8511ef312479e9fd97d05ecd69d35a8d2ab727aa6e49f20c441657d714f7dd53`, raw `ots_base64`, `state=pending`, no Bitcoin block heights, and pending calendars `alice` and `bob`. | The exact proof artifact exists and is retained, but it is explicitly pending and therefore is not Bitcoin-confirmed evidence. |
| retained OTS base64 matches the returned proof length/hash | `INDEPENDENT_LOCAL_RECONSTRUCTION` | Decoding the supplied `ots_base64` produced exactly 721 bytes; SHA-256 of those bytes is `8511ef312479e9fd97d05ecd69d35a8d2ab727aa6e49f20c441657d714f7dd53`, exactly matching the returned `proof_sha256`. The bytes begin with the OpenTimestamps proof header. | The retained raw proof bytes are internally consistent with the service response. This does not convert a pending OTS proof into Bitcoin confirmation. |
| Bitcoin anchoring of stamp `1789455657` is independently verified | `NOT_ESTABLISHED` | The retained proof is `state=pending`, has `bitcoin_block_heights=[]`, and contains pending calendar attestations. | This proof cannot satisfy a Bitcoin-confirmed external-time claim yet. It must be upgraded/confirmed and independently verified against Bitcoin first. |
| AILeash publishes an unauthenticated single-tip witness-attestation route | `SOURCE_INSPECTED` + `USER_RETAINED_PUBLIC_RESPONSE` | Public source describes `GET /x/witness/attest?peer=&tip=` as “did we witness this, and when”; the user successfully exercised it for the exact flavorflow tip. | Route existence, unauthenticated use, and exact positive behavior are established for this peer/tip. |
| Appendix A R4: a live tip can be queried and return observed status, first-seen time, and chain position in one unauthenticated call | `INDEPENDENTLY_REPRODUCED_BEHAVIOR` | Exact flavorflow request returned `witnessed=true`, first/last observation times, count, sealed chain hash, and block index. | The core Appendix A R4 route/response behavior is no longer merely counterpart-reported. Richard's exact historical response artifact is not the artifact reproduced here, so provenance remains distinct. |
| Public AILeash ordering-test declares mutual witnessing live both directions with an external peer chain hourly since 2026-08-01 | `COUNTERPART_REPORTED` plus `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` for the declaration itself | `/.well-known/ordering-test.json` publicly returned a declaration of mutual witnessing. | We independently observed the declaration, not the full two-way hourly history. |
| Public witness page says AILeash operates one chain and does not run the network | `COUNTERPART_REPORTED` plus public declaration observed | Public sebbi.pro witness page makes that statement and publishes open witness routes. | Operator/network independence remains a topology/control-domain claim requiring external corroboration for conformance scoring. |
| Justin Dobson is the operator/owner associated with AILeash/sebbi.pro | `USER_PROVIDED_PUBLIC_PROFILE` + `SOURCE_INSPECTED` self-declaration | User-provided LinkedIn screenshots identify Justin Dobson and AILeash/sebbi.pro; public repository self-descriptions name Justin Antony Dobson/Monop Content. | Strong contextual linkage, but operator-controlled/self-profile material is not independent identity verification. |
| Justin Dobson's star-versus-graph and collusion/simultaneous-failure analysis is an implementation-informed contribution | `COUNTERPART_REPORTED` with source-text provenance | Evidence Custody Seam v0.3/v0.4 credits Justin in place. | Preserve the attribution and architecture insight; do not infer network topology facts not directly evidenced. |
| A witness count alone proves independence | `NOT_ESTABLISHED` / rejected by current seam text | v0.3/v0.4 replaces witness count with an independence/control/failure-domain figure. | Node/member count must not be promoted to an independence claim. |
| AILeash witness topology currently satisfies the v0.4 collusion/failure-domain metric at a particular numeric value | `NOT_ESTABLISHED` | Public peer list plus one exact positive peer/tip attestation show a concrete witness relationship, but do not establish ownership/control/failure-domain independence among all peers. | No numeric resilience figure is assigned by StegVerse from these artifacts alone. |
| The clean-room 784-record / 30-commitment Section 5 run was independently reproduced by StegVerse | `NOT_ESTABLISHED` | Appendix A reports the run and syscall trace; no retained StegVerse-side reproduction artifact is in this reconciliation lane. | Treat as counterpart implementation evidence, not StegVerse-verified conformance. |

## Promotion resulting from the exact witness artifact

The exact flavorflow peer/tip and sebbi.pro witness-attest response reproduce the core public-read behavior described by Appendix A R4. The following narrow behavioral claim is promoted:

> An unauthenticated third party can submit an exact `peer` + `tip` lookup to sebbi.pro's witness-attest route and receive a positive response stating whether that exact tip was witnessed, when it was first and last observed, how many times it was observed, and where the observation was sealed in sebbi.pro's own chain.

This promotion does **not** establish identity, current liveness, control-domain independence, completeness of all witness observations, Bitcoin confirmation of the witness block, or Richard Whitney's exact historical response artifact.

## OTS result

The supplied proof for stamp `1789455657` is useful but intentionally non-promoting for Bitcoin. The raw artifact is internally consistent with the service response: 721 decoded bytes and the exact reported proof SHA-256. Its own state is `pending`; it carries no Bitcoin block height and names pending OpenTimestamps calendars. It therefore proves only that a concrete OTS proof artifact was retained and that the artifact is pending, not that the digest is in Bitcoin.

## Relation to v0.4 R4 topology

The public peer list plus the exact positive flavorflow witness response demonstrate at least one concrete cross-system witnessing relationship. They still do not establish the administrative, ownership, infrastructure, or correlated-failure independence required by v0.4. The map therefore does not convert visible peers or observed relationships into a resilience score.

## Promotion rules

- Never promote operator-controlled README, `.well-known` declarations, profile text, or conformance JSON into independent runtime proof by themselves.
- A public endpoint response may be promoted only for the exact fields actually returned.
- A positive witness claim requires the exact peer/tip pair and retained response or equivalent checkable artifact; that condition is satisfied for the flavorflow pair above.
- A Bitcoin-confirmed claim requires independent proof verification; `pending`, calendar acceptance, or service-reported confirmation is not enough by itself.
- Identity, ownership, endorsement, and control-domain independence remain separate claims.
- Missing proof remains missing; it does not imply the event did not happen.
