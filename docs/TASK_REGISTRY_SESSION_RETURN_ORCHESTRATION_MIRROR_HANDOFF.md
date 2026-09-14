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
