# Task Registry Check-in Event History Mirror Handoff

Goal Task ID: `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`
Parent Goal: `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`
Canonical issue: `StegVerse-Labs/.github#1387`
Implementation PR: `StegVerse-Labs/.github#1390`
Merge commit: `0e2c9b94e4ffc224a2b3cfc1ac25bef36bb6eeb5`
Status: `ACTIVE / CHECKED_OUT / HASH-LINKED EVENT LEDGER MERGED_VALIDATED / RECENT-WINDOW EVALUATOR INTEGRATION MERGED_VALIDATED / CANONICAL SESSION RETURN RECORDER MERGED_VALIDATED / STOP DISPOSITIONS AUTO-CLOSE`

## Objective

Persist non-authorizing Task Registry check-in/check-out history so collision aggregation can include recently returned sessions as well as tasks currently marked active/checked out.

## Merged prerequisite

Parent PR `StegVerse-Labs/.github#1344` merged at `a1b6043348354072af59b9e1696451720b83cda6` with deterministic Task Registry dispositions, fail-closed Canonical Work pre-mutation enforcement, fail-closed portable WorkerCoordinator preclaim enforcement, exact disposition-hash binding into WorkerCoordinator receipt lineage, central `STEGOS-NODE-MANIFOLD-001` registration, and normalized check-in context carrying session/branch/PR/source-head/first-predicate/intended-target metadata.

This child consumes that existing evaluator and disposition contract. It does not create a second collision engine.

## Merged implementation

- `schemas/task-registry-checkin-event.v1.schema.json`
- `scripts/task_registry_checkin_event_history.py`
- `scripts/evaluate_task_registry_collision_checkin.py`
- `scripts/record_task_registry_session_return.py`
- `tests/test_task_registry_checkin_event_history.py`
- `tests/test_task_registry_recent_event_collision_integration.py`
- `tests/test_task_registry_session_return_recorder.py`

PR #1390 merged on 2026-09-11 as `0e2c9b94e4ffc224a2b3cfc1ac25bef36bb6eeb5`. The branch's final validated head carried the automatic STOP closure and recent-return integration. Source/validation merge evidence does not grant execution authority.

## Event contract

The event ledger uses `stegverse.task-registry-checkin-event/v1` and retains task/session identity, event type (`CHECK_IN`, `CHECK_OUT`, `RETURNED`, `STOPPED`), timezone-aware event time, repository/branch/PR/source-head/first-unresolved-predicate context, repositories/components under mutation, exact registry disposition and hash, coordination state, predecessor event hash, current event hash, and `authority_effect=NONE`.

The JSONL ledger path is configurable through `STEGVERSE_TASK_REGISTRY_EVENT_LEDGER`; default source/runtime projection is `runtime/task-registry/checkin-events.jsonl`. This avoids binding the protocol to GitHub storage and preserves later migration to sovereign KV custody.

## Recent-returned policy

The deterministic recent-returned collision window is `1800` seconds / 30 minutes.

For each `(task_id, session_id)`, only the latest event controls participation. A latest `RETURNED` or `STOPPED` event inside the window contributes collision evidence when its retained repository/component targets overlap the arriving task. A later `CHECK_IN` for that same session supersedes its earlier returned state. Expired events do not participate.

Recent history augments canonical task-record collision evidence. It cannot create a hard current-checkout stop by itself; it produces convergence evidence. Current canonical `CHECKED_OUT` component/lineage overlap remains the source of `STOP_COLLISION` hard-stop behavior.

## Evaluator integration

`evaluate_task_registry_collision_checkin.py` reads canonical task records, computes current-record collisions, reads qualifying recent returned/stopped events, appends `source=RECENT_EVENT_HISTORY` candidates, returns `COORDINATE_CONVERGENCE` when recent overlap exists absent a harder current checkout collision, records the arriving session's `CHECK_IN`, and returns `checkin_event_sha256`.

When the resulting disposition begins with `STOP_`, the evaluator immediately appends a same-session `STOPPED` event through the same hash chain and returns `stopped_event_sha256`. Therefore a rejected/superseded/inactive/unregistered session cannot leave a dangling latest `CHECK_IN` after the registry has instructed it to end.

The check-in/stop events are recorded before downstream Canonical Work source mutation or portable WorkerCoordinator claim issuance, preserving the parent ordering contract.

## Canonical voluntary session return path

`scripts/record_task_registry_session_return.py` is the bounded normal-session/task relinquish entrypoint. It accepts only `CHECK_OUT`, `RETURNED`, or `STOPPED`, requires the exact Task Registry disposition object on stdin, validates exact task identity and `authority_effect=NONE`, appends through the same hash-linked ledger, and emits `stegverse.task-registry-session-return-receipt/v1` containing event/predecessor hashes with no authority effect.

The worker-return observation contract concerns execution-history return to Master Records, which is a different boundary and is not overloaded with ChatGPT/session coordination state.

## Validation and merge evidence

Implementation PR #1390 is merged. Historical exact-head validation for the implementation passed the deterministic repository suite, organization-control validation, and Heartbeat validation before merge. The authoritative merge commit is `0e2c9b94e4ffc224a2b3cfc1ac25bef36bb6eeb5`.

## Authority invariants

Task Registry event history is coordination evidence only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition/admission authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Remaining

1. keep the merged event ledger/evaluator semantics as the single Task Registry collision-history implementation;
2. use `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001` for product/session footer-close gating rather than adding another return mechanism;
3. continue the existing `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001` lane for sovereign KV event custody without changing collision semantics;
4. converge future user/browser action-surface collision work into the parent anti-collision goal instead of creating a second collision engine.

## README impact review

The root README already documents Task Registry resolution, cross-task collision coordination, and Canonical Work pre-admission semantics. This child adds durable recent-session evidence beneath that existing protocol rather than changing its user-level authority model; no root README rewrite is required.

## Manual work

None.

## 2026-09-24 component-010 exact predecessor readback — owner review candidate

The canonical evaluator already writes the arriving session's `CHECK_IN` through the existing hash-linked Task Registry event ledger and immediately records `STOPPED` for `STOP_*` dispositions. The previously returned gate disposition carried the check-in and STOP event hashes but omitted their exact immediate-predecessor hashes. The existing source-level check-in response now includes `checkin_event_predecessor_sha256` and (for a STOP event) `stopped_event_predecessor_sha256`, using exact values returned by the **existing** `append_event` call. Positive and STOP regression tests require parity with the actual retained JSONL events. No new ledger, runtime, caller, task identity, attestation, or governance authority is introduced. A check-in without an actual retained event cannot claim a predecessor, and an inaccessible resident ledger remains UNKNOWN.

This source repair is a component-010 owner-review candidate, not authentic `AI_SESSION_GATE` invocation, actual component-010 registry/shard reconciliation, a COSV assignment, or governed execution evidence for `WORKER-TASK-RESOURCE-COST-LINKAGE-001` / issue #2619. The first authentic runtime chain remains exact-shard projection readback, genuine generation-bound session invocation, hash-linked event readback, and applicable organization/Master Records evidence separately.
