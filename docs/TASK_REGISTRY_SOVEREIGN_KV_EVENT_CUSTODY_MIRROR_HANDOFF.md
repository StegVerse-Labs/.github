# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
COSV: not established in the canonical task record
Status: `ACTIVE / CHECKED_OUT / SOURCE INTEGRATION MERGED / REUSABLE COMPONENT COMPOSITION DECLARED / AUTHENTIC ADMITTED WRITE + EXACT READBACK PENDING`

## Objective

Project canonical hash-linked Task Registry session events into provider-neutral StegVerse sovereign KV custody while preserving exact event hashes, collision semantics, and existing authority boundaries.

The Goal Task remains valid. Reusable Task Component Model reconciliation changes how the process is composed; it does not rename, restart, duplicate, or close the Goal Task.

## Canonical source state

- `.github` PR #1425 merged at `b1668cd940ddb7a7180dc7e01583afaa19795ee3`.
- `continuity-vault-kit` PR #211 merged at `700dba383c3c15f0bc98542729f10cf09dc27306`.
- `.github` PR #1452 merged at `daf123b00462ff824dc4cb0beff6972d7eeea5b2`, binding runtime execution to existing owners instead of creating a provider executor.
- `.github` PR #1470 merged at `2798059fc750a64e1cc3a716c00e3c58ede9f67f`, adding the non-authorizing runtime intake contract.
- `.github` PR #1490 merged at `59e32449715fef07e82fd395d22b6112197da6f7` after exact-head Deterministic Repository Suite `34635583389`, Heartbeat Worker Project `34635583403`, and organization-control `34635583406` all passed.
- `.github` PR #1484 merged at `782e5a26c7cc41a3253ad3648e7e7ea17ea767b0`, superseding the conflicted #1467 coordination path and registering `TVC-RECIPIENT-ADMISSION-SIGNING-CUSTODY-001` as an adjacent dependency of the Device/KV/SKAP owner.
- PR #1495 remained open and exact-head green at `949d5906327183f7fd0c21429a11ea34f09e77b8`, but its branch predates the canonical Reusable Task Component Model. Its useful coordination corrections are carried forward here instead of extending that stale branch.

The `.github` bridge preserves exact `event_sha256` / predecessor lineage. The `continuity-vault-kit` binding remains the task-specific translator into the existing provider-neutral storage operation contract. Neither is a runtime authority.

## Reusable Task Component Model reconciliation

Canonical model: `data/reusable-task-component-model.json`
Decomposition policy: `data/reusable-task-component-decomposition-policy.json`
Transport contract: `data/reusable-transport-component-contract.json`
Goal profile: `data/goal-task-transport-profiles/TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001.json`

This flow crosses multiple repositories and authority owners, contains repeated governed request/response evidence, has independently provable stages, and previously presented a growing linear handoff. It therefore satisfies the policy's `13+` stop-scope-growth condition and must be represented as reusable components before more bespoke orchestration is added.

No new reusable component is required.

### Required component map

| Component | Existing owner / implementation | Inputs | Outputs | Preconditions | Expected evidence | Cardinality | Requirement |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `RTC-MANIFEST-001` Manifest Intake and Binding | reusable transport contract + existing runtime intake contract | live canonical Task Registry event, exact event hash/predecessor, target KV/provider parameters | manifest-bound invocation inputs | canonical event, task identity, required evidence declared | exact input/hash binding | once | required |
| `RTC-GOVERNED-PROCESSING-002` Governed Processing | existing runtime owners; Interlock/InTr for state transitions | bound provider-write intent | bounded governed processing result | required execution owner and applicable admission path present | governed processing/admission evidence | once | required |
| `RTC-ROUNDTRIP-003` Governed Round Trip | existing provider path | provider WRITE request; later exact readback request | provider result and readback result | applicable admission/session state | chained request/response evidence | twice: admitted provider write + exact hash readback | required/repeatable |
| `RTC-EVIDENCE-CUSTODY-004` Evidence Custody and Reconstruction | Master Records | accepted runtime receipts and exact readback evidence | durable observed-reality custody/reconstruction | authentic component evidence exists | Master Records custody/reconstruction evidence | once terminally | required |
| `RTC-STEGVERSE-EGRESS-007` StegVerse-side Final Egress Transition | Interlock/InTr | admitted local provider-operation candidate | egress candidate | contemporaneous transition decision | egress transition receipt | as required by provider path | required |
| `RTC-INTERLOCK-INTR-TRANSPORT-008` Interlock/InTr Transport | Interlock/InTr | governed provider packets | governed packet movement / transition receipts | exact transition admission | authentic ingress/egress transport evidence | repeatable | required |
| `RTC-FARSIDE-FINAL-009` Far-side Final Transition | existing provider execution owner | admitted provider WRITE | stored provider object / operation result | provider/session prerequisites satisfied | authentic provider execution receipt | once for target write | required |

