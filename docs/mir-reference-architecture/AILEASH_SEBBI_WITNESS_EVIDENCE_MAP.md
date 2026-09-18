# AILeash / sebbi.pro witness evidence map

Updated: 2026-09-18
Goal Task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

Purpose: reconcile prior observations with the Evidence Custody Seam Appendix A claims without promoting unverified claims.

## v0.7 reconciliation

The user supplied the complete Evidence Custody Seam v0.7 joint-review text. Appendix A now carries an explicit evidence class on every row and retains the separate A.2 sebbi.pro row contributed by its operator:

- requirement: R10 Vocabulary declaration;
- stated mechanism: sealed records do not state what their field names meant at sealing time;
- stated status: `NOT MET`.

Current evidence status:

| Claim | Current status | Evidence / observation | Bound conclusion |
|---|---|---|---|
| sebbi.pro historical witness artifacts do not self-carry vocabulary definitions | `SOURCE_INSPECTED` | Public `modules/witness.py` shows pre-v1.2 blocks retain `confirmed`, current code uses `self-consistent`, the sealed payload carries `witness_version` and term values but not vocabulary definitions, and current read routes attach vocabulary after lookup because sealed blocks travel while legends do not. | The artifact-portability gap is independently source-inspected. |
| sebbi.pro fails R10 as a complete conformance predicate | `COUNTERPART_REPORTED` + `PARTIALLY_SOURCE_INSPECTED` | Justin Dobson, the operator, disclosed the failure. Source inspection verifies the historical portability problem, but no complete audit has yet established whether vocabulary was durably published alongside the relevant R6 scheme for historical commitments. | Preserve the operator's `NOT MET` disclosure, but StegVerse must not present the blanket conformance failure as independently established until the R6/vocabulary publication coupling is inspected. |
| historical witness protocol/spec publication existed alongside the v1.1 `confirmed` commitments | `NOT_ESTABLISHED` + `CURRENT_SOURCE_CORROBORATION` | Current `modules/witness.py` at upstream commit `b119e2d91cd37a4929d2c69367fcba51cb7a292f` says `/x/witness/spec` was added in v1.3 and the vocabulary consolidation was also added in v1.3; the disputed blocks are v1.1-and-earlier and the rename occurred in v1.2. The previously retained commit `f824ac83c5843053bdeca7eba53b77afa99465f5` is no longer resolvable from the upstream contents surface. | Current source strongly corroborates that scheme/vocabulary publication was repaired later, but the inspected evidence does not exclude every other durable historical publication surface. Do not promote the blanket R10 verdict beyond the operator disclosure. |
| current sebbi.pro live vocabulary publication repairs historical readability going forward | `INDEPENDENTLY_OBSERVED_PUBLIC_RESPONSE` + `SOURCE_INSPECTED` | Live `/x/witness/peers` identifies witness v1.4 and publishes definitions for both legacy `confirmed` and current `self-consistent`; current source attaches the same vocabulary to reader-facing responses. | Current readability is established for the live service, but a later repair does not retroactively establish that vocabulary was durably published alongside the historical R6 scheme. |
| Richard Whitney agrees A.2's current reason establishes the artifact/SHOULD gap but does not by itself establish the R10 MUST failure | `USER_RETAINED_COUNTERPART_COMMUNICATION` | User-supplied review-thread screenshots show Richard explicitly distinguishing the MUST (durable publication alongside R6) from the SHOULD (carrying vocabulary in the artifact), stating that A.2's reason does not reach its own verdict, and contrasting it with A.1's "no published statement" rationale. | This corroborates the StegVerse interpretation of v0.6 as joint-review evidence. It does not establish the missing historical publication fact. |
| Appendix evidence class is explicit per row in v0.7 | `USER_SUPPLIED_SHARED_DOCUMENT_REVIEWED` | The supplied v0.7 text defines `Operator-disclosed`, `Demonstrated`, and `Third-party checkable` and places an evidence-class value on every A.1 and A.2 row. | The v0.6 presentation defect is repaired in the supplied v0.7 artifact; evidence class now travels with each claim. |
| v0.7 A.2 R10 reason is narrowed to the artifact condition rather than presented as independent proof of the MUST failure | `USER_SUPPLIED_SHARED_DOCUMENT_REVIEWED` | A.2 states that sealed records do not carry the vocabulary statement, marks the row `NOT MET, on the operator's own statement` / `Operator-disclosed`, and explicitly says the artifact condition reaches the SHOULD while the R6-linked publication question remains open. | The v0.7 text now matches the existing StegVerse evidence boundary. |
| MIRegistry A.1 R2 is independently established by the Section 5 run | `NOT_ESTABLISHED` + `OPERATOR_DISCLOSED_IN_V0.7` | v0.7 marks R2 `Operator-disclosed` and says the recorded run joined the external-time proof to the bundle sequence tip but did not complete an end-to-end chain walk; an outside attempt was indeterminate because of pagination rather than integrity. | Do not promote A.1 R2 beyond the document's operator-disclosed status without a clean outside chain walk. |
| Justin has answered whether durable R6-linked vocabulary publication existed before the rename | `NOT_ESTABLISHED` | Richard asks Justin the question directly in the supplied thread; no answer is present in the supplied screenshots. | The exact historical-publication predicate remains open. |
| historical 784-record / 30-commitment clean-room run satisfies the current submitter-removed Section 5 test | `NOT_ESTABLISHED` | v0.7 preserves that the prior run predates submitter removal and that a rerun is intended. | The old run remains evidence only for the conditions it actually exercised. |

## Previously established evidence

- exact unauthenticated `flavorflowstrategy.uk` witness-attest behavior is independently reproduced;
- public witness responses distinguish self-consistency from third-party verification;
- the retained OTS artifact is byte/hash consistent but remains pending and not Bitcoin-confirmed;
- witness roster membership is not control-domain independence;
- identity and full topology claims remain separate and unpromoted.

## Promotion rules

- Source inspection can establish implementation/source facts but not authentic runtime execution.
- Operator disclosure may be preserved as such without being promoted to independent verification.
- A `NOT MET` conformance row based on a MUST should be independently promoted only when every alternative allowed by that MUST has been checked or excluded.
- The R10 SHOULD that vocabulary travel inside the artifact is stronger portability guidance, but failure of the SHOULD alone does not establish failure of the R10 MUST if durable scheme-linked publication exists elsewhere.
- Missing proof remains missing; it does not imply the event did not happen.
- A later current publication can repair present readability without proving that the same vocabulary was durably published alongside the historical commitment scheme.
