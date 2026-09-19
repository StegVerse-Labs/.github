# AILeash / sebbi.pro witness evidence map

Updated: 2026-09-19
Goal Task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

Purpose: reconcile prior observations with the Evidence Custody Seam Appendix A claims without promoting unverified claims.

## Current reconciliation

| Claim | Current status | Evidence / observation | Bound conclusion |
|---|---|---|---|
| sebbi.pro historical witness artifacts do not self-carry vocabulary definitions | `SOURCE_INSPECTED` | Public `modules/witness.py` shows pre-v1.2 blocks retain `confirmed`, current code uses `self-consistent`, the sealed payload carries version/term values but not the vocabulary definitions, and current read routes attach vocabulary after lookup. | The artifact-portability gap is independently source-inspected. |
| sebbi.pro fails R10 as a complete conformance predicate | `COUNTERPART_REPORTED` + `PARTIALLY_SOURCE_INSPECTED` | Justin Dobson disclosed the failure. Source inspection verifies the historical portability problem, but no complete audit excludes every durable R6-linked historical vocabulary publication. | Preserve the operator's `NOT MET` disclosure, but do not present the blanket conformance failure as independently established. |
| historical vocabulary and commitment-scheme source coexist before the rename | `INDEPENDENTLY_RETRIEVED_HISTORICAL_SOURCE` | Commit `2d6715868bb2812b98d874ab17890ff89ece30d5` contains witness v1.1 definitions and peer legend (`e6093a954837a418ceef99e6e474bcd61c59704f`) alongside server chain hashing/sealing/verification (`99718aa051dc09448ade1a6700abc738ebc38a13`). | Corrects the inference that the later witness-specific spec route establishes absence of earlier publication. Exact historical commitment coverage and public-availability timing remain unresolved; neither blanket R10 failure nor compliance is promoted. |
| previously unavailable historical source ref | `OBJECT_TYPE_ERROR_CORRECTED` | `f824ac83c5843053bdeca7eba53b77afa99465f5` is a retrievable v1.4 Git blob, not a commit. It resolves as `modules/witness.py` at commit `4c78cdff5695d5f1ff8b141f2f3befc45dce1bbe`. | An invalid commit lookup did not establish loss of historical publication. |
| current sebbi.pro live vocabulary publication repairs readability going forward | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` + `SOURCE_INSPECTED` | Live `/x/witness/peers` identifies current witness vocabulary for both legacy and current terms; current source attaches vocabulary to reader-facing responses. | Current readability is established; later repair does not retroactively prove historical publication alongside R6. |
| Appendix evidence class is explicit per row in v0.7 | `USER_SUPPLIED_SHARED_DOCUMENT_REVIEWED` | v0.7 defines `Operator-disclosed`, `Demonstrated`, and `Third-party checkable` and places an evidence class on every A.1/A.2 row. | The v0.6 presentation defect is repaired. |
| v0.7 A.2 R10 reason is narrowed to the artifact condition | `USER_SUPPLIED_SHARED_DOCUMENT_REVIEWED` | A.2 states that sealed records do not carry the vocabulary statement, while the full `NOT MET` remains operator-disclosed and the R6-linked publication question remains open. | The text now matches the evidence boundary. |
| MIRegistry A.1 R2 was independently established by the pre-v0.8 Section 5 run | `NOT_ESTABLISHED` + `OPERATOR_DISCLOSED_IN_V0.7` | v0.7 says the prior run joined external time to the bundle tip but did not complete an end-to-end chain walk; an outside attempt was indeterminate due to pagination. | Do not retroactively promote the earlier run. |
| submitter-removed rerun exists | `COUNTERPART_REPORTED_COMPLETE` | User-supplied v0.8 review-thread screenshots show Richard Whitney stating that the rerun now exists and that the appendix no longer calls it intended. | Supersedes `rerun intended` as a counterpart claim, but is not yet independently verified. |
| v0.8 production-export run contains 1,534 events / 50 checkpoints / 48 Bitcoin-anchored checkpoints / 1,406 events under an anchored checkpoint | `COUNTERPART_REPORTED` | Richard reports these counts in the supplied thread. No matching public artifact was located in the inspected upstream GitHub source. | Preserve exact reported counts with attribution; do not treat as independently measured. |
| checkpoint 4714 OTS proof binds offline to the same tip carried in the bundle and independent explorers confirm the attested block Merkle root | `COUNTERPART_REPORTED` | Richard reports offline OTS verification and two independent explorers. Underlying proof bytes and explorer records are not yet independently retained here. | Potentially closes the old R2 shape only after artifact retrieval and independent recomputation. |
| all 1,534 leaves/proofs recompute and chain links are unbroken | `COUNTERPART_REPORTED` | Richard reports all leaf hashes recomputed, inclusion proofs reaching roots, and chain links unbroken. | Treat as run report, not yet third-party verification. |
| verification key came from a different endpoint and was pinned before use | `COUNTERPART_REPORTED` | Richard reports separate endpoint retrieval and pre-use pinning. | Strong evidence design if reproduced; not yet independently checked. |
| zero socket-family syscalls across three runs | `COUNTERPART_REPORTED_WITH_SELF_CORRECTION` | Richard states two earlier syscall-counting mistakes and says the corrected metric is zero socket-family syscalls in every run. | Preserve the corrections and require raw traces for independent promotion. |
| proof-derived order differs from submitter-claimed order even for ordinary production data | `COUNTERPART_REPORTED` | Richard reports max claimed-time/receipt gap of 233 ms, yet claimed order and proof-derived order differ. | Supports the conceptual distinction between asserted timestamps and proof-derived order; independent artifact check still required. |
| adversarial local run reverses claimed vs proven order and negative controls fail closed | `COUNTERPART_REPORTED` | Richard reports two submitters, one adversarial, 2,453-day displaced claims, reverse claimed order, and refusal on edited claim, edited weight, or valid-but-unpinned key. | Strong negative-test shape if reproduced; no independent promotion yet. |
| ordering is derived from checkpoint-chain position plus leaf index, not party date fields | `COUNTERPART_REPORTED_METHOD` | Richard explicitly states the method and records correcting an earlier `createdAt` sort mistake. | The method is materially better aligned with evidence custody than date-field ordering; independent code/artifact inspection remains pending. |
| R5 appendix wording was understated | `COUNTERPART_REPORTED_DOCUMENT_CORRECTION` | Richard states that refusal to verify against a bundle-carried key is an artifact-construction property, not merely a runtime check. | Track as a document correction pending direct v0.8 artifact review. |
| Justin has answered whether durable R6-linked vocabulary publication existed before the rename | `NOT_ESTABLISHED` | No answer is present in the supplied material. | Historical-publication predicate remains open. |

## Previously established evidence

- exact unauthenticated `flavorflowstrategy.uk` witness-attest behavior is independently reproduced;
- public witness responses distinguish self-consistency from third-party verification;
- the retained OTS artifact is byte/hash consistent but remains pending and not Bitcoin-confirmed;
- witness roster membership is not control-domain independence;
- identity and full topology claims remain separate and unpromoted.

## Promotion rules

- Source inspection can establish implementation/source facts but not authentic runtime execution.
- Operator/counterpart disclosure may be preserved as such without being promoted to independent verification.
- A run report becomes independently established only after its artifacts can be retrieved and its measurements recomputed.
- A `NOT MET` conformance row based on a MUST should be independently promoted only when every alternative allowed by that MUST has been checked or excluded.
- Failure of R10's SHOULD alone does not establish failure of the MUST if durable scheme-linked publication exists elsewhere.
- Missing proof remains missing; it does not imply the event did not happen.
- Corrections and failed intermediate analyses are part of the evidence record and must not be erased from provenance.

## Historical-source recovery — 2026-09-19

Full immutable source links, object IDs, source-method details and remaining commitment-binding predicates are retained in [the canonical handoff](../MIR_AILEASH_WITNESS_EVIDENCE_RECONCILIATION_MIRROR_HANDOFF.md#r6-linked-historical-publication-inspection--corrected-2026-09-19). The v0.8 run report above is preserved from existing PR #2119; this continuation did not retrieve the underlying run artifacts and does not promote the report to independent verification.

## Targeted acquisition status — 2026-09-19

No exact disputed historical sealed block or authentic 1,534-event / 50-checkpoint rerun package was retrieved in this continuation. The public roster identifies MIR's transparency-tip locator; full sebbi.pro block/export routes are keyed in published source. Browser retrieval returned ERR_BLOCKED_BY_CLIENT, which is not evidence that either service or artifact is absent. Focused MIR-2025 public-source searches returned no matching package. Exact artifact inputs and verification steps are recorded in the canonical handoff's targeted acquisition section. R10 classification and all prior proof ceilings remain unchanged.


## Generation 70 reconciliation note — 2026-09-19

Task Registry generation 70 was re-read from canonical main `67d082eb648a65f4b1a3dc61b639354de7c3b933`; the task remains ACTIVE. Complete-tree inspection of AILeash revision `2d6715868bb2812b98d874ab17890ff89ece30d5` confirms co-location of v1.1 witness vocabulary/legend and chain commitment implementation, but did not yield an authentic historical sealed-block/export corpus. Consequently no exact disputed commitment has yet been bound to that revision, and A.2 R10 remains operator-disclosed rather than independently promoted.

Fresh public GitHub searches for the v0.8 run's distinctive counts/identifiers did not retrieve the underlying 1,534-event / 50-checkpoint package or checkpoint-4714 proof material. The rerun therefore remains `COUNTERPART_REPORTED_COMPLETE`. The prior 784-record / 30-commitment run remains historical and settled; no classification or custodian-naming change is made here.


## Generation 86 new walk/reset-disclosure source — 2026-09-19

Upstream AILeash main `8edfe2b97e489c3d1f1a576505f95bfbe6c1b7d7` now contains a public current-chain walk source and a reset-disclosure source. `modules/walk.py` v1.1.0 publishes a genesis-to-tip traversal contract for the **post-2026-09-07** chain and exact preimage recomputation for public blocks. `modules/disclosure.py` v1.0.0 explicitly states that pre-reset blocks belong to an earlier chain and cannot be verified against the current chain; its source leaves the previous chain's final tip and height unrecorded in the disclosure.

This narrows the unresolved R10 evidence question: current-chain walkability does not bridge the historical chain. No disputed pre-reset commitment was authenticated or bound to v1.1 by this source, so R10 remains operator-disclosed `NOT MET` without independent blanket failure/compliance promotion. The v0.8 1,534/50 package remains counterpart-reported complete, and the historical 784/30 run remains settled.


## Generation 111 pre-reset completeness / Bitcoin verification — 2026-09-19

A one-shot public-evidence transport recovered authentic retained August 2026 completeness commitments from sebbi.pro. The subjects commitment is old-chain block `1895`, root `5a34b9af7ab85de4d2b9b3d18c238c4aaa632333f4fedeb4c5fe1d5c6953abff`, chain seal `4a99a3b5fa83d79a8baba0c8cd4415bab37b0435ee5dff14d50900e7b0acf260`, with 30 leaves. Independent Merkle replay verified membership of `wit:flavorflowstrategy.uk`, `wit:praesidium`, and `wit:red-flag-ai-pro` in that retained pre-reset set.

The exact retained OTS proof for `4a99a3b5...` (original proof SHA-256 `275186cb44c66ef366181d10f26daa9df0afec6a44e996a491061e352604d38f`) was independently upgraded. Corrected run `35463311073` established Bitcoin attestations at heights `965082` and `965103`; proof-derived Merkle roots matched both Blockstream and mempool.space at both heights. This advances the August subjects commitment to independently verified external timestamp anchoring.

This does not reconstruct block 1895's original chain preimage or expose an exact disputed historical witness record's sealed `witness_version`/liveness term. Therefore historical binding to `2d6715868bb2812b98d874ab17890ff89ece30d5` remains unresolved and A.2 R10 remains operator-disclosed `NOT MET`. The v0.8 1,534/50 package remains counterpart-reported complete; the historical 784/30 run remains settled.

## Canonical strict state-dependent progression — 2026-09-19

This evidence map is now explicitly ordered rather than checkpoint-based. The canonical progression is:

`PRE_RESET_COMPLETENESS_COMMITMENT_CLOSED`
→ `HISTORICAL_WITNESS_RECORD_RECONSTRUCTED`
→ `HISTORICAL_WITNESS_SEAL_RECOMPUTED`
→ `HISTORICAL_WITNESS_VERSION_TERM_BOUND`
→ `R10_DISPOSITION_RECONCILED`.

Each successor MUST consume the immediately preceding Master Records closure, and that predecessor closure must be `RECORDED` with reconstruction PASS, required-evidence-validation PASS, and exact receipt/reconstruction digest equality. No independent observation, later artifact, parallel checkpoint, or stronger side evidence may skip a predecessor, satisfy a later state directly, or alter R10 before the ordered chain reaches the terminal disposition state.

Current canonical position is state 1: the independently retrieved and Bitcoin-anchored `4a99a3b5...` pre-reset subjects commitment. The only admissible successor is individual historical witness-record reconstruction. R10 remains operator-disclosed `NOT MET` until all intermediate states close in order.
