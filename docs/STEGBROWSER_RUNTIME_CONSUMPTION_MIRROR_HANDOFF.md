# StegBrowser Runtime Consumption Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONSUMPTION-001`
- Parent Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record shard: `data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json`
- Canonical registry identity source: `data/canonical-task-registry.json`

## Canonical state

The parent task is `SUPERSEDED`; this successor remains `ACTIVE / CHECKED_OUT`. The selected execution substrate is `ADMITTED-EPHEMERAL-STEGOS-NODE`. StegOS devices/nodes are interchangeable execution/transport nodes, not user-verification authority. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT` is `NOT_APPLICABLE`; no connected-device discovery and no second user-operated device are prerequisites.

Task Registry check-in `CONTINUE` is already observed and regression-protected. That evidence is coordination-only and does not prove resident execution, WorkerCoordinator claim/fence, Interlock/InTr admission, TVC promotion, observer execution, or owner-ingress readiness.

## Source continuity already merged

The existing resident path is reused rather than duplicated:

```text
Task Registry exact check-in -> CONTINUE
-> existing Canonical Work bootstrap
-> applicable Interlock/InTr admission for ADMITTED-EPHEMERAL-STEGOS-NODE
-> ephemeral StegOS runner materialization
-> authentic Canonical Work resident consumption
-> WorkerCoordinator claim/fence
-> exact selector stegbrowser_tvc_source_promotion
-> current-dispatch-bound consumption receipt
-> primary TVC source aef6b6f5dc99d2a531718ca475d20858ae8e68a6 materialization
-> transient promotion
-> same stegtvc-primary-runtime.service restart
-> immutable observer source 4c78f8653b8a5899350479d57c58e936b50e023a
-> simultaneous 127.0.0.1:8765 and 127.0.0.1:8775 observation
-> OWNER_INGRESS_READY_OBSERVED
```

Existing merged source includes the successor resident request, the generalized Canonical Work consumer, collision preflight, global convergence participation, and WorkerCoordinator self-heal source-root continuity. Source/CI/merge state remains non-authorizing.

## Substrate conformance reconciliation

`.github` PR `#1817` repaired an inconsistency introduced while selecting ephemeral StegOS. The task record now preserves the canonical single-device-first `review_order` while keeping `ADMITTED-EPHEMERAL-STEGOS-NODE` as the sole selected substrate. The same PR repaired `scripts/validate_task_registration_substrate_resolution.py` so pull-request validation covers modified canonical task records (`--diff-filter=AM`), not only newly added task records.

Exact head `c87f731a89bcc5b5edc186304cf787e6ab38219e` passed:

```text
Validate organization control plane: 34853498266 SUCCESS
Deterministic Repository Suite: 34853498305 SUCCESS
Heartbeat Worker Project: 34853498284 SUCCESS
```

PR `#1817` squash-merged as `e755c433f685e311273125981a9c383b76a18260`.

This closes only task-record substrate conformance and modified-record validation coverage. It does not establish any runtime predicate.

## First unresolved runtime predicate

`CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`

Required successor receipt:

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

A fresh repository search after `#1817` found only the handoff, request consumer declaration, canonical task dependency, and regression references for that path; no authentic successor consumption receipt was observed. A fresh search of `master-records/orchestration` for `STEG-BROWSER-RUNTIME-CONSUMPTION-001` returned no retained Master Records entry. Therefore the task must remain active and uncompleted.

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

The superseded parent's historical receipt is provenance only and cannot satisfy the successor. Source state, CI, heartbeat progression, repository merges, or task registration do not prove runtime completion.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed admission/state-transition authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification/custody authority where applicable.
- StegOS devices/nodes: interchangeable execution/transport nodes only.
- Master Records: observed-reality/provenance authority.
- HeartBeat: observability/timing/freshness/correlation only.
- GitHub/source/CI: runtime authority `NONE`.

The reusable ephemeral contract remains fail-closed: applicable admission precedes runner materialization, exact task/COSV binding must be preserved, duplicate scheduler/worker/runtime planes are prohibited, and chained runtime receipts are required.

## Completion predicate

Complete only when authentic evidence establishes all of:

1. Task Registry check-in `CONTINUE` — observed;
2. Canonical Work resident consumption on an admitted interchangeable StegOS/StegBrowser node class;
3. current WorkerCoordinator claim/fence;
4. Interlock/InTr admission;
5. exact `stegbrowser_tvc_source_promotion` current-dispatch-bound successful consumption;
6. pinned TVC source materialization and same primary-runtime restart;
7. immutable observer execution;
8. simultaneous TVC 8765 and SKAP 8775 observation for the same runtime/recipient binding;
9. `OWNER_INGRESS_READY_OBSERVED` retained;
10. no parallel scheduler, dispatcher, credential path, connected-device prerequisite, or second user-operated device.

Credential ingress, current-iPhone signing/TestFlight, social publication/readback, and later custody stages remain independent continuations and are not silently claimed here.

## README disposition

No README semantic change is required. Existing repository documentation already covers Canonical Work ingress, autonomous continuation, COSV continuation, reusable-task composition, and authority separation.

## Current state

`ACTIVE / CHECKED_OUT / TASK_REGISTRY_CHECKIN_CONTINUE_OBSERVED / EPHEMERAL_STEGOS_SELECTED / CANONICAL_SUBSTRATE_REVIEW_ORDER_RESTORED / MODIFIED_TASK_RECORD_VALIDATION_ENFORCED / SUCCESSOR_RESIDENT_INGRESS_SOURCE_MERGED / WORKER_SELF_HEAL_SOURCE_CONTINUITY_REPAIRED / CANONICAL_WORK_RESIDENT_CONSUMPTION_NOT_OBSERVED / MASTER_RECORDS_SUCCESSOR_CUSTODY_NOT_OBSERVED / WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED / INTR_ADMISSION_NOT_OBSERVED / TVC_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / TVC_PRIMARY_RUNTIME_RESTART_NOT_OBSERVED / IMMUTABLE_OBSERVER_EXECUTION_NOT_OBSERVED / OWNER_INGRESS_READY_NOT_OBSERVED / REMOTE_DEVICE_NOT_REQUIRED / NO_CONNECTED_DEVICE_PREREQUISITE / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None. The next unresolved step is authentic resident consumption on the already-selected admitted ephemeral StegOS path; do not repeat source/bootstrap work unless new evidence shows a source defect.
