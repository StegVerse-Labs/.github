# COSV Task Pointer Runtime Enforcement Mirror Handoff

Status: SOURCE_COMPACT_CONTINUATION_RESOLUTION_FIXED / EXECUTION_EVIDENCE_PENDING
Repository: `StegVerse-Labs/.github`
Task ID: `COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001`
Root correlation / goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Parent task: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Canonical pointer policy: `data/task-coordination-policy.json`
Pointer contract handoff: `docs/COSV_TASK_POINTER_COORDINATION_MIRROR_HANDOFF.md`
Reusable construct handoff: `docs/REUSABLE_TASK_EPHEMERAL_CONSTRUCT_MIRROR_HANDOFF.md`
Reusable registry: `data/reusable-task-registry.json#generation-2`
Reusable construct contract: `data/reusable-task-ephemeral-construct-contract.json`
COSV profile: `management/COSV_PROFILE_V1.json#task.v1`
Machine preflight: `receipts/preflight/COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001.json`
Resident execution request: `control/resident-execution-request.d/cosv-task-pointer-runtime-enforcement-001.json`
Resident consumer: `scripts/consume_cosv_task_pointer_runtime_enforcement_request.py`
Resident dispatcher: `scripts/dispatch_resident_execution_requests.py#cosv_task_pointer_runtime_enforcement`
Resident execution bridge: `scripts/refresh_and_execute_resident_task.py`
Continuation evaluator: `scripts/evaluate_goal_resolution_continuation.py`
Compact continuation tests: `tests/test_goal_resolution_compact_pointer.py`
Expected consumption receipt: `receipts/sovereign-host/cosv-task-pointer-runtime-enforcement-request-consumption.latest.json`

## Defect corrected 2026-09-07

The continuation evaluator previously required callers to supply pre-expanded `returned_tasks` and an explicit `goal_id`. That contradicted the canonical compact-pointer contract because a receiving session/runtime could not use only `task_id + cosv_task_vector` to reconstruct canonical continuation state.

The evaluator now resolves compact continuation directly from:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

It verifies the exact Task ID/vector binding against `control/task-vector-index.json`, resolves the unique record in `data/canonical-task-registry.json`, derives root goal/correlation identity, resolves applicable `*_MIRROR_HANDOFF.md` references, dependencies, adjacent tasks, evidence references, source state-vector provenance, and registry provenance, and then feeds that resolved task into the existing autonomous continuation evaluation.

Fail-closed tests were added for exact resolution, vector mismatch, and missing task identity. This source fix does not mint WorkerCoordinator claim/fence, Interlock/InTr transition authority, credential authority, or runtime evidence.

## Terminology correction

A runtime is not an authority or governance boundary. It is an execution substrate/surface. The canonical boundaries relevant to this task are:

- WorkerCoordinator claim/fence authority;
- Interlock/InTr governed transition admission;
- TV/TVC credential authority;
- Master Records observed-reality and reconstruction authority;
- explicit human-only authority states where applicable.

Runtime availability, locality, freshness, or successful execution may be predicates or observations, but they are not themselves governance boundaries.

## Purpose

Implement machine/runtime enforcement so a continuation payload containing only:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

can resolve complete canonical task context, applicable reusable identities, and the exact invocation-specific TT/RTG/GTG construct needed for the highest-priority admissible work without repeated prompt prose or permanent one-off runners.

## Implemented source behavior

The source path includes canonical compact-pointer continuation policy, reusable-task identity/construct semantics, resident pointer validation, resident request/consumer/dispatcher integration, and now direct compact-pointer canonical resolution in the continuation evaluator.

No second task registry, COSV profile, scheduler, WorkerCoordinator, heartbeat, oscillator, credential authority, transition authority, dispatcher, or permanent runner plane was created.

## Remaining execution evidence

Execution evidence must still demonstrate consumption through the already-materialized resident execution surface, including pointer verification before execution, ordinary WorkerCoordinator admission/claim/fence when admissible, applicable Interlock/InTr transition admission, required bounded invocation construction, execution receipts, Master Records custody/reconstruction, and entropy recovery where applicable.

These are execution/evidence requirements across the existing authority boundaries. They are not runtime boundaries.

## Current COSV state

```text
profile: task.v1
vector: 10100000100000
symbol_order: LRUIVGOCMTBEAP
lifecycle: UNCLAIMED
archive_ready: false
unassigned_work: 1
chat_owned_implementation: 0
chat_owned_validation: 0
chat_owned_integration: 0
chat_owned_observation: 0
chat_owned_credentials: 0
canonical_owner_installed: true
thread_required: false
blocker_count: 0
evidence_complete: false
activated: false
propagated: false
```

The vector remains unchanged because source correction and source tests are not a WorkerCoordinator claim, execution receipt, Master Records custody/reconstruction proof, or activation proof.

## Next evidence predicate

The source defect that forced pre-expanded continuation context is corrected. The next evidence predicate is successful resident consumption of the corrected compact pointer path. The expected first authentic receipt remains:

```text
receipts/sovereign-host/cosv-task-pointer-runtime-enforcement-request-consumption.latest.json
```
