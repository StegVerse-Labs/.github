# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
Status: `ACTIVE / CHECKED_OUT / SOURCE INTEGRATION MERGED / RUNTIME INTAKE CONTRACT IMPLEMENTED / FRESH EVIDENCE OBSERVATION RECORDED / AUTHENTIC ADMITTED WRITE + EXACT READBACK PENDING`

## Objective
Project canonical hash-linked Task Registry session events into StegVerse sovereign KV custody while preserving exact event hashes, collision semantics, and existing authority boundaries.

## Merged source integration
- `.github` PR #1425 merged at `b1668cd940ddb7a7180dc7e01583afaa19795ee3` after all three required validation lanes passed.
- `continuity-vault-kit` PR #211 merged at `700dba383c3c15f0bc98542729f10cf09dc27306` after Security Baseline, repository validation diagnostics, and KV Guardrails passed.
- `.github` PR #1452 merged at `daf123b00462ff824dc4cb0beff6972d7eeea5b2`, canonically binding runtime execution to the already-existing KV tasks rather than creating a duplicate provider executor.
- `.github` PR #1470 merged at `2798059fc750a64e1cc3a716c00e3c58ede9f67f`, adding the non-authorizing runtime intake contract for one live exact-hash Task Registry event.

The `.github` bridge preserves exact `event_sha256` / predecessor lineage and accepts custody only when a `stegverse.task-registry-sovereign-kv-projection-receipt/v1` proves the same exact event hash was stored with provider-adapter, Interlock/InTr, and KV-instance references and `authority_effect=NONE`.

The continuity-vault-kit binding reuses the canonical `stegverse.kv.storage-provider-operation-request/v1` contract with `operation=WRITE`, `object_ref=event_sha256`, `governance_state=PENDING_INTERLOCK_INTR`, SKAP reference required, and no credential material. Its result validator emits the Task Registry projection receipt only after an ADMITTED/executed provider WRITE plus exact stored-event SHA-256 readback.

## Runtime intake contract
`data/task-registry-sovereign-kv-runtime-intake-contract.json` defines the handoff from this custody task into the existing runtime owners. It requires one live canonical `stegverse.task-registry-checkin-event/v1`, its exact `event_sha256` and predecessor hash, target KV instance/set, and provider ID. It rejects fixture/synthetic events and repository/CI-only evidence.

Execution ownership is unchanged:
- `KV-CONNECTION-REVALIDATION-WORKER-001` owns authentic provider execution/admission and the existing Google Drive/provider lane;
- `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` owns authentic Device/KV/SKAP/InTr evidence;
- this task owns only Task Registry event custody projection and exact-hash readback acceptance.

The intake contract creates no provider executor, grants no execution authority, and carries no credentials.

## Fresh evidence observation — 2026-09-11
`docs/TASK_REGISTRY_SOVEREIGN_KV_EVENT_CUSTODY_EVIDENCE_OBSERVATION_2026-09-11.md` records the latest checked evidence state.

- `.github` PR #1467 for `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` remains open at `fe7ca113bdd20d5d6d9b2d92c33a67b85dfa9b99`; its three validation lanes are green. It records TVC #408 / StegOS #343 authenticated-admission source progress while production TVC signing-key custody and canonical public trust-anchor binding remain authentic runtime predicates.
- `continuity-vault-kit` has no newer provider-execution PR beyond the merged source contracts; current provider-operation source still distinguishes intent/persistence from actual remote I/O and admission.
- Connected Drive searches for the provider-operation receipt schema, sovereign-KV projection receipt schema, `kvprov_`, this Goal Task ID, and `provider-state` found no authentic Task Registry custody/provider-operation receipt. The only `provider-state` match was an older project handoff, not runtime evidence.

This observation changes no authority or runtime state. It confirms only that the authentic admitted provider WRITE plus exact event-hash readback remains unmaterialized in the checked evidence surfaces.

## Current runtime state inherited from existing owners
`KV-CONNECTION-REVALIDATION-WORKER-001` remains machine-owned with resident ingress observed and cloud provider execution pending. `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` remains ACTIVE/CHECKED_OUT with source integration advancing but authentic runtime custody/readback predicates still open. This custody task must not collide with or replace either owner.

## Authority invariants
Task Registry remains coordination only. WorkerCoordinator remains claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains credential authority. Master Records remains observed-reality/reconstruction authority. HB remains observability only. GitHub runtime authority remains NONE.

## Current unresolved predicate
`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

## Next
1. consume a live canonical Task Registry event through the runtime intake contract only when the existing provider path admits execution;
2. bind its exact hash as the canonical provider WRITE `object_ref`;
3. require authentic ADMITTED Interlock/InTr + SKAP provider-operation evidence from the existing execution owner;
4. perform exact stored-event SHA-256 readback from the target sovereign KV;
5. feed the resulting receipt through `.github/scripts/project_task_registry_event_to_sovereign_kv.py`;
6. close this goal only after exact-hash sovereign KV custody is observed and reconstructable.

## Manual work
None.
