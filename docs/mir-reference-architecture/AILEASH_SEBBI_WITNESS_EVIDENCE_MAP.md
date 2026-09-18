# AILeash / sebbi.pro witness evidence map

Updated: 2026-09-18
Goal Task: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV: `50000000100000`

Purpose: reconcile prior observations with the Evidence Custody Seam Appendix A claims without promoting unverified claims.

## v0.6 reconciliation

The user supplied Evidence Custody Seam v0.6. Appendix A now includes a separate A.2 sebbi.pro row contributed by its operator:

- requirement: R10 Vocabulary declaration;
- stated mechanism: sealed records do not state what their field names meant at sealing time;
- stated status: `NOT MET`.

Current evidence status:

| Claim | Current status | Evidence / observation | Bound conclusion |
|---|---|---|---|
| sebbi.pro historical witness artifacts do not self-carry vocabulary definitions | `SOURCE_INSPECTED` | Public `modules/witness.py` shows pre-v1.2 blocks retain `confirmed`, current code uses `self-consistent`, the sealed payload carries `witness_version` and term values but not vocabulary definitions, and current read routes attach vocabulary after lookup because sealed blocks travel while legends do not. | The artifact-portability gap is independently source-inspected. |
| sebbi.pro fails R10 as a complete conformance predicate | `COUNTERPART_REPORTED` + `PARTIALLY_SOURCE_INSPECTED` | Justin Dobson, the operator, disclosed the failure. Source inspection verifies the historical portability problem, but no complete audit has yet established whether vocabulary was durably published alongside the relevant R6 scheme for historical commitments. | Preserve the operator's `NOT MET` disclosure, but StegVerse must not present the blanket conformance failure as independently established until the R6/vocabulary publication coupling is inspected. |
| historical 784-record / 30-commitment clean-room run satisfies the current submitter-removed Section 5 test | `NOT_ESTABLISHED` | v0.6 explicitly says the prior run predates submitter removal and a rerun is intended. | The old run remains evidence only for the conditions it actually exercised. |

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
