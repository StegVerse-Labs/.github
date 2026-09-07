# COSV Task Pointer Runtime Enforcement Mirror Handoff

Status: SOURCE_COMPACT_CONTINUATION_POST_RESOLUTION_PICKUP_AND_LIFECYCLE_STATUS_SEMANTICS_FIXED / EXECUTION_EVIDENCE_PENDING
Repository: `StegVerse-Labs/.github`
Task ID: `COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001`
COSV: `10100000100000`
Root correlation / goal: `STEGVERSE-CANONICAL-WORK-COORDINATION-001`
Canonical pointer policy: `data/task-coordination-policy.json`
Canonical lifecycle contract: `data/task-lifecycle-status-contract.json`
Continuation evaluator: `scripts/evaluate_goal_resolution_continuation.py`
Compact continuation tests: `tests/test_goal_resolution_compact_pointer.py`
Retired review tests: `tests/test_retired_task_history_review.py`
Lifecycle status tests: `tests/test_task_lifecycle_statuses.py`
Resident execution request: `control/resident-execution-request.d/cosv-task-pointer-runtime-enforcement-001.json`
Resident consumer: `scripts/consume_cosv_task_pointer_runtime_enforcement_request.py`
Resident dispatcher: `scripts/dispatch_resident_execution_requests.py#cosv_task_pointer_runtime_enforcement`
Resident execution bridge: `scripts/refresh_and_execute_resident_task.py`
Expected consumption receipt: `receipts/sovereign-host/cosv-task-pointer-runtime-enforcement-request-consumption.latest.json`

## Compact continuation invariant

`Task ID + COSV` is sufficient to resolve canonical task state. The evaluator resolves the canonical record, handoffs, dependencies, adjacent work, evidence/provenance, and existing execution-request references, then derives the next admissible work where the lifecycle state permits continuation.

A status-only response is not valid continuation for unresolved ACTIVE work. If ACTIVE work has no resolvable next action, evaluation returns `CONTINUATION_RESOLUTION_INCOMPLETE`.

## Canonical lifecycle states

The canonical lifecycle set is:

- `ACTIVE` — work remains; normal continuation is allowed.
- `COMPLETED` — primary task work is complete; only explicit closure, propagation, release, or retirement verification work may continue.
- `RETIRED` — terminal, closed, non-executable, non-resumable, provenance/history only.
- `SUPERSEDED` — terminal under the old identity; redirect-only to an explicitly linked successor Task ID/COSV.
- `INVALID` — canonical state/identity is inconsistent or unsupported; fail closed until repaired.

Unknown lifecycle labels normalize to `INVALID`; they do not silently become ACTIVE.

## RETIRED invariant

`RETIRED` is terminal. It never emits a continuation request and never restores execution under that Task ID.

Resurrection of a retired task means **history review only**. The history-review projection may expose the canonical record, COSV projection, handoffs, evidence, receipts, and reconstruction material needed to make the history reviewable. It cannot restore execution, continuation, claim/fence use, transition progression, or prior consequence authority.

If historical review discovers new work, the system creates a new Task ID linked to the retired task by provenance. The retired task remains retired.

## COMPLETED invariant

`COMPLETED` is not ordinary implementation work. It may continue only for explicit closure kinds:

- `CLOSURE_VERIFICATION`
- `PROPAGATION_VERIFICATION`
- `RELEASE_VERIFICATION`
- `RETIREMENT_VERIFICATION`
- `RETIRE_TASK`

When explicit closure predicates are satisfied, the evaluator returns `COMPLETED_READY_TO_RETIRE`; feature implementation under a COMPLETED identity is rejected as unresolved closure semantics rather than resumed as normal work.

Recommended retirement predicates are implementation complete, validation complete, required evidence reconciled, required propagation complete, required release/tag complete, and no unresolved task-owned work.

## SUPERSEDED invariant

`SUPERSEDED` never resumes the source Task ID. It emits a redirect projection only. A successor Task ID is required; successor COSV should be included whenever available. Missing successor identity produces `SUPERSEDED_SUCCESSOR_UNRESOLVED`.

## Stale handoff invariant

Canonical Task Registry lifecycle state wins over handoff projections. A stale handoff cannot reactivate a `RETIRED`, `SUPERSEDED`, or `INVALID` task. Stale handoffs are reconciliation/provenance inputs only.

## Governance / authority semantics

A runtime is an execution substrate/surface, not a boundary. Authority is a consequence of governance: governance determines the admissible action, scope, predicates, and conditions from which authority for a consequence follows. Possession of a credential, claim, runtime, model capability, or task identity does not independently create authority.

## Implemented source behavior

The source now includes compact pointer resolution, canonical lifecycle classification, next-work derivation, continuation-request emission, status-only rejection, COMPLETED closure-only behavior, RETIRED terminal/review-only behavior, SUPERSEDED redirect-only behavior, INVALID fail-closed behavior, and stale-handoff suppression semantics.

No centralized executable queue was introduced.

## Current COSV state

```text
profile: task.v1
vector: 10100000100000
lifecycle: UNCLAIMED
archive_ready: false
unassigned_work: 1
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
