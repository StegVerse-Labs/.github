# StegBrowser Runtime Consumption Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONSUMPTION-001`
- Parent Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical task record: `data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json`
- Canonical registry identity source: `data/canonical-task-registry.json`

## Canonical state

`ACTIVE / CHECKED_OUT`.

Selected execution substrate is `ADMITTED-EPHEMERAL-STEGOS-NODE`. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT` remains `NOT_APPLICABLE`; no external device and no second user-operated device are prerequisites. StegOS nodes are interchangeable execution/transport surfaces only; KV/SKAP Vault remains user-verification/custody authority.

Task Registry check-in `CONTINUE` is already observed and regression-protected. It is coordination evidence only.

## Existing runtime chain to reuse

```text
Task Registry CONTINUE
-> reusable trigger RT-STEGBROWSER-RUNTIME-CONSUMPTION-001
-> existing SovereignLocalEventRuntimeAdapter
-> admitted EVENT_EPHEMERAL StegOS carrier/worker materialization
-> existing Canonical Work resident consumer
-> Interlock/InTr ingress/admission
-> WorkerCoordinator claim/fence
-> authentic Canonical Work resident consumption
-> exact stegbrowser_tvc_source_promotion consumption
-> pinned TVC aef6b6f5dc99d2a531718ca475d20858ae8e68a6 materialization/restart
-> immutable observer 4c78f8653b8a5899350479d57c58e936b50e023a
-> simultaneous 127.0.0.1:8765 and 127.0.0.1:8775 observation
-> OWNER_INGRESS_READY_OBSERVED
-> Master Records custody/reconstruction
```

No second runtime plane, scheduler, WorkerCoordinator, credential path, device identity, or provider authority may be introduced.

## Reusable ephemeral runner binding merged

`.github` PR `#1831` merged as `6f1b08ee786c8f72395cfa5d393397bcdb7404c5` after exact head `d806711eadba0325fbf300b89b6fc8e216b8d566` passed:

```text
Validate organization control plane: 34862161235 SUCCESS
Deterministic Repository Suite: 34862161192 SUCCESS
Heartbeat Worker Project: 34862161135 SUCCESS
```

The merge adds:

```text
source-bundles/reusable-task-registry.d/RT-STEGBROWSER-RUNTIME-CONSUMPTION-001.json
scripts/run_stegbrowser_runtime_consumption_reusable.py
tests/test_stegbrowser_runtime_consumption_reusable_binding.py
```

and binds the existing resident request to that reusable identity without changing its `CANONICAL_WORK_EVENT_BOOTSTRAP` semantics.

The runner reuses `SovereignLocalEventRuntimeAdapter`, requires `ADMITTED-EPHEMERAL-STEGOS-NODE`, materializes the existing sovereign carrier/worker runtime, invokes the existing `consume-canonical-work-coordination-bootstrap.py`, and fails closed unless authentic successor consumption/TVC/observer receipts are present. Standard reusable-task completion output is emitted only when the full declared runtime evidence chain is observed.

This closes the prior source-level executable-runner binding gap. It does **not** itself prove runtime execution.

## Existing source continuity

Prior merged source remains applicable:

- `.github#1763`: successor resident-ingress pointer and Canonical Work request path.
- `.github#1781`: exact Task Registry `CONTINUE` preflight.
- `.github#1789`: WorkerCoordinator self-heal source-root continuity.
- `.github#1817`: canonical substrate review-order and modified-record validation repair.
- `StegOS#380`: current-iPhone processing-observer source continuity.
- `Site#1305`: same-device root Universal InTr/CanonicalWork ingress capability.

None of these source/CI merges substitute for authentic runtime receipts.

## First unresolved runtime predicate

`CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`

Required authentic successor receipt:

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

The reusable binding now provides a machine-executable path to attempt this predicate on the selected ephemeral StegOS substrate. Until that runner is actually invoked on an eligible sovereign runtime and the receipt is observed, the Goal remains active.

## Required runtime evidence

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
receipts/sovereign-host/worker-source-refresh.latest.json
receipts/sovereign-host/resident-refresh-dispatch.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/dispatch-latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/latest.json
/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
```

Historical parent receipts are provenance only and cannot satisfy this successor.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed admission/state-transition authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification/custody authority where applicable.
- Master Records: observed-reality/provenance authority.
- HeartBeat: timing/freshness/observability only.
- GitHub/source/CI: runtime authority `NONE`.

The reusable automation contract remains `TRIGGER_ONCE_ADVANCE_UNTIL_COMPLETION_OR_REAL_BOUNDARY`; manual coordination between machine-admissible internal steps is not required.

## Completion predicate

Complete only when authentic evidence establishes all of:

1. Task Registry `CONTINUE` — observed;
2. Canonical Work resident consumption;
3. current WorkerCoordinator claim/fence;
4. Interlock/InTr admission;
5. current-dispatch-bound `stegbrowser_tvc_source_promotion` successful consumption;
6. pinned TVC source materialized and the same primary runtime restarted;
7. immutable observer executed;
8. simultaneous TVC 8765 and SKAP 8775 observation for the same runtime/recipient binding;
9. `OWNER_INGRESS_READY_OBSERVED` retained;
10. no parallel scheduler/dispatcher/credential path or second user-operated device.

## Current state

`ACTIVE / CHECKED_OUT / TASK_REGISTRY_CHECKIN_CONTINUE_OBSERVED / EPHEMERAL_STEGOS_SELECTED / REUSABLE_EPHEMERAL_RUNNER_BINDING_MERGED / CANONICAL_WORK_RESIDENT_CONSUMPTION_NOT_OBSERVED / WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED / INTR_ADMISSION_NOT_OBSERVED / TVC_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / TVC_PRIMARY_RUNTIME_RESTART_NOT_OBSERVED / IMMUTABLE_OBSERVER_EXECUTION_NOT_OBSERVED / OWNER_INGRESS_READY_NOT_OBSERVED / REMOTE_DEVICE_NOT_REQUIRED / NO_CONNECTED_DEVICE_PREREQUISITE / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None for source/runtime binding. The next required action is machine execution of the merged reusable runner on an eligible sovereign resident execution surface; absence of a Remote Desktop connection is not itself a Goal blocker.
