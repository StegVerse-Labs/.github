# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-16
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED BY BOTH SIDES / REFERENCE ARCHITECTURE DRAFT V0.2 MATERIALIZED / COUNTERPART EVIDENCE-SEAM INPUT PENDING`

## Canonical reconciliation

The Goal Task is canonically registered on main and remains `ACTIVE`. The frozen v0.3 collaboration state is preserved separately from this post-freeze reference-architecture drafting lane.

## Frozen-contract state

Counterpart communication confirms mutual freeze acceptance of the v0.3 separation-of-powers evidence contract. Freeze acceptance is distinct from later conformance measurement and does not itself prove downstream runtime execution.

The already-canonical child task `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001` remains the concrete section-12.8 cross-implementation conformance lane. Its current boundary remains: StegVerse and a neutral reproducer match the frozen fixture; authentic MIR independent reproduction is still required before that child can claim completion.

## Reference-architecture direction

The agreed next layer is a vendor- and model-neutral public reference architecture for governable/insurable agents organized around explicit separation of powers rather than a specific model or vendor.

StegVerse leads:

- actor/authority graph;
- governance/governed-transition contract;
- prohibited authority-collapse list;
- minimum conformance receipts for each seam;
- proof-scope/proof-ceiling semantics;
- fail-closed negative conformance cases.

MIR/Richard leads the evidence-custody/reconstruction seam and its concrete minimum receipts. The two sides converge on prohibited collapses because those are where the boundaries become enforceable.

## Current StegVerse draft v0.2

`docs/mir-reference-architecture/SEPARATION_OF_POWERS_REFERENCE_ARCHITECTURE_DRAFT.md`

Draft v0.2 is materialized on canonical main. It is **not frozen** and does not alter frozen v0.3.

It now defines:

1. a non-linear six-corner authority graph for governance/policy, admission/state transition, execution, credential/provider authority, evidence custody/reconstruction, and observability;
2. a common receipt envelope with explicit `proof_scope` and `proof_ceiling` semantics;
3. minimum seam-specific receipt fields for all six corners;
4. twelve prohibited authority collapses;
5. the invariant `SEAM_CONFORMANCE != RUNTIME_CHAIN_PROOF`;
6. a six-corner conformance matrix;
7. fail-closed minimum negative tests for each corner;
8. runtime-chain proof composition rules requiring authentic mutually consistent records rather than inference from one authority's success;
9. evidence-status discipline for `VERIFIED`, `COUNTERPART_REPORTED`, `NOT_REQUESTED`, `UNAVAILABLE`, and `PENDING`;
10. an insurability/governability interpretation that provides evidence properties for external evaluation without claiming that any implementation is itself insurable.

## Required architecture invariant

A clean interface or seam-conformance result is evidence about that seam, never proof of the downstream runtime chain behind it. Runtime proof requires custody of authentic transition records plus a reconstruction path under the applicable contemporaneous evidence semantics. No authority above the transition may infer that proof merely from its own decision or interface success.

The reverse is also explicit: evidence custody cannot infer missing upstream authorization merely because an event record exists.

Evidence custody/reconstruction therefore remains an independent corner. It must not collapse into governance/policy, admission/state-transition, execution, credential/provider authority, or observability.

## Counterpart claim requiring evidence before promotion

Richard reported that MIR's tamper-evident hash-chained checkpoints are now anchored to Bitcoin and that an inclusion-proof endpoint is next. Earlier collaboration explicitly established that no OTS artifact then existed and `otsStatus` remained a pending stub. The newer Bitcoin-anchor statement therefore remains `COUNTERPART_REPORTED / UNVERIFIED` until a concrete anchor receipt, transaction/proof reference, or independently checkable inclusion artifact is received. It must not be promoted into StegVerse conformance evidence by chat assertion alone.

## Evidence still required from MIR

No new MIR evidence-custody seam artifact or independently checkable Bitcoin-anchor/inclusion artifact is currently present in the canonical workstream. Accordingly:

- `COUNTERPART_EVIDENCE_SEAM_DRAFT_RECEIVED` remains unsatisfied;
- the Bitcoin-anchor claim remains counterpart-reported/unverified;
- MIR independent `mir.leaf.v3` reproduction remains pending in the child task;
- no downstream runtime-chain proof is claimed.

## Next action

Deliver/review draft v0.2 with MIR and obtain Richard's evidence-custody/reconstruction first pass, concrete minimum evidence receipts, proposed prohibited-collapse changes, and one checkable Bitcoin anchor/inclusion artifact if that claim is to be promoted. Then reconcile those artifacts against frozen v0.3 and the existing `mir.leaf.v3` fixture, preserve every unobserved predicate as unverified, and only then prepare a jointly reviewable next-freeze candidate.