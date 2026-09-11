# Task Registry Check-in Event History Mirror Handoff

Goal Task ID: `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`
Parent Goal: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1387`
Status: `ACTIVE / CHECKED_OUT / CHILD REGISTERED / IMPLEMENTATION READY`

## Objective

Persist non-authorizing Task Registry check-in/check-out history so collision aggregation can include recently returned sessions as well as tasks currently marked active/checked out.

## Merged prerequisite

Parent PR `StegVerse-Labs/.github#1344` merged at `a1b6043348354072af59b9e1696451720b83cda6` with:

- deterministic Task Registry dispositions;
- fail-closed Canonical Work pre-mutation enforcement;
- fail-closed portable WorkerCoordinator preclaim enforcement;
- exact disposition-hash binding into WorkerCoordinator receipt lineage;
- central registration of `STEGOS-NODE-MANIFOLD-001`;
- normalized check-in context carrying session/branch/PR/source-head/first-predicate/intended-target metadata.

This child must consume that existing evaluator and disposition contract. It must not create a second collision engine.

## Required retained event fields

- `task_id`
- `session_id`
- `event_type` (`CHECK_IN`, `CHECK_OUT`, `RETURNED`, or equivalent canonical states)
- `checked_in_at` / `checked_out_at`
- repository
- branch
- pull request
- source head
- first unresolved predicate
- repositories under mutation
- components under mutation
- registry disposition
- exact disposition SHA-256
- checkout/return state
- predecessor event hash / event hash for reconstructable ordering

## Required behavior

1. Record check-in before source mutation or claim issuance.
2. Record return/check-out when a session relinquishes the task or is stopped/superseded.
3. Define a deterministic recent-returned window policy.
4. Feed qualifying recent events into `evaluate_task_registry_collision_checkin.py` as additional collision evidence.
5. Preserve current task-record collision checks; event history augments rather than replaces them.
6. Keep all event evidence non-authorizing.
7. Keep storage/provider semantics abstract enough to move from GitHub/runtime projection to StegVerse sovereign KV custody later.

## Authority invariants

Task Registry history is coordination evidence only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Next implementation

1. define versioned event schema;
2. implement append/record helper with hash-linked events;
3. implement recent-window reader;
4. augment the merged anti-collision evaluator with recent-event candidates;
5. add deterministic tests for check-in, return, expiry, collision, and supersession cases;
6. update README/handoff where functionally required;
7. validate exact head and merge.

## Manual work

None.
