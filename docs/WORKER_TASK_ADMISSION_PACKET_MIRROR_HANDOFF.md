# Worker Task Admission Packet Mirror Handoff

Updated: 2026-08-26T16:12:00-05:00

## Authority and goal

```text
goal_id: WORKER-TASK-ADMISSION-PACKET-016
repository: StegVerse-Labs/.github
branch: main
parent_runtime_handoff: docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md
canonical_issue: StegVerse-Labs/.github#276
state: COMPLETE_VALIDATED
credential_authority: TV/TVC
heartbeat_authority_effect: NONE
review_authority_effect: NONE
```

This handoff owns the universal fail-closed review transaction that must occur immediately before a HANDOFF_READY task may proceed into worker assignment, claim, fence, lease/timer, or worker-instance creation.

It does not create another WorkerCoordinator, heartbeat, scheduler, credential authority, execution authority, or task registry.

## Required transaction

```text
canonical handoff/current task source
  -> current worker-registry projection
  -> fresh Worker Task Admission Packet
  -> source-of-truth reconciliation
  -> dependency review
  -> owner/collision review
  -> execution/admission authority review
  -> credential/non-authority review
  -> stale/superseded task determination
  -> ADMIT | UPDATE | RETIRE | BLOCK
  -> only ADMIT may continue into assignment/claim/fence/lease creation
```

The reviewer is evidence-only. `ADMIT` is a predicate allowing the existing WorkerCoordinator to continue under independently existing execution authority; it grants no execution authority itself.

## Installed canonical surfaces

```text
schemas/worker-task-admission-packet.schema.json
heartbeat_runtime/worker_task_admission.py
heartbeat_runtime/admitted_worker_runtime.py
heartbeat_runtime/worker_runtime_legacy.py
heartbeat_runtime/worker_runtime.py
heartbeat_runtime/__init__.py
tests/test_worker_task_admission.py
tests/test_worker_runtime_independent_admission.py
tests/test_heartbeat_carrier_non_authority.py
.github/workflows/heartbeat-worker-project.yml
receipts/worker-task-admission/**
```

The exact pre-gate WorkerCoordinator implementation is retained in `worker_runtime_legacy.py` only for inheritance/compatibility. `heartbeat_runtime.worker_runtime.WorkerCoordinator` and the package-level `WorkerCoordinator` both resolve to `heartbeat_runtime.admitted_worker_runtime.WorkerCoordinator`, closing the previous direct-import bypass used by resident/runtime launch surfaces.

## Packet requirements

Each packet binds the live task projection, loaded canonical handoff, registry generation, dependency state, worker availability, execution authorization result, current compact heartbeat reference, credential authority, trigger source, source-state reconciliation result where present, and canonical SHA-256 digests of the task/handoff/registry projections reviewed.

Required dispositions:

```text
ADMIT   = all current predicates pass; WorkerCoordinator may continue
UPDATE  = task/handoff projection is stale or semantically changed; do not initiate
RETIRE  = task is superseded/terminal/no longer required; do not initiate
BLOCK   = dependency, authority, collision, credential, executor, or integrity predicate fails
```

## Fail-closed boundary

No generation increment, claim ID, fencing token, worker instance ID, assignment timer/lease, or worker BUSY transition may occur before a fresh admission packet has verdict `ADMIT`.

The admitted wrapper performs review first and returns without invoking the preserved assignment implementation for every non-ADMIT verdict. Only the ADMIT branch delegates to the existing assignment implementation, which retains the fresh fencing-floor, scope, cost-basis, worker-resolution, timer, and claim/fence rules.

Existing ACTIVE workers are not retroactively invalidated. Their lifecycle remains governed by their current claim/fence/lease and closure contract. The gate applies to new HANDOFF_READY activation attempts.

## Authority invariants

```text
credential_authority: TV/TVC
review_grants_execution_authority: false
heartbeat_grants_execution_authority: false
github_token_runtime_authority: NONE
claim_authority_from_review: false
fence_authority_from_review: false
lease_authority_from_review: false
```

Admission receipts are evidence-only. Receipt persistence cannot itself create an assignment or revive a blocked/retired/stale task.

## Validation history

Two validation failures were repaired during installation rather than promoted as completion:

```text
run 33013801617
  failure: malformed compatibility shim source
  disposition: repaired

run 33014061631
  functional repository suite: 577/577 PASS
  remaining failure: stale workflow module-location assertion only
  disposition: workflow assertion reconciled to admitted WorkerCoordinator
```

Terminal exact-current-main validation:

```text
head: 7dd969bbbfe2b58419e638918b48791dd82107c7
workflow: Heartbeat Worker Project - Validation Only / No GitHub Token Authority
run: 33014153166
job: 98327882599
result: SUCCESS
compile runtime/workers/scripts: PASS
canonical JSON parse: PASS (342 files)
executable handoffs: PASS (41 total / 36 live lanes / 5 non-executable)
complete deterministic repository suite: 577/577 PASS
worker admission focused cases: PASS
carrier/worker separation + admitted gate assertion: PASS
external timing zero-authority contract: PASS
historical replay/current protocol anchor: PASS
ephemeral projection validation: PASS
workflow non-authority: PASS
GitHub credential token in validation environment: NONE
```

Focused admission coverage proves:

```text
valid current packet -> ADMIT
missing dependency -> BLOCK
missing execution authorization -> BLOCK
existing assignment/claim -> BLOCK
stale semantic state -> UPDATE
handoff task identity mismatch -> UPDATE
terminal/archive-eligible task -> RETIRE
non-TV/TVC credential authority -> BLOCK
GitHub token runtime authority -> BLOCK
review grants claim/fence/lease/execution authority -> false
```

## Compatibility and heartbeat separation

The existing semantic state-vector preclaim check remains valid and is consumed as one admission predicate. Existing task/handoff schemas are not rewritten merely to add this review transaction.

The canonical heartbeat remains 10 ms / 100 Hz / OSCILLATOR_ONLY. The compact HB identifier is observation context only; heartbeat existence/progression neither admits nor initiates a worker.

## Completion assessment

```text
packet schema: COMPLETE
reviewer: COMPLETE
ADMIT/UPDATE/RETIRE/BLOCK dispositions: COMPLETE
canonical direct-import enforcement: COMPLETE
legacy assignment safeguards retained: COMPLETE
focused fail-closed tests: COMPLETE
full repository regression suite: COMPLETE 577/577
exact-head hosted validation: COMPLETE SUCCESS
missing required source modules: 0
scaffolding/stubs: 0
user/manual action required: NONE
```

## Archive continuity

WORKER-TASK-ADMISSION-PACKET-016 is complete and validated. All unique implementation, validation, failure/repair history, authority boundaries, and continuation semantics are captured here. Conversation history is not required for this goal.
