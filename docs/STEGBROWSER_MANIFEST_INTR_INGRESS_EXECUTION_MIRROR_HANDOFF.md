# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SOURCE BINDING REPAIR REQUIRED / AUTHENTIC A3+A4 EXECUTION PENDING`

## Goal

Bind the existing StegBrowser manifest-bound resident request into the existing resident dispatcher and existing organization-local Interlock/InTr boundary, then execute the invocation-owned path through ephemeral StegOS materialization, WorkerCoordinator claim/fence, and authentic A4 Interlock/InTr ingress without introducing, discovering, waiting for, or checking any external runtime/device/host.

## Canonical execution invariant

There is no external runtime that connects to this Goal. The invocation itself instantiates the admitted execution surface.

```text
canonical manifest
-> existing StegBrowser resident request
-> existing resident dispatcher
-> existing organization-local Interlock/InTr boundary
-> invocation-bound admitted EVENT_EPHEMERAL StegOS materialization
-> WorkerCoordinator claim/fence
-> authentic organization-local Interlock/InTr ingress receipt
-> A4 satisfied
-> Round Trip #1 may proceed
```

Forbidden prerequisites:

- waiting for an online device;
- Remote Desktop/device-connectivity checks;
- Render or another hosted carrier;
- GitHub Actions as runtime authority;
- endpoint/receiver discovery;
- second user-operated machine.

## Exact source defects observed at task creation

### D1 — stale Canonical Work request identity

`control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json` correctly targets active Goal `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`, but `control/resident-execution-request.d/consume-canonical-work-coordination-bootstrap.py` still declares the StegBrowser request spec task ID as retired `STEG-BROWSER-RUNTIME-CONSUMPTION-001`.

Required repair:

- bind the StegBrowser spec to the active invocation Goal identity;
- preserve `STEG-BROWSER-RUNTIME-CONSUMPTION-001` only as operation lineage;
- materialize/preserve the active task shard, not rely on retired identity as the execution owner.

### D2 — incorrect A3/A4 ordering in reusable runner

`scripts/run_stegbrowser_runtime_consumption_reusable.py` currently attempts its Canonical Work ingress projection before observing a real WorkerCoordinator claim/fence, and its projection gate references stale `INGRESS_ADMITTED` semantics not present in the current Goal transition set.

Required repair:

- use the already-merged manifest binding first;
- materialize invocation-owned ephemeral StegOS;
- stage one exact StegBrowser packet into `spool/organization-local-boundary/ingress` using existing `stegverse.organization-local-boundary.packet/v1`;
- invoke existing `ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001` through existing `scripts/refresh_and_execute_resident_task.py`;
- accept A3 only from the resulting durable organization-local receipt containing a valid WorkerCoordinator `claim_id` and `fencing_token`;
- accept A4 only after exact packet/profile/hash verification of that receipt;
- only then continue the StegBrowser Canonical Work/transport path.

## Reuse owner

The required boundary executor already exists:

- `workers/organization_local_resident_boundary_executor.py`
- `control/process-worker-adapters.d/organization-local-resident-boundary-executor-001.json`
- `control/worker-registry.d/organization-local-resident-boundary-executor-001.json`
- `scripts/refresh_and_execute_resident_task.py`

Do not create another runtime, dispatcher, scheduler, WorkerCoordinator, or Interlock/InTr implementation.

The known reusable pattern is demonstrated by `workers/stegclaw_p4_profiled_resident_execution.py`: construct exact organization-local ingress packet -> invoke existing boundary task -> verify claim/fence and durable receipt.

## Required predicates

```text
MANIFEST_BOUND_TO_INVOCATION = true
STEGBROWSER_ACTIVE_RESIDENT_REQUEST_DISPATCH_BINDING_VALID = true
INVOCATION_OWNED_EPHEMERAL_STEGOS_MATERIALIZED = true
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = true
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = true
AUTHENTIC_INTR_INGRESS_OBSERVED = true
```

A4 is not satisfied by source, CI, request existence, dispatcher selection, or an ingress packet alone.

## Authority boundaries

- Manifest: route declaration/binding only.
- Resident request/dispatcher: non-authorizing invocation transport.
- EVENT_EPHEMERAL StegOS materialization: compute surface only; authority effect `NONE`.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: transition and governed packet-movement authority.
- Organization-local boundary executor: bounded execution surface; does not mint transition authority.
- TV/TVC: credential authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Completion boundary

Source completion requires corrected request/consumer identity binding, exact organization-local packet construction/verification, deterministic tests, all repository validation lanes PASS, and merge.

Runtime completion for this Goal requires authentic retained evidence from the invocation-owned path proving WorkerCoordinator claim/fence plus verified organization-local Interlock/InTr ingress. Source/CI must not promote those predicates.

## Manual work

None.
