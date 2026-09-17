# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-16
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED / REFERENCE ARCHITECTURE DRAFT V0.2 / PROVEN SV002 ROUTE REUSED / MIR RESIDENT EXECUTION REQUEST MATERIALIZED / COUNTERPART EVIDENCE-SEAM INPUT PENDING`

## Canonical state

The Goal Task remains `ACTIVE`. Frozen v0.3 is preserved separately from the post-freeze reference-architecture lane. Draft v0.2 remains non-frozen and continues to enforce the six-corner authority model, bounded proof scopes/ceilings, fail-closed negative tests, and `SEAM_CONFORMANCE != RUNTIME_CHAIN_PROOF`.

The child `MIR-LEAF-V3-CONFORMANCE-FIXTURE-001` still requires authentic MIR independent reproduction before completion. Richard's newer Bitcoin-anchor statement remains `COUNTERPART_REPORTED / UNVERIFIED` until an independently checkable anchor/inclusion artifact is supplied.

## Proven-route duplication rule

StegVerse-002 already established the successful reusable engineering route:

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

The transport successor `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001` therefore duplicates that route first and adds only current MIR-specific bindings/evidence. Generic SV002 Node/Interlock/InTr/lease/runtime mechanics may not be inserted as another re-proof gate. Historical receipts prove the old event only and grant no present authority.

Canonical route source remains:

- `StegVerse-Labs/Site/data/mir-roundtrip-egress-sv002-route-binding.v1.json`
- `StegVerse-Labs/Site/docs/MIR_ROUNDTRIP_EGRESS_AUTHENTICITY_MIRROR_HANDOFF.md`

## Current authority-owned execution package

The child transport lane is now installed into the existing sovereign WorkerCoordinator/runtime source rather than left as documentation-only work. Canonical `.github` source contains:

- `control/task-vectors/MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001.json`
- `control/task-vector-index.d/MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001.json`
- `control/worker-registry.d/mir-roundtrip-egress-authenticity-001.json`
- `control/process-worker-adapters.d/mir-roundtrip-egress-authenticity-001.json`
- `control/resident-execution-request.d/mir-roundtrip-egress-authenticity-001.json`
- `workers/mir_roundtrip_egress_authenticity_worker.py`

The standing request is machine-owned and asks the existing WorkerCoordinator to mint the fresh claim/fence and execute exactly one current MIR-bound invocation under COSV `50000000100000`. It does not create another scheduler, dispatcher, WorkerCoordinator, runtime, transport plane, credential path, or user-device dependency.

The worker binds the current Goal/COSV, `destination_profile=MIR`, the current retained registered Node/Interlock receipt, and the reused sequence:

```text
RTC-STEGVERSE-EGRESS-007
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> RTC-FARSIDE-FINAL-009
```

It uses the existing StegOS `SovereignLocalEventRuntimeAdapter` and `run_mir_profile_transition`, retains the exact MIR MIRROR response packet, requires the MIR MIRROR external-ingress receipt/correlation, and delegates custody/reconstruction to the existing `workers/reusable_task_master_records_roundtrip.py`, which invokes destination-owned Master Records ingest/reconstruction and enforces exact-byte equality.

## Runtime proof boundary

One-way MIR MIRROR transport is promoted only if the same current invocation proves:

```text
current Goal/COSV binding
MIR destination profile binding
current StegVerse-side egress
current Interlock/InTr transport
MIR MIRROR far-side transition
MIR destination evidence retention
Master Records reconstruction of current final exit
```

Any successful owned-mirror receipt must retain provenance `MIR_MIRROR_BUILD_TEST_COUNTERPART_RUNTIME`; it is not evidence that the authentic external MIR endpoint executed.

The canonical expected receipt is:

`receipts/mir-roundtrip-egress-authenticity/current.latest.json`

No such canonical receipt was present when this handoff was reconciled, so new one-way runtime success is not yet claimed.

## Governed-return boundary

The MIR-profile runtime retains the exact response bytes so subsequent return processing consumes the actual runtime consequence rather than a synthesized fixture. Full round-trip completion remains separate and requires authentic StegVerse-side return admission, durable recording, and the final allowed transport-exit transition before `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED` or `communication_complete` can become true.

## Separation-of-powers invariants

- Task Registry: coordination only.
- WorkerCoordinator: current claim/fence authority.
- Interlock/InTr: state-transition/admission authority.
- TV/TVC: credential authority where required.
- MIR: MIR-native semantics.
- Master Records: observed-reality custody/reconstruction only.
- GitHub/GitHub Actions: source validation/evidence transport only; runtime authority `NONE`.
- MIR MIRROR seam/runtime evidence cannot be promoted into authentic external MIR endpoint evidence.

## Counterpart evidence still required

Separately from the owned-mirror transport execution:

- Richard/MIR evidence-custody/reconstruction seam first pass remains pending;
- concrete minimum custody receipts remain pending;
- independently checkable Bitcoin anchor/inclusion evidence remains pending;
- authentic MIR `mir.leaf.v3` independent reproduction remains pending.

## Next action

Reconcile the first authority-owned resident receipt produced by the standing MIR transport request. If the receipt proves the one-way MIR MIRROR transition plus exact Master Records reconstruction, promote only those supported predicates and immediately continue the retained exact return packet through the already-existing governed return-admission/SDK return path. Preserve all unsupported external-MIR and full-round-trip predicates as unverified.
