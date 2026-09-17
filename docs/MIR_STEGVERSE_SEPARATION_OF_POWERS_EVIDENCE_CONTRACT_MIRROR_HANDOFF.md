# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED / REFERENCE ARCHITECTURE DRAFT V0.2 / PROVEN SV002 ROUTE REUSED / AUTONOMOUS MIR INVOCATION SOURCE CHAIN VALIDATED / COUNTERPART EVIDENCE-SEAM INPUT PENDING`

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

The transport successor `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001` duplicates that route first and adds only current MIR-specific bindings/evidence. Generic SV002 Node/Interlock/InTr/lease/runtime mechanics may not be inserted as another re-proof gate. The frozen route artifact is prior-event evidence only and grants no present authority.

Canonical route source:

- `StegVerse-Labs/Site/data/mir-roundtrip-egress-sv002-route-binding.v1.json`
- `StegVerse-Labs/Site/docs/MIR_ROUNDTRIP_EGRESS_AUTHENTICITY_MIRROR_HANDOFF.md`

## Current authority-owned execution package

The child transport lane is installed into the existing sovereign WorkerCoordinator/runtime source. Canonical `.github` source contains the MIR task vector/index fragment, worker registry/process adapter, standing resident request, bounded MIR runtime worker, and resident request consumer.

The request is attached to the already-existing `canonical_work_coordination` resident dispatch path through `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`. The wrapper visits the MIR request before its legacy request set and delegates through the existing targeted WorkerCoordinator bridge. No second dispatcher, scheduler, WorkerCoordinator, runtime, transport plane, credential path, resident receiver, or device prerequisite is introduced.

## Autonomous invocation chain reconciled

The existing source authority chain has now been traced end-to-end:

```text
scripts/run_heartbeat_runtime.py --continuous
-> scripts/repair_resident_worker_presence.py#ensure_worker_presence
-> scripts/run_worker_runtime.py --continuous
-> first task-capable WorkerCoordinator cycle
-> scripts/run_worker_runtime.py#dispatch_local_resident_requests
-> scripts/dispatch_resident_execution_requests.py
-> canonical_work_coordination
-> control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py
-> scripts/consume_mir_roundtrip_egress_authenticity_request.py
-> scripts/refresh_and_execute_resident_task.py --task-id MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001
-> existing WorkerCoordinator current claim/fence
-> workers/mir_roundtrip_egress_authenticity_worker.py
-> existing StegOS SovereignLocalEventRuntimeAdapter + run_mir_profile_transition
-> Master Records exact-byte custody/reconstruction
```

The historical self-heal defect in which long tick-zero maintenance could starve the first task-capable WorkerCoordinator tick has already been repaired. Current `run_worker_runtime.py` records the first task-capable cycle before long maintenance and already includes resident dispatch on the existing cadence. Therefore this trace found no remaining source-level autonomous-invocation defect to repair by adding another scheduler, dispatcher, or runtime plane.

Canonical source-trace preflight:

`receipts/preflight/MIR-AUTONOMOUS-INVOCATION-CHAIN-001.json`

## Current runtime observation boundary

Source readiness is not runtime execution proof. At the latest reconciliation:

- no current authentic `runtime-presence.latest.json` was retained in canonical GitHub evidence;
- no current MIR request-consumption receipt was retained in canonical GitHub evidence;
- no `receipts/mir-roundtrip-egress-authenticity/current.latest.json` was retained in canonical GitHub evidence;
- the authorized remote-runtime connector exposed no reachable device/surface during this session.

The remote connector result is only observation-surface reachability evidence; it is not promoted into a claim that no sovereign runtime exists anywhere.

Accordingly the unresolved runtime boundary is explicitly:

`AUTHENTIC_SOVEREIGN_RUNTIME_SURFACE_OR_RUNTIME_RECEIPT_NOT_OBSERVED`

Passive waiting for a receipt to “appear” is not accepted as execution. If an existing authorized sovereign runtime surface executes the already-standing request, only its authentic receipts may promote the MIR runtime predicates. GitHub/GitHub Actions cannot substitute because runtime authority remains `NONE`.

## Runtime proof boundary

One-way MIR MIRROR transport is promoted only if the same current invocation proves current Goal/COSV binding, MIR destination-profile binding, current StegVerse-side egress, current Interlock/InTr transport, MIR MIRROR far-side transition, MIR destination evidence retention, and Master Records reconstruction of the current final exit.

Any successful owned-mirror receipt retains provenance `MIR_MIRROR_BUILD_TEST_COUNTERPART_RUNTIME`; it is not evidence that the authentic external MIR endpoint executed.

## Governed-return boundary

The MIR-profile runtime retains exact response bytes so subsequent return processing consumes the actual runtime consequence rather than a synthesized fixture. Full round-trip completion remains separate and requires authentic StegVerse-side return admission, durable recording, and the final allowed transport-exit transition before `SUCCESSFUL_DATA_TRANSPORT_ROUND_TRIP_IDENTIFIED` or `communication_complete` can become true.

## Separation-of-powers invariants

- Task Registry: coordination only.
- WorkerCoordinator: current claim/fence authority.
- Interlock/InTr: state-transition/admission authority.
- TV/TVC: credential authority where required.
- MIR: MIR-native semantics.
- Master Records: observed-reality custody/reconstruction only.
- GitHub/GitHub Actions: source validation/evidence transport only; runtime authority `NONE`.
- Historical SV002 route evidence grants no present authority.
- MIR MIRROR seam/runtime evidence cannot be promoted into authentic external MIR endpoint evidence.

## Counterpart evidence still required

Separately from the owned-mirror transport execution:

- Richard/MIR evidence-custody/reconstruction seam first pass remains pending;
- concrete minimum custody receipts remain pending;
- independently checkable Bitcoin anchor/inclusion evidence remains pending;
- authentic MIR `mir.leaf.v3` independent reproduction remains pending.

## Next action

Reconcile an authentic resident cadence/request-consumption receipt if one becomes available from an existing authorized sovereign runtime surface. If it proves the one-way MIR MIRROR transition plus exact Master Records reconstruction, promote only those supported predicates and immediately continue the retained exact return packet through the already-existing governed return-admission/SDK return path. Do not create another scheduler, dispatcher, runtime plane, user-device prerequisite, or generic SV002 re-proof gate to work around the explicit runtime-observation boundary.
