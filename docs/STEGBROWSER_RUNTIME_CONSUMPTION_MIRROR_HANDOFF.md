# StegBrowser Runtime Consumption Mirror Handoff

Updated: 2026-09-13

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONSUMPTION-001`
- Parent Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record shard: `data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json`
- Canonical registry identity source: `data/canonical-task-registry.json`

## Why this successor exists

The parent Goal reached a clean source/component completion point: reusable-component reconciliation, primary TVC source pinning, immutable observer binding, dedicated consumption semantics, and runtime-preflight diagnosis are merged and validated. The remaining work has independent completion semantics: authentic runtime consumption and admission through `OWNER_INGRESS_READY`.

This successor reuses the existing Canonical Work, WorkerCoordinator, Interlock/InTr, resident dispatcher, exact TVC source-promotion consumer, primary runtime, SKAP ingress, and immutable observer components. It does not create a second execution path.

The parent task is canonically `SUPERSEDED` with `continuation_task_id=STEG-BROWSER-RUNTIME-CONSUMPTION-001`. The historical parent request and receipt remain provenance only and cannot satisfy successor ingress or consumption.

## Coordination preflight completed

PR `#1781` merged at `d75ddb18ffb51f3131f3bde54fc9582f57991471` after exact-head deterministic suite `34787453203`, organization-control `34787453261`, and Heartbeat validation `34787453228` all completed successfully.

The regression invokes the existing `scripts/evaluate_task_registry_collision_checkin.py` through the already-admitted `INTERNAL_CANONICAL_WORK_BOOTSTRAP` caller surface for this exact successor and requires:

```text
registry_identity_source = CANONICAL_TASK_REGISTRY
selected_execution_substrate = STEG-BROWSER-RETAINED-RESIDENT-NODE
disposition = CONTINUE
session_action = CONTINUE_CURRENT_TASK
hard_collision_task_ids = []
authority_effect = NONE
```

This closes only `TASK_REGISTRY_CHECKIN_CONTINUE_OBSERVED`. It is coordination evidence, not a runtime transition, WorkerCoordinator claim, Interlock/InTr admission, resident execution, TVC promotion, or owner-ingress observation.

## First unresolved runtime predicate

`CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`

Required successor receipt:

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

Repository search after the merged check-in validation found only the handoff, consumer declaration, and regression references to that path; no successor consumption receipt was present. Therefore resident consumption remains unobserved.

## Existing runtime chain to reuse

```text
Task Registry exact check-in -> CONTINUE   [coordination predicate observed]
-> existing Canonical Work bootstrap
-> authentic Canonical Work resident consumption
-> WorkerCoordinator claim/fence
-> Interlock/InTr admission
-> exact selector stegbrowser_tvc_source_promotion
-> dedicated current-dispatch-bound consumption receipt
-> primary TVC source aef6b6f5dc99d2a531718ca475d20858ae8e68a6 materialization
-> transient promotion
-> same stegtvc-primary-runtime.service restart
-> immutable observer source 4c78f8653b8a5899350479d57c58e936b50e023a
-> simultaneous 127.0.0.1:8765 and 127.0.0.1:8775 observation
-> OWNER_INGRESS_READY_OBSERVED
```

## Successor resident-ingress source already merged

PR `#1763` repaired the canonical resident-ingress pointer from the superseded parent to this successor. The merged source now includes:

```text
control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json
  -> task_id = STEG-BROWSER-RUNTIME-CONSUMPTION-001
  -> COSV = 40000100100000
  -> mode = CANONICAL_WORK_EVENT_BOOTSTRAP
  -> authority_effect = NONE_REQUEST_ONLY
  -> second_machine_required = false

consume-canonical-work-coordination-bootstrap.py
  -> active StegBrowser request targets this successor
  -> successor task shard is preserved/materialized through the existing generic path
  -> superseded parent request is not the active StegBrowser request

install_and_run_canonical_work_event_bootstrap.py
  -> successor participates in the existing StegBrowser/global convergence path
  -> collision preflight remains mandatory
```

PR `#1781` then proved that the current canonical collision preflight returns `CONTINUE` for this successor on current source.

## WorkerCoordinator self-heal source continuity repaired

PR `#1789` merged at `b04d928f039fa185519913fed8343e37319035bd` after exact-head deterministic suite `34791624607`, organization-control `34791624631`, and Heartbeat validation `34791624597` all completed successfully.

