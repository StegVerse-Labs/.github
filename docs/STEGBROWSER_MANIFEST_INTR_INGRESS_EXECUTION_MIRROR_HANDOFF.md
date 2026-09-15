# StegBrowser Manifest Interlock/InTr Ingress Execution Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`

## Task pointer

- Goal Task ID: `STEG-BROWSER-MANIFEST-INTR-INGRESS-EXECUTION-001`
- Parent Goal: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`
- COSV: `40000100100000`
- Status: `ACTIVE / CHECKED_OUT / SOURCE REPAIR VALIDATED / MERGE PENDING / AUTHENTIC A3+A4 EXECUTION PENDING`

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
-> governed round-trip lifecycle may proceed
```

Forbidden prerequisites:

- waiting for an online device;
- Remote Desktop/device-connectivity checks;
- Render or another hosted carrier;
- GitHub Actions as runtime authority;
- endpoint/receiver discovery;
- second user-operated machine.

## Source repairs

### D1 — stale Canonical Work request identity

Observed source mismatch: `control/resident-execution-request.d/canonical-work-stegbrowser-runtime-consumption-001.json` targets active Goal `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`, while the canonical consumer's StegBrowser request spec retained retired operation-lineage identity `STEG-BROWSER-RUNTIME-CONSUMPTION-001`.

Repair implemented:

- preserve the existing Canonical Work resident consumer and public implementation/API contract;
- overlay only the StegBrowser invocation owner to active `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001`;
- preserve `STEG-BROWSER-RUNTIME-CONSUMPTION-001` as operation lineage and canonical source-contract text;
- preserve/materialize the active remediation task shard without creating a second dispatcher.

### D2 — incorrect A3/A4 ordering in reusable runner

Observed source ordering attempted Canonical Work ingress projection before an authentic WorkerCoordinator claim/fence.

Repair implemented:

- use the already-merged manifest binding first;
- materialize invocation-owned ephemeral StegOS;
- stage one exact StegBrowser packet into `spool/organization-local-boundary/ingress` using existing `stegverse.organization-local-boundary.packet/v1`;
- invoke existing `ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001` through existing `scripts/refresh_and_execute_resident_task.py`;
- accept A3 only from the resulting durable organization-local receipt containing a valid WorkerCoordinator `claim_id` and `fencing_token`;
- accept A4 only after exact packet/profile/hash verification of that receipt;
- only then continue the StegBrowser Canonical Work/transport path.

## Validation evidence

Exact source-validation candidate `b530c27194aaa0d45e889e30fed910e0c8596bdc` passed all three required non-authorizing validation lanes before this handoff reconciliation:

- organization-control run `34926414425`: `success`;
- deterministic repository suite run `34926414434`: `success`;
- Heartbeat validation run `34926414456`: `success`.

Because this handoff/task-record reconciliation changes the branch head, merge requires the same three validation lanes to pass again on the final exact head. No source/CI result is runtime evidence.

## Reuse owner

The required boundary executor already exists:

- `workers/organization_local_resident_boundary_executor.py`
- `control/process-worker-adapters.d/organization-local-resident-boundary-executor-001.json`
- `control/worker-registry.d/organization-local-resident-boundary-executor-001.json`
- `scripts/refresh_and_execute_resident_task.py`

Do not create another runtime, dispatcher, scheduler, WorkerCoordinator, or Interlock/InTr implementation.

The reusable pattern is demonstrated by `workers/stegclaw_p4_profiled_resident_execution.py`: construct exact organization-local ingress packet -> invoke existing boundary task -> verify claim/fence and durable receipt.

## Required predicates

```text
MANIFEST_BOUND_TO_INVOCATION = true
STEGBROWSER_ACTIVE_RESIDENT_REQUEST_DISPATCH_BINDING_VALID = true
INVOCATION_OWNED_EPHEMERAL_STEGOS_MATERIALIZED = true
CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED = true
ORGANIZATION_LOCAL_INTR_INGRESS_RECEIPT_VERIFIED = true
AUTHENTIC_INTR_INGRESS_OBSERVED = true
```

Current predicate ownership:

- Source validation may establish the binding implementation is valid.
- Source/CI/merge MUST NOT establish ephemeral materialization, WorkerCoordinator claim/fence, organization-local ingress receipt verification, or authentic A4 ingress.
- A3/A4 remain pending until invocation-owned durable runtime evidence is observed.

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

Source completion requires corrected request/consumer identity binding, exact organization-local packet construction/verification, deterministic tests, all repository validation lanes PASS on the final exact head, and merge.

Runtime completion for this Goal requires authentic retained evidence from the invocation-owned path proving WorkerCoordinator claim/fence plus verified organization-local Interlock/InTr ingress. Source/CI must not promote those predicates.

## Manual work

None.
