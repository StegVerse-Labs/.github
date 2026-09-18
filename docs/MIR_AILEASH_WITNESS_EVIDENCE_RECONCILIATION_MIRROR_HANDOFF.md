# MIR / AILeash witness evidence reconciliation mirror handoff

Updated: 2026-09-18
Goal Task ID: `MIR-AILEASH-WITNESS-EVIDENCE-RECONCILIATION-001`
Parent Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / APPENDIX A R4 BEHAVIOR INDEPENDENTLY REPRODUCED / V0.7 USER-SUPPLIED SHARED ARTIFACT REVIEWED / V0.8 COUNTERPART RUN REPORT OBSERVED / SUBMITTER-REMOVED RUN CLAIMED COMPLETE BUT ARTIFACT NOT YET INDEPENDENTLY RETRIEVED / PER-ROW EVIDENCE CLASS PRESENT / A.2 R10 BASIS NARROWED / A.1 R2 LIMITATION EXPLICIT / SEBBI R10 PORTABILITY GAP SOURCE-INSPECTED / R6-LINKED PUBLICATION PATH INSPECTED WITHOUT FULL HISTORICAL PROMOTION / OTS PROOF RETAINED PENDING`

## Goal

Reconcile prior AILeash/sebbi.pro observations with the current Evidence Custody Seam Appendix A claims and Justin Dobson witness-topology contribution while preserving strict evidence-status boundaries.

## Current truth

The canonical prior observations remain unchanged:

- exact unauthenticated witness-attest behavior for one `flavorflowstrategy.uk` peer/tip is independently reproduced;
- the retained pending OTS artifact is byte/hash consistent but not Bitcoin-confirmed;
- identity, current liveness, control/failure-domain independence, and complete topology remain unpromoted beyond the evidence actually retained.

## v0.7 joint-review state

The user supplied the complete Evidence Custody Seam v0.7 joint-review text. The artifact repaired the v0.6 presentation defect by carrying an evidence class on every Appendix A row: `Operator-disclosed`, `Demonstrated`, or `Third-party checkable`.

For A.2 R10, v0.7 correctly narrows the independently supported mechanism to the artifact condition: historical sealed records do not self-carry the field-meaning statement, while the full `NOT MET` remains operator-disclosed pending the historical R6-linked publication question.

For A.1 R2, v0.7 explicitly marks the row `Operator-disclosed` because the prior Section 5 run joined external time to the same sequence tip but did not walk the chain end to end; an outside attempt was indeterminate because of pagination.

The open questions after v0.7 were:

1. whether a durable vocabulary publication tied to the R6 scheme covered the historical commitments before the rename;
2. whether `custodian` collides with a privacy-regime term in a way the document's definition/non-claims do not already resolve;
3. whether an authentic submitter-removed rerun of the Section 5 test exists.

## Evidence Custody Seam v0.8 — user-retained counterpart report observed

The user supplied review-thread screenshots in which Richard Whitney states that v0.8 is published and that the previously intended submitter-removed run now exists.

Richard reports that the run used a live production export and produced these results:

- one artifact containing 1,534 events and 50 checkpoints;
- 48 checkpoints reported as Bitcoin-anchored;
- 1,406 events reported as falling under an anchored checkpoint;
- an OpenTimestamps proof for checkpoint 4714 reported as committing, when read offline, to the exact sequence tip carried inside the bundle;
- two independently operated explorers reported as confirming the block Merkle root;
- all 1,534 leaf hashes reported as recomputed and all 1,534 inclusion proofs reported as reaching their roots;
- chain links reported unbroken;
- the verification key reported fetched from a different endpoint than the bundle and pinned before use;
- zero socket-family syscalls reported across three runs;
- a maximum observed gap of 233 ms between a production submitter's claimed `occurredAt` and the custodian receipt, while claimed ordering still differed from proof-derived ordering;
- an adversarial local case with two submitters, one adversarial, claims displaced by 2,453 days and asserted in the exact reverse of sealing order, with proof-derived order returning the reverse of the claimed order;
- negative controls reported fail-closed when editing the submitter's claim, editing a weight, or substituting a valid but unpinned key;
- ordering reported as derived from checkpoint-chain position plus each leaf's index inside its own tree, not from any party-provided date field.

Richard also records three corrections to his own analysis:

1. an initial within-checkpoint sort by `createdAt` was wrong because that substituted the custodian's receipt time for proof-derived position; he reports correcting the analysis to derive position from the proof path before counted runs;
2. syscall traces were miscounted twice by treating signal lines as syscalls; he reports the corrected socket-family count as zero for every run;
3. R5 was understated in the appendix, because refusing a bundle-carried key is an artifact construction property rather than merely a runtime check.

### Evidence classification for v0.8

These v0.8 statements are presently classified as `USER_RETAINED_COUNTERPART_COMMUNICATION`.

The screenshots materially supersede the earlier `rerun intended` statement as a counterpart claim: Richard now says the submitter-removed rerun exists. However, no matching public run artifact, bundle, proof package, or repository-bound result containing the reported 1,534-event / 50-checkpoint / checkpoint-4714 evidence was independently located in the inspected public GitHub source.

Therefore:

- do not continue to describe the rerun as merely intended;
- do describe it as `COUNTERPART_REPORTED_COMPLETE`;
- do not promote the reported run statistics, Bitcoin-anchor checks, offline OTS binding, chain walk, syscall trace, negative controls, or order reconstruction to independently verified until the underlying artifacts are retrievable and checked;
- preserve Richard's explicit self-corrections as part of the run record rather than smoothing them away.

## R6-linked historical publication inspection

Inspection of the current sebbi.pro witness source remains unchanged:

- current upstream source at `justrightdecorators-ops/aileash@b119e2d91cd37a4929d2c69367fcba51cb7a292f` says blocks through witness v1.1 used `confirmed`, v1.2 renamed the same check to `self-consistent`, and the older blocks cannot be altered;
- `/x/witness/spec` and consolidated reader-facing vocabulary were added only in witness v1.3;
- current live `/x/witness/peers` publishes both legacy and current definitions;
- the historical publication record still does not exclude every other durable external publication surface.

Bound conclusion: the source strongly corroborates the operator-disclosed historical vocabulary/spec publication gap, but StegVerse still does not independently promote a blanket R10 conformance verdict beyond the evidence actually inspected.

## Naming resolution

Canonical StegVerse usage supports `custodian`. Existing architecture uses `historical custodian` and `personal-record custodian` while keeping custody separate from governance, admission, transition, credential, and interpretation authority. No specific privacy-regime collision has been established in the supplied materials.

## Evidence map

Canonical evidence map: `docs/mir-reference-architecture/AILEASH_SEBBI_WITNESS_EVIDENCE_MAP.md`.

## Next action

Retrieve the authentic v0.8 submitter-removed run artifacts if Richard/MIRegistry publishes or shares them: the production export bundle, checkpoint-chain material, checkpoint 4714 OpenTimestamps proof, inclusion proofs, pinned key record, explorer evidence, syscall traces, adversarial fixtures, and negative-control results. Recompute the run claims independently before promoting any row from counterpart-reported/demonstrated to third-party-checkable or independently established.

Separately, preserve the unresolved historical A.2 R10 publication question until Justin's answer or an independently retrievable historical publication record resolves it.