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
- `.github` PR #1490 validated at exact head `00827874a0aa5b203bdaa7374450d074b61bfbc4` and merged at `59e32449715fef07e82fd395d22b6112197da6f7` after deterministic-suite run `34635583389`, Heartbeat run `34635583403`, and organization-control run `34635583406` all succeeded.

The `.github` bridge preserves exact `event_sha256` / predecessor lineage and accepts custody only when a `stegverse.task-registry-sovereign-kv-projection-receipt/v1` proves the same exact event hash was stored with provider-adapter, Interlock/InTr, and KV-instance references and `authority_effect=NONE`.

The continuity-vault-kit binding reuses the canonical `stegverse.kv.storage-provider-operation-request/v1` contract with `operation=WRITE`, `object_ref=event_sha256`, `governance_state=PENDING_INTERLOCK_INTR`, SKAP reference required, and no credential material. Its result validator emits the Task Registry projection receipt only after an ADMITTED/executed provider WRITE plus exact stored-event SHA-256 readback.

## Runtime intake contract
`data/task-registry-sovereign-kv-runtime-intake-contract.json` defines the handoff from this custody task into the existing runtime owners. It requires one live canonical `stegverse.task-registry-checkin-event/v1`, its exact `event_sha256` and predecessor hash, target KV instance/set, and provider ID. It rejects fixture/synthetic events and repository/CI-only evidence.

Execution ownership is unchanged:
- the provider-execution lineage rooted at `KV-CONNECTION-REVALIDATION-WORKER-001` owns authentic provider execution/admission rather than this custody task;
- `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` owns authentic Device/KV/SKAP/InTr evidence;
- this task owns only Task Registry event custody projection and exact-hash readback acceptance.

The intake contract creates no provider executor, grants no execution authority, and carries no credentials.

## Fresh evidence observation — 2026-09-11
`docs/TASK_REGISTRY_SOVEREIGN_KV_EVENT_CUSTODY_EVIDENCE_OBSERVATION_2026-09-11.md` records the latest checked evidence state.

- `.github` PR #1490 is merged only after all three exact-head validation lanes passed; those repository checks do not constitute runtime custody proof.
- The earlier Device/KV/SKAP coordination PR #1467 was superseded by `.github` PR #1484. PR #1484 merged at `782e5a26c7cc41a3253ad3648e7e7ea17ea767b0`, registering `TVC-RECIPIENT-ADMISSION-SIGNING-CUSTODY-001` because production TVC recipient-admission signing custody remains an authentic runtime condition; TVC issue #409 owns that bounded condition.
- `KV-CONNECTION-REVALIDATION-WORKER-001` reached its parent-goal ceiling and transferred genuinely remaining native publication work to `SITE-PUBLICATION-NATIVE-RUNTIME-EXECUTION-001`; that transfer does not satisfy this Task Registry custody predicate and is not provider WRITE/readback evidence.
- Connected Drive searches for `task-registry-sovereign-kv-projection-receipt` and `ADMITTED provider WRITE event_sha256` returned no matching evidence artifact.

This observation changes no authority or runtime state. It confirms only that the authentic admitted provider WRITE plus exact event-hash readback remains unmaterialized in the checked evidence surfaces.

## Current runtime state inherited from existing owners
The provider-execution lineage still has unresolved authentic remote/provider execution conditions, while `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` remains ACTIVE/CHECKED_OUT with authentic runtime custody/readback predicates open. This custody task must not collide with or replace either execution owner or successor.

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

## README review
`README.md` was reviewed during this reconciliation. The repository-level authority and Canonical Work principles remain accurate; this change adds no new organization-level principle requiring README prose changes.

## Manual work
None.
