# GADI Resident Execution Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `SOURCE_CONTRACTS_RECONCILED / WORKERCOORDINATOR_REGISTRATION_REPAIR_MERGED / WORKER_PROTOCOL_BRIDGE_MERGED / NONCLAIM_READINESS_CONVERGENCE_REPAIR_IN_VALIDATION / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and is not superseded.

Merged trajectory includes runtime-evidence materialization, local source resolution, native StegOS command compatibility, canonical InTr admission compatibility, WorkerCoordinator claim/fence compatibility, governed actuator-observation projection, the StegOS controlled-output receipt seam, parent source-chain reconciliation, targeted WorkerCoordinator registration repair, and the post-claim worker protocol bridge.

PR #1388 repaired targeted WorkerCoordinator registration and merged as `261b1636db05baa3d34072236557618e9607b5e7` after repaired exact head `d2d361327a6a48a1d9afc1109f6506b23fce82eb` passed organization-control, deterministic repository-suite diagnostics, and Heartbeat validation.

PR #1395 repaired the post-claim ProcessWorkerAdapter/GADI dispatcher protocol gap. Exact head `cc5df51b4663417d2b910a3cbebf94d5647c8d08` passed organization-control run `34559259086`, deterministic repository-suite run `34559259115`, and Heartbeat run `34559259028`, then squash-merged as `b1b613452406b26d8fe17a9fbb98b57054a4f046`.

PR #1396 reconciled that merged bridge into the canonical handoff. Exact head `3174f8ecd53a4e988e6531ebdcd877f5e5bf160a` passed all three canonical validations and squash-merged as `b4b6e467d057b476e1e12fae75097d2b39b3c7e0`.

The canonical runtime evidence state still remains `HANDOFF_READY` with no authentic current claim/fence, InTr admission, runtime binding, controlled actuator result, or resident-consumption receipt observed.

## Canonical execution chain

```text
NON-CLAIM LOCAL SOURCE READINESS
-> TARGETED WORKERCOORDINATOR CLAIM/FENCE
-> SOURCE RESOLUTION WITH WORKER CLAIM DEFERRED
-> FRESH WORKERCOORDINATOR CLAIM PROJECTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
```

The four runtime source classes remain independently owned by StegOS command materialization, canonical InTr admission, WorkerCoordinator claim/fence assignment, and the controlled pre-authorized actuator observation plane.

## Non-claim readiness / convergence audit — repair in validation

Inspection of the merged bridge against the global runtime-evidence convergence runner found two remaining architectural collisions.

### 1. Locator circularity

When `state/gadi-resident-execution/source-locators.json` exists, the source resolver previously required all four locators, including `worker_claim`, before WorkerCoordinator had created the fresh claim. That recreated the claim circularity even though the post-claim dispatcher was ready to inject the live row.

`scripts/resolve_gadi_resident_runtime_sources.py` now supports `--defer-worker-claim`. In that mode it resolves only:

- `stegos_command`;
- `intr_admission`;
- `actuator_observation`.

It neither requires nor copies a worker-claim locator. The post-claim dispatcher stages the exact current WorkerCoordinator row immediately afterward. This avoids both a missing-locator deadlock and stale pre-claim claim bytes.

`dispatch_gadi_resident_execution.dispatch()` automatically uses this deferred mode whenever `current_worker_claim` is supplied by the merged process-worker bridge.

### 2. Global convergence bypassed WorkerCoordinator

`run_global_runtime_evidence_convergence.py` classifies GADI as an existing task-specific wrapper and invokes the dispatcher CLI directly. After the corrected claim model, a claimless direct dispatcher invocation may not satisfy the GADI bundle because WorkerCoordinator is the sole claim/fence authority.

Rather than adding a second dispatcher or synthetic claim, the claimless `dispatch_gadi_resident_execution.py` CLI now delegates to:

`scripts/run_gadi_targeted_runtime_if_ready.py`

The Python `dispatch()` function remains the post-claim path called by `workers/gadi_resident_execution_worker.py` with the authentic current task row.

## Readiness-gated targeted entry

`run_gadi_targeted_runtime_if_ready.py` is non-authorizing until the canonical targeted WorkerCoordinator is invoked.

It first runs local source resolution with worker claim deferred and validates the current three non-claim source classes for:

- native command ready state;
- observed InTr admission;
- exact `intr_decision_ref`;
- non-empty runtime binding;
- control-surface and target-class bindings;
- controlled pre-authorized actuator observation;
- no credential exposure;
- matching command/InTr/actuator bindings;
- existing separated carrier reference.