The resident carrier already performs local supervision of WorkerCoordinator presence. A concrete source-continuity gap existed in that recovery path: the normal worker service receives `STEGVERSE_HEARTBEAT_SOURCE_ROOT`, but a later carrier-side worker repair could occur after that locator was no longer present in the carrier service environment. The repaired `scripts/run_heartbeat_runtime.py` now restores the non-secret canonical source locator from the native `receipts/sovereign-host/materialization.latest.json` receipt before invoking worker supervision when no explicit locator is already present. An explicitly configured locator remains authoritative.

This repair means a self-healed WorkerCoordinator can retain the local canonical source locator required by the existing local-source refresh path and therefore discover current resident requests after recovery. It does not prove that WorkerCoordinator is presently running, that it has consumed this successor request, or that any later runtime predicate has occurred. HeartBeat remains non-authorizing; no scheduler, dispatcher, credential path, network source transport, connected-device prerequisite, or second user-operated device was introduced.

## Required runtime evidence

The runtime path must authentically produce or bind:

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

The superseded parent's historical consumption receipt remains provenance only; it is not the successor completion receipt.

Source state, CI, heartbeat progression, repository merges, task registration, or this handoff do not prove any runtime predicate.

## Authority and substrate invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: admission/transition authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification/custody path where applicable.
- Master Records: observed-reality/provenance authority.
- HeartBeat: observability/timing/freshness/correlation only.
- GitHub: validation/evidence transport only; runtime authority NONE.

Selected substrate remains `STEG-BROWSER-RETAINED-RESIDENT-NODE`. Current-device, StegBrowser ephemeral lease, same-device Site Safari service worker, and admitted ephemeral StegOS capacity remain declared reusable alternatives where canonical admission permits them. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT` is not selected, no connected-device discovery is a prerequisite, and no second user-operated device is allowed.

The reusable ephemeral construct contract requires applicable admission before runner materialization, preserves Interlock/InTr as transition authority, forbids duplicate scheduler/worker/runtime planes, and requires chained runtime receipts. An ephemeral fallback therefore cannot be declared authentic merely because code can execute in an unrelated container or CI job.

## Completion predicate

This Goal is complete only when authentic evidence establishes all of:

1. exact Task Registry check-in returned `CONTINUE` for this successor after any required convergence reconciliation — **observed and regression-protected**;
2. Canonical Work resident consumption occurred;
3. current WorkerCoordinator claim/fence was observed;
4. Interlock/InTr admission occurred;
5. exact `stegbrowser_tvc_source_promotion` consumption produced a current-dispatch-bound successful staged result;
6. TVC `aef6b6f5dc99d2a531718ca475d20858ae8e68a6` was materially promoted and the same primary runtime restarted;
7. immutable observer `4c78f8653b8a5899350479d57c58e936b50e023a` executed;
8. TVC 8765 and SKAP 8775 were observed simultaneously for the same runtime/recipient binding;
9. `OWNER_INGRESS_READY_OBSERVED` was authentically retained;
10. no parallel scheduler, dispatcher, credential path, connected-device prerequisite, or second user-operated device was introduced.

Credential ingress, current-iPhone signing/TestFlight, social publication/readback, and final Master Records custody remain later independent continuation stages and are not silently claimed by this runtime-consumption Goal.

## README disposition

The repository README already documents Canonical Work ingress, autonomous continuation, COSV task-pointer continuation, the Reusable Task Component Model, and authority separation. The work in this handoff changes task-specific evidence state only; no README semantic change is required.

## Current state

`ACTIVE / CHECKED_OUT / TASK_REGISTRY_CHECKIN_CONTINUE_OBSERVED / SUCCESSOR_RESIDENT_INGRESS_SOURCE_MERGED / WORKER_SELF_HEAL_SOURCE_CONTINUITY_REPAIRED / CANONICAL_WORK_RESIDENT_CONSUMPTION_NOT_OBSERVED / WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED / INTR_ADMISSION_NOT_OBSERVED / TVC_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / TVC_PRIMARY_RUNTIME_RESTART_NOT_OBSERVED / IMMUTABLE_OBSERVER_EXECUTION_NOT_OBSERVED / OWNER_INGRESS_READY_NOT_OBSERVED / NO_CONNECTED_DEVICE_PREREQUISITE / NO_SECOND_USER_OPERATED_DEVICE`
