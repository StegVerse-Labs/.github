# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
Status: `ACTIVE / CHECKED_OUT / SOURCE INTEGRATION MERGED / EXISTING KV RUNTIME DEPENDENCIES BOUND / AUTHENTIC ADMITTED WRITE + EXACT READBACK PENDING`

## Objective
Project the canonical hash-linked Task Registry check-in/return event history into StegVerse sovereign KV custody while preserving exact event bytes/hashes, recent-session collision semantics, and all existing authority boundaries.

## Merged source integration
- `.github` PR #1425 merged at `b1668cd940ddb7a7180dc7e01583afaa19795ee3` after organization-control, Heartbeat, and deterministic repository-suite validation passed.
- `continuity-vault-kit` PR #211 merged at `700dba383c3c15f0bc98542729f10cf09dc27306` after Security Baseline, repository validation diagnostics, and KV Guardrails all passed.

The `.github` bridge preserves exact Task Registry `event_sha256` / predecessor lineage and accepts custody only when a returned `stegverse.task-registry-sovereign-kv-projection-receipt/v1` proves the same exact event hash was stored and binds provider-adapter, Interlock/InTr, and KV-instance references with `authority_effect=NONE`.

The continuity-vault-kit binding reuses `runtime/kv_storage_provider_adapter.py` and emits the existing canonical `stegverse.kv.storage-provider-operation-request/v1` with `operation=WRITE`, `object_ref=event_sha256`, `governance_state=PENDING_INTERLOCK_INTR`, SKAP credential reference required, and no credential material. Its result validator emits the `.github` projection receipt only after an ADMITTED/executed provider WRITE plus exact stored-event hash readback.

## Runtime dependency reconciliation
A repository-wide search found no resident consumer that independently executes `stegverse.kv.storage-provider-operation-request/v1`. continuity-vault-kit source explicitly still reports Google Drive CONNECT/VERIFY provider execution pending. Therefore this custody task does not create another provider executor.

The authentic provider-operation dependency is assigned to already-existing adjacent/canonical work:
- `KV-CONNECTION-REVALIDATION-WORKER-001` — owns provider connection/revalidation, existing Google Drive peer, SKAP credential reference, and authentic Interlock/InTr CONNECT/VERIFY execution work;
- `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` — owns authentic device/KV/SKAP/InTr roundtrip evidence required to prove the governed path rather than source-only receipts.

This Task Registry custody task consumes their admitted provider-operation capability once proven and adds the exact Task Registry event WRITE/readback predicate; it does not supersede or duplicate them.

## Branch-recovery incident
During initial continuity-vault-kit integration, three files were mistakenly written to default `main`. A feature branch was created from that state, all three accidental files were removed from default `main`, then the feature branch was reset to the restored clean `main` and the three intended PR files were recreated. PR #211 was reopened with a clean three-file diff and validated/merged. No runtime or custody claim derives from those transient repository commits.

## Authority invariants
Task Registry remains coordination only. WorkerCoordinator remains claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains credential authority. Master Records remains observed-reality/reconstruction authority. HB remains observability only. GitHub runtime authority remains NONE.

## Current unresolved predicate
`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

## Next
1. wait for/reuse authentic provider-operation capability from `KV-CONNECTION-REVALIDATION-WORKER-001` / `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` rather than creating a duplicate executor;
2. submit an exact Task Registry event through the merged continuity-vault-kit WRITE binding;
3. require ADMITTED Interlock/InTr + SKAP provider-operation receipt;
4. perform exact stored-event hash readback from the target sovereign KV instance;
5. feed the resulting projection receipt through `.github/scripts/project_task_registry_event_to_sovereign_kv.py`;
6. only after exact-hash custody is observed consider making sovereign KV projection required rather than optional for Task Registry durability.

## Manual work
None.
