# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
Status: `ACTIVE / CHECKED_OUT / PROVIDER-NEUTRAL CUSTODY BRIDGE GREEN / CONTINUITY-VAULT-KIT GOVERNED WRITE BINDING OPEN / AUTHENTIC ADMITTED WRITE + EXACT READBACK PENDING`

## Objective
Project the canonical hash-linked Task Registry check-in/return event history into StegVerse sovereign KV custody while preserving exact event bytes/hashes, recent-session collision semantics, and all existing authority boundaries.

## Merged prerequisites
- PR #1390 merged hash-linked Task Registry event history and recent-return collision windows.
- PR #1412 merged canonical session-close/footer gating on a successful RETURNED/CHECK_OUT receipt.

## .github provider-neutral bridge
PR `StegVerse-Labs/.github#1425` implements:
- `data/canonical-task-records/TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001.json`
- `data/task-registry-sovereign-kv-event-custody-contract.json`
- `scripts/project_task_registry_event_to_sovereign_kv.py`
- `tests/test_task_registry_sovereign_kv_event_custody.py`

Exact head `136853c4852c7faa0b99af2ad1e8627635055d7b` passed:
- organization-control run `34567358894`;
- Heartbeat validation run `34567358856`;
- deterministic repository suite run `34567358903`.

The bridge preserves canonical Task Registry `event_sha256` / predecessor lineage and accepts custody only when a returned `stegverse.task-registry-sovereign-kv-projection-receipt/v1` proves the same exact event hash was stored and binds provider-adapter, Interlock/InTr, and KV-instance references with `authority_effect=NONE`.

## Existing KV path reconciliation
The existing reusable storage path was identified rather than duplicated:
- `StegVerse-Labs/continuity-vault-kit/runtime/kv_storage_provider_adapter.py` owns provider-neutral `stegverse.kv.storage-provider-operation-request/v1` for `CONNECT`, `VERIFY`, `READ`, `WRITE`, `SYNC`, and `DISCONNECT`, with `PENDING_INTERLOCK_INTR`, SKAP-only credential semantics, and no provider execution authority.
- `StegVerse-Labs/continuity-vault-kit/runtime/kv_provider_operation_store.py` persists pending requests and only applies already-ADMITTED provider results carrying Interlock, InTr, SKAP, and provider-result evidence.
- `StegVerse-Labs/StegOS/stegos/kv_readiness_intr_delivery.py` demonstrates strict exact-payload InTr receipt validation without granting provider or execution authority.

Cross-repo PR `StegVerse-Labs/continuity-vault-kit#211` now adds `runtime/task_registry_event_sovereign_kv_binding.py`, tests, and its mirror handoff. It converts the Task Registry projection request into the existing canonical provider `WRITE` request with `object_ref=event_sha256`, `governance_state=PENDING_INTERLOCK_INTR`, SKAP reference required, and no credential material. Its result validator emits the `.github` projection-receipt schema only after an ADMITTED/executed WRITE receipt plus exact stored-event SHA-256 readback.

During creation of the continuity-vault-kit branch, three files were accidentally written to default `main`; all three were subsequently removed from `main`, restoring default-branch content before PR #211 was opened. The implementation is preserved on the feature branch. No runtime/custody claim derives from those transient repository commits.

## Authority invariants
Task Registry remains coordination only. WorkerCoordinator remains claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains credential authority. Master Records remains observed-reality/reconstruction authority. HB remains observability only. GitHub runtime authority remains NONE.

## Current unresolved predicate
`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

## Next
1. validate continuity-vault-kit PR #211 exact head and repair any regression;
2. merge #211 only if green;
3. bind the provider WRITE request to an existing admitted Interlock/InTr + SKAP runtime path rather than creating a new executor;
4. obtain an authentic provider WRITE receipt and exact stored-event hash readback from a sovereign KV target;
5. feed the resulting projection receipt to `.github/scripts/project_task_registry_event_to_sovereign_kv.py`;
6. only after exact-hash custody is observed consider making sovereign KV projection required rather than optional for Task Registry durability.

## Manual work
None.
