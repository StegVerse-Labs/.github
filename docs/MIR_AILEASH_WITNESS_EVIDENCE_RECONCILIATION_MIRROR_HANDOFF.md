# MIR / AILeash witness evidence reconciliation mirror handoff

Updated: 2026-09-18
Goal Task ID: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / APPENDIX A R4 BEHAVIOR INDEPENDENTLY REPRODUCED / V0.6 REVIEW RECEIVED / SEBBI R10 PORTABILITY GAP SOURCE-INSPECTED / R6-LINKED PUBLICATION PATH INSPECTED WITHOUT FULL HISTORICAL PROMOTION / CLEAN-ROOM RERUN INTENDED / OTS PROOF RETAINED PENDING`

## Goal

Reconcile prior AILeash/sebbi.pro observations with the current Evidence Custody Seam Appendix A claims and Justin Dobson witness-topology contribution while preserving strict evidence-status boundaries.

## Current truth

The canonical prior observations remain unchanged:

- exact unauthenticated witness-attest behavior for one `flavorflowstrategy.uk` peer/tip is independently reproduced;
- the retained pending OTS artifact is byte/hash consistent but not Bitcoin-confirmed;
- identity, current liveness, control/failure-domain independence, complete topology, and the historical clean-room run remain unpromoted beyond the evidence actually retained.

## v0.6 joint-review draft — 2026-09-18

The user supplied the full Evidence Custody Seam v0.6 text.

Substantive convergence now present in v0.6:

- version allocation is limited to the shared document, while outside reviews identify their base version and do not allocate a competing version number;
- R10 remains separate from append-only correction, with the stronger explanation that append-only defines HOW correction is recorded while R10 supplies the sealed meaning against which a meaning correction can be made;
- the clean-room section now states that the historical run predates submitter removal and that a submitter-removed rerun is intended;
- the naming section retains `custodian` and explains why recorder, keeper, steward, registrar, and archivist are poorer fits;
- Appendix A now separates MIRegistry A.1 from sebbi.pro A.2 rather than treating one implementation as representative of the whole corner;
- the A.2 sebbi.pro entry is explicitly contributed by its own operator and is non-normative.

### One evidence-status issue remains

v0.6 Appendix A.2 currently says:

- R10 status: `NOT MET`;
- mechanism: “Sealed records do not state what their field names meant at the time of sealing.”

Source inspection independently supports the historical portability problem behind this statement. Public `modules/witness.py` shows that pre-v1.2 sealed blocks retain `confirmed`, current code maps the same check to `self-consistent`, the seal payload carries `witness_version` and term values but not the vocabulary definitions, and read-time routes now attach vocabulary because “sealed blocks travel and legends do not.”

However, R10's normative MUST is broader than “the artifact itself carries the vocabulary”: it requires that every commitment remain readable under the vocabulary in force and that the vocabulary be published alongside the R6 scheme. Carrying vocabulary inside the artifact is only a SHOULD.

Therefore the current StegVerse evidence supports a narrow source-inspected finding that historical sealed witness artifacts do not self-carry their vocabulary and depend on external publication/reconciliation. It does not yet independently establish that no historically durable R6-linked vocabulary publication exists for those commitments.

Disposition: do not reject v0.6 or reopen R10. Preserve Justin's operator-disclosed `NOT MET` row as counterpart disclosure, but if the appendix is intended to read as independently evidenced conformance status, either:
1. add the R6-linked publication evidence showing the vocabulary was not durably published alongside the scheme, or
2. phrase A.2 as operator-disclosed nonconformance pending independent R6/vocabulary verification.

## R6-linked historical publication inspection — 2026-09-18

Inspection was limited to the sebbi.pro witness commitment/vocabulary publication path relevant to the Appendix A.2 R10 disclosure.

New independently retrievable observations:

- current upstream source is available at `justrightdecorators-ops/aileash@b119e2d91cd37a4929d2c69367fcba51cb7a292f`;
- current `modules/witness.py` states that blocks sealed through witness v1.1 used `confirmed`, that v1.2 renamed the same check to `self-consistent`, and that those older blocks cannot be altered;
- the same source states that `/x/witness/spec` was added only in witness v1.3 because this module previously lacked the protocol/spec publication route used by other modules;
- the same source states that the reader-facing vocabulary consolidation was added in v1.3 after repeated wording drift;
- current live `/x/witness/peers` publishes both `confirmed` and `self-consistent` definitions and identifies current witness version 1.4;
- the previously retained StegVerse source reference `justrightdecorators-ops/aileash@f824ac83c5843053bdeca7eba53b77afa99465f5` is no longer resolvable through the upstream GitHub contents surface, so it cannot currently function as an independently retrievable historical publication anchor.

Bound conclusion:

This materially corroborates the operator-disclosed R10 failure shape: the historical value predates the witness protocol spec route, and the current source itself describes the vocabulary/spec publication as a later repair. It still does not prove that no other durable external publication of the v1.1 vocabulary existed alongside whatever R6 commitment-scheme material was in force. The relevant historical commit/release publication record is not presently recoverable from the inspected upstream surface.

Therefore Appendix A.2 remains:
- operator-disclosed `NOT MET`;
- independently source-corroborated for the historical vocabulary/spec publication gap;
- not promoted by StegVerse to a blanket independently established R10 conformance verdict.

Missing historical publication evidence remains missing; it is not converted into a claim that publication never existed.

## Clean-room rerun artifact check — 2026-09-18

The upstream repository was searched for the reported `784` records, `30` commitments, `clean-room`, and submitter-removed rerun terminology. No authentic submitter-removed rerun artifact matching the v0.6 Section 5 intention was found. The historical run remains historical evidence only, and no current-test predicate is promoted.

## Naming resolution

Canonical StegVerse usage supports `custodian`. Existing architecture uses `historical custodian` and `personal-record custodian` while keeping custody separate from governance, admission, transition, credential, and interpretation authority. No distinct canonical StegVerse term `evidence holder` was found.

The remaining v0.6 question about privacy-regime terminology is a drafting/legal-ambiguity question, not an architecture conflict. The document's explicit definition and non-claims already bound the role tightly enough for StegVerse architecture purposes.

## Clean-room state

The v0.6 wording is acceptable: the historical 784-record / 30-commitment run remains evidence only for what it exercised, does not inherit submitter removal retroactively, and a submitter-removed rerun is explicitly intended. No rerun is claimed complete.

## Evidence map

Canonical evidence map: `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md`.

## Next action

For joint review, accept the v0.6 merge structure and naming treatment. Raise only the narrow Appendix A.2 evidence-status clarification: operator-disclosed `NOT MET` is fine as disclosure, but independent conformance classification requires confirming the R6-linked historical vocabulary publication path. Do not reopen settled R1-R10 text.

Preserve the current bounded R10 disposition unless a durable historical v1.1/v1.2 scheme-linked vocabulary publication artifact becomes independently retrievable. Then coordinate the submitter-removed clean-room rerun and retain authentic artifacts before promoting the Section 5 current-test predicate.
