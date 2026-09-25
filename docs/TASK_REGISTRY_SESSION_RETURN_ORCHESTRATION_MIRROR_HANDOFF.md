# Task Registry Session Return Orchestration Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Parent: `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`
Canonical issue: `StegVerse-Labs/.github#1411`
Implementation PR: `StegVerse-Labs/.github#1412`
Merge commit: `bba6467fd324ba0b97ec759c76b65bb9a73ef2fa`
Status: `ACTIVE / CHECKED_OUT / SESSION-CLOSE COORDINATOR MERGED_VALIDATED / FOOTER-HANDOFF RETURN RECEIPT GATE MERGED_VALIDATED`

## Objective
Bind normal voluntary session close to the merged Task Registry RETURNED/CHECK_OUT ledger so handoff/footer completion cannot silently relinquish work outside the anti-collision history.

## Merged implementation
- `scripts/materialize_task_session_close.py`
- `data/task-session-close-orchestration-contract.json`
- `tests/test_task_registry_session_close_orchestration.py`
- `data/canonical-task-records/TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001.json`

The coordinator validates the exact Task Registry disposition, exact task identity, and `authority_effect=NONE`, delegates to the merged `record_task_registry_session_return.py`, requires the returned canonical `event_sha256`, and only then emits `stegverse.task-session-close/v1` with `footer_handoff_emission_admissible=true` and `required_pre_footer_return_event_sha256`.

The child orchestration contract is anchored to `data/task-coordination-policy.json#session_close_contract`. Its ordering requires canonical continuity materialization, exact disposition validation, hash-linked return append, return-event hash verification, and only then footer/handoff emission. Failed return recording blocks session-close/footer admission. No second collision engine is introduced.

## Validation and merge evidence
PR #1412 merged on 2026-09-11 as `bba6467fd324ba0b97ec759c76b65bb9a73ef2fa`. Final exact-head validation passed the deterministic repository suite, organization-control lane, and Heartbeat validation before merge.

The previous handoff wording that exact-head validation and merge were still pending was stale and is superseded by this merged state.

## Authority
Task/session close evidence is coordination only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Remaining
1. preserve this merged session-close coordinator as the sole footer/handoff return gate;
2. project it into future product-specific UI/session emitters only by reuse, without changing ledger/evaluator semantics;
3. continue sovereign KV event-history custody through `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001` rather than creating another session-return mechanism.

## Manual work
None.

## Session STATUS duplicate/conjunction projection — source candidate, 2026-09-25

This is additive work under **the existing** `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001` Goal and its parent `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`, coordinated by issues #1411 and #1387. The current Registry generation inspected for this change was 248; owner remained `ACTIVE / CHECKED_OUT`. The implementation is a separate **source-only review candidate** and must be reconciled with the checked-out owner's active mutation scope before merging. No new task, COSV, checkout, ledger, claim/fence or separate collision evaluator was created.

The existing check-in evaluator now emits an additive `session_status_projection`, included in its existing disposition hash before recording an event. It retains the original `disposition` and `session_action` outputs. The existing session-close coordinator validates and echoes the projection **before** appending a RETURNED/CHECK_OUT event; legacy callers without a projection receive `UNVERIFIED` defaults. The existing return-event hash continues to gate footer emission.

```text
STATUS: <canonical task lifecycle> /
        DUPLICATE: UNVERIFIED | CONFIRMED /
        COLLISION: UNVERIFIED | CONJOIN_REQUIRED | REVIEW_REQUIRED |
                   NO_REGISTERED_COLLISION_OBSERVED
```

`CONJOIN_REQUIRED` follows an exact existing `hard_collision_task_ids` checkout collision. `COORDINATE_CONVERGENCE` remains review-only; shared repositories or shareable runtime surfaces do not automatically require absorption. Two distinct active CHECK_IN events on the *same task* and same component/branch/PR establish a retained **candidate**; because the present ChatGPT source caller does not supply authenticated session origin, the projected duplicate remains `UNVERIFIED`, even when the ledger hash chain validates. Genuine `CONFIRMED` must wait for existing authenticated session-origin evidence; no synthetic source test or declaration may promote it. When a second active check-in candidate shares the mutation scope, overlapping mutations require owner coordination even without authenticated duplication. A recent RETURNED/STOPPED event does not constitute an active duplicate. Existing 1800-second recent-return collision handling is unchanged.

The projected status is **non-authorizing presentation and routing evidence**, not a new task lifecycle state, successor allocation, owner election or permission to mutate. The checked-out owner must validate current claims and current registry generation when absorbing overlapping work. Until authentic ChatGPT session-origin ingress is established, live enforcement of the confirmed-duplicate path remains `NOT_ESTABLISHED`. Source tests exercise synthetic candidate, return, current hard collision, stale-generation and pre-return validation cases; exact-head CI and owner merge still require independent proof.
