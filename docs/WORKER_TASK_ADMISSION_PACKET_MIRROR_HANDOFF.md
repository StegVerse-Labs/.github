# Worker Task Admission Packet Mirror Handoff

Updated: 2026-08-26T16:01:00-05:00

## Authority and goal

```text
goal_id: WORKER-TASK-ADMISSION-PACKET-016
repository: StegVerse-Labs/.github
branch: main
parent_runtime_handoff: docs/HEARTBEAT_RUNTIME_SEPARATION_MIRROR_HANDOFF.md
state: SOURCE_IMPLEMENTATION_ACTIVE
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

## Canonical surfaces

```text
schemas/worker-task-admission-packet.schema.json
heartbeat_runtime/worker_task_admission.py
heartbeat_runtime/admitted_worker_runtime.py
tests/test_worker_task_admission.py
receipts/worker-task-admission/**
```

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

Existing ACTIVE workers are not retroactively invalidated. Their lifecycle remains governed by their current claim/fence/lease and closure contract. The new gate applies to new HANDOFF_READY activation attempts.

## Compatibility

The existing semantic state-vector preclaim check remains valid and is consumed as one admission predicate. Existing task/handoff schemas are not rewritten merely to add this review transaction.

The canonical heartbeat remains 10 ms / 100 Hz / OSCILLATOR_ONLY. The compact HB identifier is observation context only.

## Completion predicate

This goal is complete only when:

1. packet schema and deterministic reviewer exist;
2. reviewer emits ADMIT/UPDATE/RETIRE/BLOCK with explicit reasons;
3. canonical worker runtime path invokes review before assignment authority artifacts are minted;
4. admission receipts are persistence-only evidence and cannot grant authority;
5. focused tests prove valid admission and fail-closed stale/dependency/authority/credential/collision cases;
6. exact-current-main hosted validation passes.

## Archive continuity

This file is the canonical continuation source for WORKER-TASK-ADMISSION-PACKET-016. Conversation history is not required after the implementation state below is reconciled here.
