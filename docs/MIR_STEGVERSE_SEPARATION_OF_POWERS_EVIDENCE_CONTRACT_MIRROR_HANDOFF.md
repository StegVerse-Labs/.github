# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-17
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED / REFERENCE ARCHITECTURE DRAFT V0.2 / PROVEN SV002 ROUTE REUSED / AUTONOMOUS MIR INVOCATION SOURCE CHAIN VALIDATED / EVENT-DRIVEN RUNTIME MODEL RECONCILED / COUNTERPART EVIDENCE-SEAM INPUT PENDING`

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

## Event-driven runtime correction

The MIR `EVENT_EPHEMERAL` runtime is not an idle service that must already exist or be remotely reachable before execution. Resident supervision and WorkerCoordinator may be durable support surfaces, but the actual event runtime is instantiated as a consequence of the admitted state transition.

Therefore the earlier remote-surface reachability framing was incorrect. A failed remote-device/surface lookup says nothing authoritative about whether the current MIR event can materialize its runtime through the existing transition path. The authoritative question is whether the current MIR-bound event enters the existing ingress and receives the required current Interlock/InTr state transition.

The superseded unresolved boundary was:

`AUTHENTIC_SOVEREIGN_RUNTIME_SURFACE_OR_RUNTIME_RECEIPT_NOT_OBSERVED`

The corrected unresolved boundary is:

`AUTHENTIC_MIR_EVENT_INGRESS_OR_STATE_TRANSITION_RECEIPT_NOT_OBSERVED`

Remote-device or remote-surface reachability is explicitly **not** a runtime predicate for this lane.

## Current authority-owned execution package

The child transport lane is installed into the existing sovereign WorkerCoordinator/runtime source. Canonical `.github` source contains the MIR task vector/index fragment, worker registry/process adapter, standing resident request, bounded MIR runtime worker, and resident request consumer.

The request is attached to the existing `canonical_work_coordination` path through `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`. No second dispatcher, scheduler, WorkerCoordinator, runtime, transport plane, credential path, resident receiver, or device prerequisite is introduced.

The exact existing source chain remains:

```text
scripts/run_heartbeat_runtime.py --continuous
-> scripts/repair_resident_worker_presence.py#ensure_worker_presence
-> scripts/run_worker_runtime.py --continuous
-> first task-capable WorkerCoordinator cycle
-> scripts/run_worker_runtime.py#dispatch_local_resident_requests
-> scripts/dispatch_resident_execution_requests.py
-> canonical_work_coordination
-> consume-canonical-work-coordination-bootstrap.py
-> consume_mir_roundtrip_egress_authenticity_request.py
-> refresh_and_execute_resident_task.py --task-id MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001
-> current WorkerCoordinator claim/fence
-> current MIR event admitted into Interlock/InTr
-> EVENT_EPHEMERAL MIR runtime materializes
-> RTC-STEGVERSE-EGRESS-007
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> RTC-FARSIDE-FINAL-009
-> Master Records exact-byte custody/reconstruction
```

Canonical source-trace preflight is `receipts/preflight/MIR-AUTONOMOUS-INVOCATION-CHAIN-001.json`, now corrected to the transition-dependent runtime model.

## Current runtime observation boundary

Source readiness is not current-event execution proof. At the latest reconciliation, no authentic current MIR event-ingress receipt, current Interlock/InTr transition receipt, MIR request-consumption receipt, or `receipts/mir-roundtrip-egress-authenticity/current.latest.json` is retained in canonical evidence.

Passive waiting for a runtime surface or receipt to appear is not accepted as execution. The correct action is to cause or observe the current MIR event entering the existing authorized ingress/transition path. If admitted, the event runtime materializes as a consequence of that state transition.

GitHub/GitHub Actions cannot substitute because runtime authority remains `NONE`.

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
- Remote-device/surface reachability grants no runtime proof and is not a runtime prerequisite.
- MIR MIRROR seam/runtime evidence cannot be promoted into authentic external MIR endpoint evidence.

## Counterpart evidence still required

Separately from the owned-mirror transport execution:

- Richard/MIR evidence-custody/reconstruction seam first pass remains pending;
- concrete minimum custody receipts remain pending;
- independently checkable Bitcoin anchor/inclusion evidence remains pending;
- authentic MIR `mir.leaf.v3` independent reproduction remains pending.

## Next action

Cause or observe the current MIR-bound event entering the existing authorized ingress/Interlock/InTr path. Treat the `EVENT_EPHEMERAL` runtime as transition-materialized, not as an idle remotely reachable surface. Reconcile only authentic event-ingress, transition, MIR destination, and Master Records receipts; do not create another scheduler, dispatcher, runtime plane, user-device prerequisite, remote-surface gate, or generic SV002 re-proof.
