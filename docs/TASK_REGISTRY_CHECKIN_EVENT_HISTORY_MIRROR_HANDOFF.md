# Task Registry Check-in Event History Mirror Handoff

Goal Task ID: `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`
Parent Goal: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1387`
PR: `StegVerse-Labs/.github#1390`
Status: `ACTIVE / CHECKED_OUT / HASH-LINKED EVENT LEDGER IMPLEMENTED / RECENT-WINDOW EVALUATOR INTEGRATION IMPLEMENTED / CANONICAL SESSION RETURN RECORDER IMPLEMENTED / EXACT-HEAD VALIDATION PENDING`

## Objective

Persist non-authorizing Task Registry check-in/check-out history so collision aggregation can include recently returned sessions as well as tasks currently marked active/checked out.

## Merged prerequisite

Parent PR `StegVerse-Labs/.github#1344` merged at `a1b6043348354072af59b9e1696451720b83cda6` with deterministic Task Registry dispositions, fail-closed Canonical Work pre-mutation enforcement, fail-closed portable WorkerCoordinator preclaim enforcement, exact disposition-hash binding into WorkerCoordinator receipt lineage, central `STEGOS-NODE-MANIFOLD-001` registration, and normalized check-in context carrying session/branch/PR/source-head/first-predicate/intended-target metadata.

This child consumes that existing evaluator and disposition contract. It does not create a second collision engine.

## Implemented source

- `schemas/task-registry-checkin-event.v1.schema.json`
- `scripts/task_registry_checkin_event_history.py`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/record_task_registry_session_return.py`
- `tests/test_task_registry_checkin_event_history.py`
- `tests/test_task_registry_recent_event_collision_integration.py`
- `tests/test_task_registry_session_return_recorder.py`

## Event contract

The event ledger uses `stegverse.task-registry-checkin-event/v1` and retains:

- `task_id` and `session_id`;
- `event_type`: `CHECK_IN`, `CHECK_OUT`, `RETURNED`, or `STOPPED`;
- timezone-aware `event_at`;
- repository / branch / PR / source head / first unresolved predicate;
- repositories and components under mutation;
- registry disposition plus exact disposition SHA-256;
- coordination state;
- predecessor event SHA-256 and current event SHA-256;
- `authority_effect=NONE`.

The JSONL ledger path is configurable through `STEGVERSE_TASK_REGISTRY_EVENT_LEDGER`; default source/runtime projection is `runtime/task-registry/checkin-events.jsonl`. This avoids binding the protocol to GitHub storage and preserves later migration to sovereign KV custody.

## Recent-returned policy

The initial deterministic recent-returned collision window is `1800` seconds / 30 minutes.

For each `(task_id, session_id)`, only the latest event controls whether the session participates. A latest `RETURNED` or `STOPPED` event inside the window contributes collision evidence when its retained repository/component targets overlap the arriving task. A later `CHECK_IN` for that same session supersedes its earlier returned state. Expired events do not participate.

Recent history augments canonical task-record collision evidence. It cannot create a hard current-checkout stop by itself; it produces convergence evidence. Current canonical `CHECKED_OUT` component/lineage overlap remains the source of `STOP_COLLISION` hard-stop behavior.

## Evaluator integration

`evaluate_task_registry_collision_checkin.py` now:

1. reads canonical task records exactly as before;
2. computes current-record collision candidates;
3. reads qualifying recent returned/stopped events from the configured ledger;
4. appends `source=RECENT_EVENT_HISTORY` candidates without replacing canonical-record candidates;
5. returns `COORDINATE_CONVERGENCE` when recent overlap exists absent a harder current checkout collision;
6. records the arriving session's own `CHECK_IN` event when a `session_id` is supplied;
7. returns that `checkin_event_sha256` in the disposition envelope.

The check-in event is recorded by the registry evaluator before downstream Canonical Work source mutation or portable WorkerCoordinator claim issuance, preserving the parent ordering contract.

## Canonical session return path

`scripts/record_task_registry_session_return.py` is the bounded session/task relinquish entrypoint. It accepts only `CHECK_OUT`, `RETURNED`, or `STOPPED`, requires the exact Task Registry disposition object on stdin, validates exact task identity and `authority_effect=NONE`, appends through the same hash-linked ledger implementation, and emits `stegverse.task-registry-session-return-receipt/v1` containing the resulting event/predecessor hashes with no authority effect.

This makes the return side explicit rather than relying on callers to construct ledger rows directly.

## Tests

Deterministic tests cover:

- hash-linked append/reload;
- recent returned overlap;
- 30-minute expiry;
- latest-session-state replacement;
- tamper/hash failure;
- existing evaluator consumption of recent returned evidence;
- evaluator recording of current `CHECK_IN`;
- canonical return recorder append;
- wrong-task disposition rejection before ledger mutation.

## Authority invariants

Task Registry event history is coordination evidence only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Remaining

1. obtain exact-head validation and repair any regression;
2. bind the canonical return recorder into the actual session/task relinquish/stop/supersession orchestration path so callers do not need to invoke it manually;
3. update root README with the durable recent-session collision-window protocol if required by repository functional-change invariant;
4. merge PR #1390 after exact-head validation is green;
5. after merge, evaluate projection of the event ledger into StegVerse sovereign KV custody without changing evaluator semantics.

## Manual work

None.
