# COSV Task Pointer Runtime Enforcement Mirror Handoff

Status: SOURCE_COMPACT_CONTINUATION_AND_POST_RESOLUTION_PICKUP_FIXED / EXECUTION_EVIDENCE_PENDING
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

## Defects corrected 2026-09-07

Two source defects prevented the intended compact continuation behavior.

First, the continuation evaluator required pre-expanded `returned_tasks` and an explicit `goal_id`. That contradicted the compact-pointer contract. The evaluator now accepts only:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

and resolves the exact Task ID/vector binding, canonical task record, root correlation/goal, applicable `*_MIRROR_HANDOFF.md` references, dependencies, adjacent tasks, evidence references, source-vector provenance, and registry provenance.

Second, after successful resolution the evaluator returned `continue_machine_work=true` but did not emit a machine-consumable continuation request. That allowed a receiving session/process to stop at status reporting even though unresolved work remained.

The evaluator now derives the next admissible work from canonical task state. It prefers an explicit canonical `next_admissible_work`/next-transition field when present and otherwise reuses an existing canonical resident execution request referenced by the task. It emits `stegverse.machine-continuation-request/v1` with `automatic_pickup_required=true`, `human_reentry_required=false`, and `status_only_response_is_completion=false`.

If an active task resolves but no next admissible work can be resolved, the evaluator now returns `CONTINUATION_RESOLUTION_INCOMPLETE` and does not claim successful autonomous continuation. A status-only result is explicitly invalid continuation state.

Tests cover exact compact resolution, Task/COSV mismatch, missing task identity, execution-request derivation, and machine continuation-request emission.

## Governance / authority semantics

A runtime is an execution substrate/surface, not a boundary.

Authority is a consequence of governance. Governance determines the admissible action, scope, predicates, and conditions from which authority for that consequence follows. Possession of a credential, claim, runtime, model capability, or task identity does not independently create authority.

Actual boundaries are real limits, interfaces, containment edges, trust separations, consequence limits, or explicit progression conditions. Governance predicates may require claim/fence state, transition admission, credential validity, reconstruction state, human-only consent, or other canonically defined conditions before a consequence may proceed.

## Purpose

A continuation payload containing only Task ID + COSV task vector must be enough for the system to reconstruct current canonical work and continue from the first unresolved admissible action without requiring the user to replay task prose, handoff text, goal identifiers, or prior session state.

## Implemented source behavior

The source path now includes:

1. compact Task ID + COSV pointer validation;
2. canonical task and handoff resolution;
3. dependency, adjacency, evidence, and provenance resolution;
4. existing resident execution-request discovery;
5. next-admissible-work derivation;
6. machine continuation-request emission;
7. explicit prohibition on treating a status-only response as successful continuation;
8. fail-closed incomplete-resolution state when an active task has no resolvable next work;
9. resident request/consumer/dispatcher integration;
10. reusable-task identity/construct semantics and bounded execution path.

No second task registry, queue, scheduler, WorkerCoordinator, heartbeat, credential plane, dispatcher, or permanent runner plane was created.

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

The vector is not changed by source correction alone.

## Next proof predicate

The remaining proof requirement is observation that the corrected compact-pointer continuation request is consumed through the existing execution path and produces the expected governed consequence/evidence. The first expected component-produced receipt remains:

```text
receipts/sovereign-host/cosv-task-pointer-runtime-enforcement-request-consumption.latest.json
```