Not selected: `RTC-PUBLISHER-005` and `RTC-SDK-RETURN-006`. This Goal Task does not publish a public artifact or assemble an SDK response.

## Existing non-transport components reused

- Runtime/execution materialization: existing runtime owners only; use the reusable task-ephemeral construct contract only where their declared runner path requires it. No second runner plane is created.
- Credential/provider release: TV/TVC.
- User verification: KV/SKAP Vault only.
- Provider adapter: `StegVerse-Labs/continuity-vault-kit/runtime/task_registry_event_sovereign_kv_binding.py` remains a task-specific translator into the reusable provider/transport path.
- Task Registry projection: `scripts/project_task_registry_event_to_sovereign_kv.py` remains task-specific exact-hash acceptance logic.
- Evidence validation: retain the existing fail-closed exact-event-hash validator; do not duplicate it in transport machinery.
- Observed reality/custody/reconstruction: Master Records.

## Duplicate orchestration retired or superseded

The prior six-step handoff sequence is preserved as historical/runtime intent but is no longer the primary architecture representation. It is superseded conceptually by the selected reusable components plus task-specific parameters and completion predicates.

Do not add:

- a task-specific provider executor;
- duplicate Interlock/InTr transport;
- duplicate credential/session resolution;
- duplicate custody/reconstruction machinery;
- device-local user verification;
- a second user-operated device requirement.

Historical evidence and provenance remain intact.

## Existing execution owners and dependencies

- `KV-CONNECTION-REVALIDATION-WORKER-001`: existing provider execution/admission lineage. Remaining independent native publication work may have successor ownership, but this Goal Task does not inherit or recreate that publication work.
- `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`: existing Device/KV/SKAP/InTr evidence lineage.
- `TVC-RECIPIENT-ADMISSION-SIGNING-CUSTODY-001`: adjacent credential-path dependency registered by merged PR #1484.
- `TASK-REGISTRY-CHECKIN-EVENT-HISTORY-001`: source event-history dependency.
- `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`: parent Goal Task.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed state-transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes, never user verifiers or user-identity authorities.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat: synchronization, timing, freshness, liveness, correlation, and observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

Runtime subject binding, node identity, Secure Enclave identity, transport identity, and device identity do not become user-verification authority.

## Current runtime/evidence state

Source integration and runtime-intake source are complete. Componentization does not upgrade evidence. No authentic provider WRITE plus exact Task Registry event-hash readback is established by the currently checked canonical evidence.

Current first unresolved predicate:

`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

## Goal-specific completion predicates after componentization

1. one live canonical `stegverse.task-registry-checkin-event/v1` is bound with exact `event_sha256` and predecessor lineage;
2. any execution-owner-required WorkerCoordinator claim/fence is authentic;
3. Interlock/InTr authentically admits the exact provider WRITE transition;
4. applicable TV/TVC + KV/SKAP session evidence is authentic and preserves authority separation;
5. the existing provider owner executes the WRITE with `object_ref` equal to the canonical event hash;
6. exact stored-event SHA-256 readback equals the canonical event hash;
7. `stegverse.task-registry-sovereign-kv-projection-receipt/v1` is accepted by the existing fail-closed projection logic;
8. required Master Records custody/reconstruction is authentically observed before terminal completion is claimed.

## Next admissible work

1. validate and merge this component-composition reconciliation only if exact-head required repository lanes are green;
2. retire/supersede stale PR #1495 after the replacement reconciliation is accepted;
3. re-observe the existing provider and Device/KV/SKAP owners for authentic component evidence;
4. if authentic admitted provider WRITE evidence exists, consume it through the existing component composition and require exact hash readback;
5. do not create a duplicate executor, transport path, credential handler, or synthetic receipt if the runtime boundary remains unsatisfied.

## README

Repository README was reviewed against the canonical Reusable Task Component Model. The model already owns the repository-level architecture projection; this consumer reconciliation does not materially change repository function, so no duplicate README prose is added.

## Manual work

None.
