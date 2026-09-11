# Task Registry Check-in Event History Mirror Handoff

Goal Task ID: `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`
Parent Goal: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1387`
PR: `StegVerse-Labs/.github#1390`
Status: `ACTIVE / CHECKED_OUT / HASH-LINKED EVENT LEDGER IMPLEMENTED / RECENT-WINDOW EVALUATOR INTEGRATION IMPLEMENTED / CANONICAL SESSION RETURN RECORDER IMPLEMENTED / STOP DISPOSITIONS AUTO-CLOSE / EXACT-HEAD VALIDATION PENDING`

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

The event ledger uses `stegverse.task-registry-checkin-event/v1` and retains task/session identity, event type (`CHECK_IN`, `CHECK_OUT`, `RETURNED`, `STOPPED`), timezone-aware event time, repository/branch/PR/source-head/first-unresolved-predicate context, repositories/components under mutation, exact registry disposition and hash, coordination state, predecessor event hash, current event hash, and `authority_effect=NONE`.

The JSONL ledger path is configurable through `STEGVERSE_TASK_REGISTRY_EVENT_LEDGER`; default source/runtime projection is `runtime/task-registry/checkin-events.jsonl`. This avoids binding the protocol to GitHub storage and preserves later migration to sovereign KV custody.

## Recent-returned policy

The deterministic recent-returned collision window is `1800` seconds / 30 minutes.

For each `(task_id, session_id)`, only the latest event controls participation. A latest `RETURNED` or `STOPPED` event inside the window contributes collision evidence when its retained repository/component targets overlap the arriving task. A later `CHECK_IN` for that same session supersedes its earlier returned state. Expired events do not participate.

Recent history augments canonical task-record collision evidence. It cannot create a hard current-checkout stop by itself; it produces convergence evidence. Current canonical `CHECKED_OUT` component/lineage overlap remains the source of `STOP_COLLISION` hard-stop behavior.

## Evaluator integration

`evaluate_task_registry_collision_checkin.py` now reads canonical task records, computes current-record collisions, reads qualifying recent returned/stopped events, appends `source=RECENT_EVENT_HISTORY` candidates, returns `COORDINATE_CONVERGENCE` when recent overlap exists absent a harder current checkout collision, records the arriving session's `CHECK_IN`, and returns `checkin_event_sha256`.

When the resulting disposition begins with `STOP_`, the evaluator immediately appends a same-session `STOPPED` event through the same hash chain and returns `stopped_event_sha256`. Therefore a rejected/superseded/inactive/unregistered session cannot leave a dangling latest `CHECK_IN` after the registry has already instructed it to end.

The check-in/stop events are recorded before downstream Canonical Work source mutation or portable WorkerCoordinator claim issuance, preserving the parent ordering contract.

## Canonical voluntary session return path

`scripts/record_task_registry_session_return.py` is the bounded normal-session/task relinquish entrypoint. It accepts only `CHECK_OUT`, `RETURNED`, or `STOPPED`, requires the exact Task Registry disposition object on stdin, validates exact task identity and `authority_effect=NONE`, appends through the same hash-linked ledger, and emits `stegverse.task-registry-session-return-receipt/v1` containing event/predecessor hashes with no authority effect.

No prior general-purpose session/task relinquish executable was found in the canonical registry scripts. The worker-return observation contract concerns execution-history return to Master Records, which is a different boundary and should not be overloaded with ChatGPT/session coordination state. This child therefore establishes the registry-owned coordination return entrypoint explicitly.

## Validation evidence

Implementation head `0ef65b20f64afc36b7f73f5813d938416903afe0` passed:

- Deterministic Repository Suite run `34563433154`;
- Validate organization control plane run `34563433104`;
- Heartbeat Worker Project validation run `34563433138`.

The branch has advanced with automatic `STOP_*` session closure and its integration test; fresh exact-head validation is required before merge.

## Tests

Deterministic tests cover hash-linked append/reload, recent returned overlap, 30-minute expiry, latest-session-state replacement, tamper/hash failure, evaluator consumption of recent returned evidence, evaluator current `CHECK_IN`, canonical voluntary return recording, wrong-task rejection before ledger mutation, and automatic `CHECK_IN -> STOPPED` closure for rejected sessions.

## Authority invariants

Task Registry event history is coordination evidence only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Remaining

1. obtain exact-head validation after automatic STOP closure and repair any regression;
2. merge PR #1390 when required validation is green;
3. after merge, bind voluntary session-return invocation into the product/session orchestration surface that emits the task handoff/footer, without changing ledger/evaluator semantics;
4. evaluate projection of the event ledger into StegVerse sovereign KV custody without changing collision semantics.

## README impact review

The root README already documents Task Registry resolution, cross-task collision coordination, and Canonical Work pre-admission semantics. This child adds durable recent-session evidence beneath that existing protocol rather than changing its user-level authority model. The canonical handoff is the direct functional reference for the new ledger/window mechanism; no root README rewrite is required for this merge.

## Manual work

None.
