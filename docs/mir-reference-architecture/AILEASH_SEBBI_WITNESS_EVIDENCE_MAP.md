# AILeash / sebbi.pro witness evidence map

Updated: 2026-09-18
Goal Task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

Purpose: reconcile prior observations with the Evidence Custody Seam Appendix A claims without promoting unverified claims.

## Current reconciliation

| Claim | Current status | Evidence / observation | Bound conclusion |
|---|---|---|---|
| sebbi.pro historical witness artifacts do not self-carry vocabulary definitions | `SOURCE_INSPECTED` | Public `modules/witness.py` shows pre-v1.2 blocks retain `confirmed`, current code uses `self-consistent`, the sealed payload carries version/term values but not the vocabulary definitions, and current read routes attach vocabulary after lookup. | The artifact-portability gap is independently source-inspected. |
| sebbi.pro fails R10 as a complete conformance predicate | `COUNTERPART_REPORTED` + `PARTIALLY_SOURCE_INSPECTED` | Justin Dobson disclosed the failure. Source inspection verifies the historical portability problem, but no complete audit excludes every durable R6-linked historical vocabulary publication. | Preserve the operator's `NOT MET` disclosure, but do not present the blanket conformance failure as independently established. |
| historical witness protocol/spec publication existed alongside v1.1 `confirmed` commitments | `NOT_ESTABLISHED` + `CURRENT_SOURCE_CORROBORATION` | Current source says `/x/witness/spec` and reader-facing vocabulary consolidation were added in v1.3, after v1.1 commitments and the v1.2 rename. | Strongly corroborates a later repair but does not exclude every other historical publication surface. |
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
