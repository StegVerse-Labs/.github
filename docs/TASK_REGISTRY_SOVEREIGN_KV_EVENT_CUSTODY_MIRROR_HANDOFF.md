# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
Status: `ACTIVE / CHECKED_OUT / PROVIDER-NEUTRAL CUSTODY BRIDGE IMPLEMENTED / AUTHENTIC KV ADAPTER RECEIPT PENDING`

## Objective
Project the canonical hash-linked Task Registry check-in/return event history into StegVerse sovereign KV custody while preserving exact event bytes/hashes, recent-session collision semantics, and all existing authority boundaries.

## Merged prerequisites
- PR #1390 merged hash-linked Task Registry event history and recent-return collision windows.
- PR #1412 merged canonical session-close/footer gating on a successful RETURNED/CHECK_OUT receipt.

## Implemented in this child
- `data/canonical-task-records/TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001.json`
- `data/task-registry-sovereign-kv-event-custody-contract.json`
- `scripts/project_task_registry_event_to_sovereign_kv.py`
- `tests/test_task_registry_sovereign_kv_event_custody.py`

The projection bridge accepts an exact canonical `stegverse.task-registry-checkin-event/v1` event, preserves its `event_sha256` and predecessor hash, builds a provider-neutral sovereign-KV projection request, and can invoke a configured adapter command. Custody is accepted only when the returned receipt binds the exact event hash as both `event_sha256` and `stored_event_sha256`, declares `custody_class=STEGVERSE_SOVEREIGN_KV`, provides `provider_adapter_ref`, `interlock_intr_receipt_ref`, and `kv_instance_ref`, and retains `authority_effect=NONE`.

The bridge may also emit request-only material for an external governed adapter. Missing or malformed receipt fails closed and does not invent sovereign KV custody.

## Authority invariants
Task Registry remains coordination only. WorkerCoordinator remains claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains credential authority. Master Records remains observed-reality/reconstruction authority. HB remains observability only. GitHub runtime authority remains NONE.

## Current unresolved predicate
`PROVIDER_NEUTRAL_SOVEREIGN_KV_PROJECTION_RECEIPT_BOUND_TO_EXACT_EVENT_HASH`

## Next
1. validate this initial provider-neutral bridge exact head;
2. reconcile the bridge with the existing StegOS / continuity-vault-kit Interlock/InTr provider-adapter path rather than creating a second adapter stack;
3. obtain an authentic projection receipt from an admitted sovereign KV target;
4. prove exact event hash readback from KV custody;
5. only then consider making sovereign KV projection required rather than optional for Task Registry event durability.

## Manual work
None.
