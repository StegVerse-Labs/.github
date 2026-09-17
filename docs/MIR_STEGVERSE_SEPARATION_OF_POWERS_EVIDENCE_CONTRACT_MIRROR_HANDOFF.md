# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED / REFERENCE ARCHITECTURE DRAFT V0.2 / PROVEN SV002 ROUTE REUSED / EVENT-DRIVEN MIR RUNTIME MODEL / PER-TRANSITION MASTER RECORDS CONFIRMATION MATERIALIZED / COUNTERPART EVIDENCE-SEAM INPUT PENDING`

## Canonical state

The Goal Task remains `ACTIVE`. Frozen v0.3 remains separate from the post-freeze reference-architecture lane. Draft v0.2 continues to enforce separation of governance, admission/state transition, execution, credential/provider authority, evidence custody/reconstruction, and observability. `SEAM_CONFORMANCE != RUNTIME_CHAIN_PROOF` remains unchanged.

The child `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001` still requires authentic MIR independent reproduction. Richard's Bitcoin-anchor statement remains `COUNTERPART_REPORTED / UNVERIFIED` until an independently checkable anchor/inclusion artifact is supplied.

## Proven route and current runtime model

StegVerse-002 already established the reusable route:

```text
registered StegVerse Node
-> Interlock
-> InTr materialization
-> bounded invocation lease
-> EVENT_EPHEMERAL runtime
-> execution-time runtime identity
-> authority-owned continuation
-> independent Master Records reconstruction
```

`MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001` duplicates that route first and adds only current MIR-specific Goal/COSV, destination-profile, transition, and evidence requirements. Generic SV002 mechanics are not a fresh re-proof gate; historical receipts grant no present authority.

The MIR event runtime is state-transition dependent, not an idle service. The current event must enter existing authorized ingress, receive the current Interlock/InTr transition, and only then materialize the `EVENT_EPHEMERAL` runtime. Remote-device/surface reachability is not a runtime predicate.

The current unresolved runtime boundary is:

`AUTHENTIC_MIR_EVENT_INGRESS_OR_STATE_TRANSITION_RECEIPT_NOT_OBSERVED`

## Per-transition Master Records confirmation contract

The existing reusable Master Records worker now fans current MIR one-way evidence into independent confirmation packets and requires exact-byte reconstruction for each observed transition before aggregate one-way evidence can be accepted.

Confirmation sequence:

```text
01 CURRENT_GOAL_COSV_BOUND
02 CURRENT_INTERLOCK_INTR_INGRESS_RECEIVED
03 RTC-STEGVERSE-EGRESS-007
04 RTC-INTERLOCK-INTR-TRANSPORT-008
05 RTC-FARSIDE-FINAL-009
06 MIR_DESTINATION_EVIDENCE_RETAINED
07 EXACT_GOVERNED_RETURN_PACKET_RETAINED
```

Each packet uses `stegverse.mir-state-transition-confirmation/v1`, has `authority_effect=NONE_CONFIRMATION_EVIDENCE_ONLY`, and is individually ingested/reconstructed by Master Records. The diagnostic uses `stegverse.mir-state-transition-master-records-diagnostic/v1` and reports `first_non_return_transition_id`. Missing transitions are classified `TRANSITION_NOT_OBSERVED`; evidence custody cannot fabricate or authorize them.

Implementation/source evidence:

- `workers/reusable_task_master_records_roundtrip.py` updated at `540d71d64f9e8544d48e50f4b7495410dbb9ea9e`;
- `tests/test_mir_transition_master_records_confirmation.py` added at `707c3932059db1d280e3d5e196a9e706949cc1b2`;
- `receipts/preflight/MIR-STATE-TRANSITION-MASTER-RECORDS-CONFIRMATION-001.json` added at `16e5ca194b526744df34b93f56eb222f661fe8a6`;
- Site README reconciled at `0bf08e6d0dbd2b4a31af761877fb5bd810b60ba6`;
- Site transport handoff reconciled at `846f47879d1a86fc87a88e34b082aad515511f55`.

## Current break location

No authentic current MIR event-ingress or Interlock/InTr state-transition receipt is retained in canonical evidence. No current MIR one-way evidence exists from which the transition-confirmation fanout can truthfully run. Therefore the current break is **upstream of the Master Records return path**, at the current MIR ingress/state-transition boundary.

This is not presently evidence of a Master Records failure. Once an authentic current transition exists, the new confirmation fanout will identify the first exact transition whose packet does not return from Master Records, if any.

## Separation-of-powers invariants

- WorkerCoordinator remains claim/fence authority.
- Interlock/InTr remains admission/state-transition authority.
- TV/TVC remains credential authority where required.
- MIR remains MIR-native semantics authority.
- Master Records remains observed-reality custody/reconstruction only.
- GitHub/GitHub Actions remain source validation/evidence transport only; runtime authority `NONE`.
- Confirmation packets do not grant transition authority.
- Missing transition evidence cannot be inferred from later custody/reconstruction.

## Counterpart evidence still required

Separately from the owned-mirror transport work, Richard/MIR evidence-custody seam input, concrete minimum custody receipts, independently checkable Bitcoin anchor/inclusion evidence, and authentic MIR `mir.leaf.v3` independent reproduction remain pending.

## Next action

Cause or observe the current MIR-bound event entering the existing authorized ingress/Interlock/InTr path. When authentic transition evidence exists, emit the per-transition confirmation packets through Master Records, use `first_non_return_transition_id` to isolate the exact failing return boundary, repair only that boundary, and then continue governed return/full round-trip evidence without creating a second scheduler, dispatcher, runtime plane, device prerequisite, or generic SV002 re-proof gate.
