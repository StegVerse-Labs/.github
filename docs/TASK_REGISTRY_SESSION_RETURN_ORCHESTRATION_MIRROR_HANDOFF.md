# Task Registry Session Return Orchestration Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Parent: `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`
Canonical issue: `StegVerse-Labs/.github#1411`
PR: `StegVerse-Labs/.github#1412`
Status: `ACTIVE / CHECKED_OUT / SESSION-CLOSE COORDINATOR IMPLEMENTED / FOOTER-HANDOFF RETURN RECEIPT GATE BOUND / EXACT-HEAD VALIDATION PENDING`

## Objective
Bind normal voluntary session close to the merged Task Registry RETURNED/CHECK_OUT ledger so handoff/footer completion cannot silently relinquish work outside the anti-collision history.

## Implemented
- `scripts/materialize_task_session_close.py`
- `data/task-session-close-orchestration-contract.json`
- `tests/test_task_registry_session_close_orchestration.py`
- `data/canonical-task-records/TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001.json`

The coordinator validates the exact Task Registry disposition, exact task identity, and `authority_effect=NONE`, delegates to the already-merged `record_task_registry_session_return.py`, requires the returned canonical `event_sha256`, and only then emits `stegverse.task-session-close/v1` with `footer_handoff_emission_admissible=true` and `required_pre_footer_return_event_sha256`.

The child orchestration contract is explicitly anchored to `data/task-coordination-policy.json#session_close_contract`. Its ordering now requires canonical continuity materialization, exact disposition validation, hash-linked return append, return-event hash verification, and only then footer/handoff emission. Failed return recording blocks session-close/footer admission. No second collision engine is introduced.

## Validation evidence
Initial PR #1412 head `107ce1027c0436e805c2ea3db6f0a3134762fab2` passed:
- Deterministic Repository Suite run `34566587055`;
- Validate organization control plane run `34566587054`;
- Heartbeat Worker Project validation run `34566587124`.

The branch advanced with explicit footer/handoff receipt gating and updated tests. Fresh exact-head validation is required before merge.

## Authority
Task/session close evidence is coordination only. WorkerCoordinator remains claim/fence authority; Interlock/InTr remains transition authority; TV/TVC remains credential authority; Master Records remains observed-reality/reconstruction authority; HB remains observability only; GitHub runtime authority remains NONE.

## Remaining
1. obtain exact-head validation after footer/handoff receipt gating;
2. repair any regression;
3. merge PR #1412 when green;
4. after merge, project the session-close invocation into any future product-specific UI emitter without changing the canonical ledger/evaluator semantics.

## Manual work
None.
