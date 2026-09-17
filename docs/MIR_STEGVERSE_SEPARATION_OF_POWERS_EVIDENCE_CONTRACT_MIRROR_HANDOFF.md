# MIR / StegVerse separation-of-powers evidence contract mirror handoff

Updated: 2026-09-16
Goal Task ID: `MIR-STEGVERSE-SEPARATION-OF-POWERS-EVIDENCE-CONTRACT-001`
COSV ID: `50000000100000`
Status: `ACTIVE / V0.3 FREEZE ACCEPTED / REFERENCE ARCHITECTURE DRAFT V0.2 / PROVEN SV002 ROUTE REUSED / MIR REQUEST WIRED INTO EXISTING RESIDENT CADENCE / COUNTERPART EVIDENCE-SEAM INPUT PENDING`

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

The child transport lane is installed into the existing sovereign WorkerCoordinator/runtime source. Canonical `.github` source contains:

- `control/task-vectors/MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001.json`
- `control/task-vector-index.d/MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001.json`
- `control/worker-registry.d/mir-roundtrip-egress-authenticity-001.json`
- `control/process-worker-adapters.d/mir-roundtrip-egress-authenticity-001.json`
- `control/resident-execution-request.d/mir-roundtrip-egress-authenticity-001.json`
- `workers/mir_roundtrip_egress_authenticity_worker.py`
- `scripts/consume_mir_roundtrip_egress_authenticity_request.py`

The request is now attached to the already-existing `canonical_work_coordination` resident dispatch cadence through `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py`. The wrapper visits the MIR request before its legacy request set, then continues ordinary canonical-work processing even if the MIR attempt fails closed. This adds no dispatcher, scheduler, WorkerCoordinator, runtime, transport plane, credential path, resident receiver, or device prerequisite.

The bounded MIR consumer calls the existing `scripts/refresh_and_execute_resident_task.py --task-id MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`. Current Goal/COSV binding is enforced by the standing request and runtime worker directly; the event is not blocked on a separate aggregate-index refresh before execution. The runtime manifest still carries the exact current Goal and COSV `50000000100000`.

The worker hashes and binds the frozen successful SV002 route artifact, records that it grants no present authority, requires a fresh current WorkerCoordinator claim/fence, binds `destination_profile=MIR`, and executes the existing StegOS `SovereignLocalEventRuntimeAdapter` + `run_mir_profile_transition` sequence:

```text
RTC-STEGVERSE-EGRESS-007
-> RTC-INTERLOCK-INTR-TRANSPORT-008
-> RTC-FARSIDE-FINAL-009
```

It retains the exact MIR MIRROR response, requires the external-ingress receipt and linked current Interlock/InTr evidence, then delegates current-event custody/reconstruction to the existing `workers/reusable_task_master_records_roundtrip.py`, which requires destination-owned Master Records ingest/reconstruction and exact-byte equality.

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

Any successful owned-mirror receipt retains provenance `MIR_MIRROR_BUILD_TEST_COUNTERPART_RUNTIME`; it is not evidence that the authentic external MIR endpoint executed.

Expected current receipt:

`receipts/mir-roundtrip-egress-authenticity/current.latest.json`

No canonical receipt at that path was present at the latest reconciliation, so one-way runtime success is not yet claimed.

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

Reconcile the first authority-owned resident receipt produced by the now-wired MIR request. If it proves the one-way MIR MIRROR transition plus exact Master Records reconstruction, promote only those supported predicates and immediately continue the retained exact return packet through the already-existing governed return-admission/SDK return path. Preserve all unsupported external-MIR and full-round-trip predicates as unverified.
