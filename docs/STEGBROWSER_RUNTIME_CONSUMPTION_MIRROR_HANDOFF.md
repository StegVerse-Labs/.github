# StegBrowser Runtime Consumption Mirror Handoff

Updated: 2026-09-13

## Task pointer

- Goal Task ID: `STEG-BROWSER-RUNTIME-CONSUMPTION-001`
- Parent Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-RUNTIME-CONSUMPTION-001.json`

## Why this successor exists

The parent Goal reached a clean source/component completion point: reusable-component reconciliation, primary TVC source pinning, immutable observer binding, dedicated consumption semantics, and runtime-preflight diagnosis are all merged and validated. The remaining work has independent completion semantics: authentic runtime consumption and admission through `OWNER_INGRESS_READY`.

This successor is therefore not a counter reset and does not create a second execution path. It reuses the existing Canonical Work, WorkerCoordinator, Interlock/InTr, resident dispatcher, exact TVC source-promotion consumer, primary runtime, SKAP ingress, and immutable observer components.

The parent task record is now canonically `SUPERSEDED` with `continuation_task_id=STEG-BROWSER-RUNTIME-CONSUMPTION-001`. Regression tests must therefore fail closed if any path attempts to re-admit or re-project the superseded parent as `PROPOSED`. The historical parent resident request remains source evidence only and does not make the superseded parent ingress-eligible again.

## First unresolved predicate

`TASK_REGISTRY_CHECKIN_CONTINUE_OBSERVED`

The existing Canonical Work wrapper performs the general Task Registry collision check before route mutation and proceeds only on exact `CONTINUE`. `COORDINATE_CONVERGENCE` and `STOP_*` remain fail-closed.

Known convergence owners remain dependencies, not collision resources:

- `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001` owns registry collision/convergence semantics;
- `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001` owns shared retained-runtime evidence convergence.

The successor registration originally also placed those coordination owners in `adjacent_task_refs` and included `StegVerse-Labs/.github` in its runtime target repositories. Because the canonical evaluator treats adjacency and repository overlap as convergence signals, that metadata made exact `CONTINUE` structurally unreachable even after the actual parent collision was repaired. The successor now keeps those owners in `dependencies` while narrowing collision targets to the TVC runtime resources it can actually consume or mutate. This does not bypass either owner or weaken collision protection; it removes coordination metadata that incorrectly masqueraded as a mutable collision surface.

## Existing runtime chain to reuse

```text
Task Registry exact check-in
-> CONTINUE
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

## Required evidence

The runtime path must authentically produce or bind:

```text
receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
receipts/sovereign-host/worker-source-refresh.latest.json
receipts/sovereign-host/resident-refresh-dispatch.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/dispatch-latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/latest.json
/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
```

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

Selected substrate remains `STEG-BROWSER-RETAINED-RESIDENT-NODE`. Current-device and admitted ephemeral StegOS capacity remain valid reuse options. `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT` is not selected, and no second user-operated device is allowed.

## Completion predicate

This Goal is complete only when authentic evidence establishes all of:

1. exact Task Registry check-in returned `CONTINUE` for this successor after any required convergence reconciliation;
2. Canonical Work resident consumption occurred;
3. current WorkerCoordinator claim/fence was observed;
4. Interlock/InTr admission occurred;
5. exact `stegbrowser_tvc_source_promotion` consumption produced a current-dispatch-bound successful staged result;
6. TVC `aef6b6f5dc99d2a531718ca475d20858ae8e68a6` was materially promoted and the same primary runtime restarted;
7. immutable observer `4c78f8653b8a5899350479d57c58e936b50e023a` executed;
8. TVC 8765 and SKAP 8775 were observed simultaneously for the same runtime/recipient binding;
9. `OWNER_INGRESS_READY_OBSERVED` was authentically retained;
10. no parallel scheduler, dispatcher, credential path, or second user-operated device was introduced.

Credential ingress, current-iPhone signing/TestFlight, social publication/readback, and final Master Records custody remain later independent continuation stages and are not silently claimed by this runtime-consumption Goal.

## README disposition

The repository README already documents Canonical Work ingress, autonomous continuation, COSV task-pointer continuation, and the Reusable Task Component Model. This successor narrows ownership of an existing runtime stage and does not change repository-wide architecture; README was re-reviewed and no semantic text change is required.

## Validation regression repair

PR `#1746` correctly superseded `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001` to this successor but left two deterministic test modules asserting that the parent remained `PROPOSED`. The repair updates those tests to assert the canonical `SUPERSEDED` lineage and to require generic bootstrap/projection to reject re-ingress of the parent. This is validation alignment only; it grants no runtime authority and proves no runtime consumption.

## Current state

`ACTIVE / CHECKED_OUT / SOURCE_COMPONENT_PARENT_SUPERSEDED_TO_THIS_SUCCESSOR / SUPERSEDED_PARENT_REINGRESS_PROHIBITED / COLLISION_METADATA_NARROWED_TO_ACTUAL_RUNTIME_TARGETS / AUTHENTIC_RUNTIME_CONSUMPTION_NOT_OBSERVED / TASK_REGISTRY_CONTINUE_NOT_OBSERVED / WORKERCOORDINATOR_CLAIM_FENCE_NOT_OBSERVED / INTR_ADMISSION_NOT_OBSERVED / TVC_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / TVC_PRIMARY_RUNTIME_RESTART_NOT_OBSERVED / IMMUTABLE_OBSERVER_EXECUTION_NOT_OBSERVED / OWNER_INGRESS_READY_NOT_OBSERVED`
