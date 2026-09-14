# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / RUNTIME PROFILE RESOLUTION CURRENT / ROUTING READY / TARGETED WORKERCOORDINATOR BRIDGE STAGED / AUTHENTIC RUNTIME PROOF PENDING`

## Canonical state

- Current Task Registry state: `ACTIVE / UNCLAIMED`.
- Predecessor `STEGAGENTS-GOVERNED-AGENT-REGISTRATION-001` remains `RETIRED / COMPLETED`; it is not reopened.
- `CodeRepair-001` remains `REGISTERED_GOVERNED_PROPOSAL_ONLY`.
- exact governed-manifest source merge: `b768eeeb0ceca14fcfd50ce665cd6c0885e2774f`.
- exact governed-manifest Git blob: `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`.
- StegAgents governed runtime/reconstruction bridge merge: `b4115293803fd1d3beaf0335baf4308b6e13052e`.
- runtime task registration: `.github` PR `#1827`, merge `a06d9d3b8c564f267c2a9b9ffcd9826a798dc168`.
- Canonical Work resident request/stale-registry remediation: `.github` PR `#1829`, merge `2fadbb9cde25557ccbcbb6ace49ef5301fba9441`.
- WorkerCoordinator process-adapter binding: `.github` PR `#1830`, merge `e3fe9aa090acd46b9f82111299144c4092fee192`.
- Runtime-profile/routing-order correction: `.github` PR `#1836`, merge `de0ad40f03e588dbf81de34b9fb6f63606987e21`.

## Runtime-profile resolution and routing readiness

Task Registry policy requires runtime requirements to resolve against the Canonical Runtime Profile Map before WorkerCoordinator admission review. The corrected requirements are:

```text
capabilities:
- task_registry_reconciliation
- worker_claim_projection
- intr_task_admission
- canonical_artifact_validation
- master_records_reconciliation
environment: SOVEREIGN_RESIDENT
direction: INTERNAL
mutation_required: true
deployment_required: false
current_observation_required: false
```

Against `control/runtime-profile-map.json` generation `2`, these resolve to exactly one routing profile:

```text
canonical-work-coordination-runtime-v1
```

The persisted runtime resolution is projection-only and grants no authority. Current routing disposition is:

```text
ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW
```

## Targeted WorkerCoordinator execution bridge

Inspection after routing readiness found a source integration gap: the existing Canonical Work request can carry task ingress/materialization, but its registry-first cycle selects `PROPOSED` ingress candidates and does not invoke `run_worker_runtime.py` for this already-`ACTIVE` task. The task therefore had no resident bridge from routing readiness to the existing WorkerCoordinator admission review.

The remediation reuses the established targeted independent-task-control pattern already used elsewhere in the resident architecture. It introduces no second dispatcher, WorkerCoordinator, scheduler, runtime profile, agent registry, InTr implementation, provider route, credential route, or runtime substrate.

New task-specific source surfaces:

```text
control/resident-execution-request.d/stegagents-governed-runtime-targeted-001.json
scripts/consume_stegagents_governed_runtime_targeted_request.py
```

Existing shared surfaces reused:

```text
scripts/dispatch_resident_execution_requests.py
scripts/refresh_sovereign_worker_runtime_source.py
scripts/refresh_sovereign_worker_runtime_source_base.py
scripts/refresh_and_execute_resident_task.py
scripts/run_worker_runtime.py
process:stegagents-governed-runtime-v1
```

The targeted request is `TARGETED_INDEPENDENT_TASK_CONTROL`, is bound to task `STEGAGENTS-GOVERNED-RUNTIME-001` and COSV `71000000101001`, requires a fresh fence greater than zero, and grants no authority. Its consumer rejects hosted execution, strips provider/API/GitHub credential material, preserves `credential_authority=TV/TVC`, requires `github_token_runtime_authority=NONE`, verifies the task/COSV pointer, and delegates only to:

```text
scripts/refresh_and_execute_resident_task.py \
  --task-id STEGAGENTS-GOVERNED-RUNTIME-001 \
  --cosv-task-vector 71000000101001
```

That bridge does not mint a claim or fence. The existing WorkerCoordinator remains the only claim/fence authority.

Expected targeted request-consumption receipt:

```text
receipts/sovereign-host/stegagents-governed-runtime-targeted-request-consumption.latest.json
```

## Authority boundaries

Canonical authority remains:

- Task Registry: work intent and coordination only.
- Runtime Profile Map: discovery/compatibility/routing projection only.
- WorkerCoordinator: execution claim/fence.
- StegCore/InTr: governed ingress/disposition/state-transition authority.
- TV/TVC: provider credential and provider-operation authority.
- KV/SKAP Vault: user-verification authority where applicable.
- Master Records: observed-reality custody/reconstruction.
- GitHub/CI: source validation and evidence transport only; runtime authority `NONE`.

`CodeRepair-001` is deterministic for this proof, so no provider operation is required. Any later provider-backed agent remains exclusively behind TV/TVC.

## Governed roundtrip contract

After authentic targeted resident consumption, the existing WorkerCoordinator must independently admit the task and mint a fresh claim/fence. The task worker then:

1. verifies the exact registered `CodeRepair-001` manifest blob `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`;
2. invokes the existing proposal-only StegAgents runtime;
3. submits the proposal through the existing SDK/canonical StegCore/InTr route;
4. requires an authentic governance disposition with continuous transaction identity;
5. performs no direct consequential execution;
6. performs no TV/TVC provider operation for this deterministic proof;
7. retains exact claim-bound result evidence;
8. requires Master Records custody and same-run reconstruction receipts;
9. returns `COMPLETED` only when all authority and evidence predicates are continuous.

Expected successful governed-runtime receipts:

```text
receipts/sovereign-host/stegagents-governed-runtime/<claim_id>.json
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

## Current authentic runtime observation

The authorized remote resident execution connector reports no connected device in the current session. Current repository-visible WorkerCoordinator state remains `HANDOFF_READY` with no authentic claim/fence, and no claim-bound governed-runtime receipt has been observed.

Therefore no runtime execution, StegCore/InTr disposition, governed proposal return, provider operation, or Master Records reconstruction is claimed from the source remediation. GitHub source, PR merges, Actions validation, runtime-profile matching, and targeted request staging are all non-authorizing evidence surfaces.

## First unresolved predicate after source remediation

```text
AUTHENTIC_TARGETED_RESIDENT_REQUEST_CONSUMPTION_AND_CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
```

Once the targeted bridge is merged and reaches an authentic sovereign resident cycle, the expected sequence is:

```text
resident source refresh
-> existing resident dispatcher visits steagents_governed_runtime_targeted
-> targeted request consumer verifies task/COSV and authority ceiling
-> refresh_and_execute_resident_task.py
-> existing WorkerCoordinator admission review
-> fresh claim/fence
-> process:stegagents-governed-runtime-v1
-> exact CodeRepair-001 manifest verification
-> existing StegAgents proposal runtime
-> existing SDK / canonical StegCore/InTr disposition
-> governed proposal returned with no consequential execution
-> Master Records custody + reconstruct_sovereign receipts
-> claim-bound resident receipt
-> canonical WorkerCoordinator reconciliation/egress
```

## README decision

No README update is required. This binds one existing ACTIVE task to the already-documented targeted WorkerCoordinator execution pattern and existing dispatcher; it adds no new runtime class or authority plane.

## Manual work

None.