If any predicate is missing, it returns `NONCLAIM_RUNTIME_EVIDENCE_PENDING` and does not invoke WorkerCoordinator.

Only when those inputs are coherent does it invoke:

```text
python scripts/run_worker_runtime.py --root <runtime> --task-id GADI-RESIDENT-EXECUTION-001
```

That existing targeted runtime remains the sole creator of the fresh claim/fence.

## Stale-consumption replay protection

The readiness wrapper records the SHA-256 of any pre-existing `gadi-resident-execution-consumption.latest.json` before targeted invocation and compares it afterward. A prior unchanged `AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED` receipt cannot satisfy the new visit.

Success requires a newly created or changed receipt from this invocation whose state is exactly `AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED`.

Otherwise the wrapper reports `TARGETED_WORKER_RUNTIME_VISITED_NO_NEW_CONSUMPTION`.

## Regression coverage

`tests/test_gadi_runtime_source_resolution.py` now verifies that a locator manifest may omit `worker_claim` only when explicit fresh-claim deferral is enabled, while the three non-claim sources are still exact-local resolved.

`tests/test_gadi_targeted_runtime_readiness.py` verifies:

- missing non-claim sources never trigger targeted execution;
- an unchanged old consumption receipt cannot satisfy a new visit;
- a changed authentic-consumption receipt may satisfy the visit;
- the wrapper does not claim to create the WorkerCoordinator claim;
- the claimless dispatcher CLI is readiness-gated and uses deferred worker-claim source resolution.

## Universal InTr observation

The shared profiled Universal InTr ingress currently exposes explicit purpose-specific materialization paths for HIL, SV002, DEVICE_KV, KV/SKAP, Publisher and related lanes. Inspection did not surface a dedicated GADI profiled ingress/destination in that shared ingress implementation.

The global convergence matrix instead identifies GADI as using its existing preflight-gated wrapper with the next evidence stage being real preflight + claim/fence + InTr + controlled execution evidence. Therefore this repair does not invent a new GADI InTr authority or endpoint. It only ensures that any current GADI command/InTr/controlled-output evidence already materialized locally is evaluated before the existing targeted WorkerCoordinator is visited.

A dedicated GADI InTr ingress should be added only if subsequent runtime inspection proves that no existing canonical InTr producer can materialize the required current admission artifact.

## Authentic evidence boundary

Merged source, CI, registration repair, protocol bridging, readiness evaluation, capability eligibility, simulation, and request records are not authentic resident execution evidence.

Current authentic conditions remain unobserved until produced by their authority planes:

```text
CURRENT_GADI_INTR_ADMISSION_NOT_OBSERVED
CURRENT_GADI_WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED
CURRENT_GADI_RUNTIME_BINDING_NOT_OBSERVED
CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT_NOT_OBSERVED
```

A future WorkerCoordinator claim is valid only when created by the actual targeted runtime invocation. It must not be fabricated or retained merely because the source path is structurally complete.

## Remaining authentic completion predicates

1. Validate and merge the non-claim readiness/convergence repair.
2. Produce or locate an authentic current native StegOS GADI command.
3. Produce or locate the exact current canonical InTr admission carrying the matching `intr_decision_ref` and runtime-binding context.
4. Produce the controlled pre-authorized software test-surface effect and governed output receipt through the merged StegOS seam.
5. Materialize those non-claim runtime sources locally.
6. Allow the readiness gate to invoke the existing targeted WorkerCoordinator; it alone creates the fresh claim/fence.
7. Require zero-blocker materialization/preflight before resident consumption.
8. Independently inspect the newly changed subject-bound resident receipt.
9. Complete closed-loop reassessment/adaptation/termination evidence.
10. Pass the authentic receipt chain to Continuity/Master Records and prove exact reconstruction.
11. Reconcile parent `GADI-001` and the umbrella manifold only from authentic observations.

## Immediate continuation

After this repair validates and merges, inspect current runtime-local source evidence and the canonical InTr producer path that would create the GADI admission artifact. If no current non-claim evidence is observed, keep GADI unclaimed and identify the exact missing producer rather than firing a targeted WorkerCoordinator claim against source-only state.

## Collision boundary

No second heartbeat, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

`README.md` was reviewed. Existing top-level documentation already defines WorkerCoordinator authority separation, targeted independent execution, local-only source refresh, runtime convergence, and non-authorizing heartbeat semantics. This repair aligns GADI with those existing surfaces and adds no new user-facing interface; no root README mutation is required.

## Release rule

This readiness/convergence repair is not a GADI release or activation. Release/tag propagation remains deferred until authentic resident runtime execution, closed-loop evidence, exact reconstruction, and canonical activation predicates are satisfied.
