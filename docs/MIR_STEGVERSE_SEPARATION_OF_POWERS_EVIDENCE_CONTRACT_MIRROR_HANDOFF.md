# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-16
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED BY BOTH SIDES / REFERENCE ARCHITECTURE DRAFTING ACTIVE`

## Reconciliation note

The task identity had been used in collaboration and as the root/parent of canonical child tasks, but the parent canonical task shard and this handoff were not present on canonical main when rechecked on 2026-09-16. They are now materialized so the collaboration state is represented in GitHub rather than only in chat/status text.

## Frozen-contract state

Counterpart communication confirms mutual freeze acceptance of the v0.3 separation-of-powers evidence contract. Freeze acceptance is distinct from later conformance measurement and does not by itself prove downstream runtime execution.

The already-canonical child task `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001` remains the concrete section-12.8 cross-implementation conformance lane. Its current boundary remains: StegVerse and a neutral reproducer match the frozen fixture; authentic MIR independent reproduction is still required before that child can claim completion.

## New collaboration direction

The agreed next layer is a vendor- and model-neutral public reference architecture for governable/insurable agents organized around explicit separation of powers rather than a specific model or vendor.

StegVerse leads:

- actor/authority diagram;
- governance/governed-transition contract;
- prohibited authority-collapse list;
- minimum conformance receipts for each seam.

MIR/Richard leads the evidence-custody seam and its concrete minimum receipts. The two sides converge on prohibited collapses because those are where the boundaries become enforceable.

## Required architecture invariant

A clean interface or seam-conformance result is evidence about that seam, never proof of the downstream runtime chain behind it. Runtime proof requires custody of the authentic transition record plus a reconstruction path under contemporaneous witness/evidence semantics. No authority above the transition may infer that proof merely from its own decision or interface success.

Evidence custody/reconstruction therefore remains an independent corner. It must not collapse into governance/policy, admission/state-transition, execution, credential/provider authority, or observability.

## Counterpart claim requiring evidence before promotion

Richard reported that MIR's tamper-evident hash-chained checkpoints are now anchored to Bitcoin and that an inclusion-proof endpoint is next. Earlier collaboration explicitly established that no OTS artifact then existed and `otsStatus` remained a pending stub. The newer Bitcoin-anchor statement is therefore retained as `COUNTERPART_REPORTED / UNVERIFIED` until a concrete anchor receipt, transaction/proof reference, or independently checkable inclusion artifact is received. It must not be promoted into StegVerse conformance evidence by chat assertion alone.

## Current draft artifact

`docs/mir-reference-architecture/SEPARATION_OF_POWERS_REFERENCE_ARCHITECTURE_DRAFT.md`

This is a drafting artifact, not a frozen standard. It establishes the first actor/authority diagram, seam contracts, prohibited collapses, and minimum receipt shapes for review with MIR.

## Next action

Review the architecture draft against the frozen v0.3 contract and existing child conformance work; then send Richard the StegVerse first pass for the actor/authority diagram and governance/governed-transition seams while requesting his evidence-custody seam draft and a concrete artifact supporting the new Bitcoin-anchor claim. Preserve all unobserved runtime/proof predicates as unverified.
