# Task Registry Sovereign KV Event Custody Mirror Handoff

Goal Task ID: `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`
Parent: `TASK-REGISTRY-SESSION-RETURN-ORCHESTRATION-001`
Canonical issue: `StegVerse-Labs/.github#1423`
COSV: not established in the canonical task record
Status: `ACTIVE / CHECKED_OUT / SOURCE INTEGRATION MERGED / REUSABLE COMPONENT COMPOSITION MERGED / CURRENT VERIFICATION SELECTOR BOUND / AUTHENTIC ADMITTED WRITE + EXACT READBACK PENDING`

## Objective

Project canonical hash-linked Task Registry session events into provider-neutral StegVerse sovereign KV custody while preserving exact event hashes, predecessor ordering, collision semantics, and authority boundaries.

The Goal Task remains valid. Reusable component composition changes how the process is expressed; it does not rename, restart, duplicate, or close the Goal Task.

## Canonical source state

- `.github` PR #1425 merged at `b1668cd940ddb7a7180dc7e01583afaa19795ee3`.
- `continuity-vault-kit` PR #211 merged at `700dba383c3c15f0bc98542729f10cf09dc27306`.
- `.github` PR #1452 merged at `daf123b00462ff824dc4cb0beff6972d7eeea5b2`, binding runtime execution to existing owners instead of creating a provider executor.
- `.github` PR #1470 merged at `2798059fc750a64e1cc3a716c00e3c58ede9f67f`, adding the non-authorizing runtime intake contract.
- `.github` PR #1490 merged at `59e32449715fef07e82fd395d22b6112197da6f7` after all three required exact-head validation lanes passed.
- `.github` PR #1484 merged at `782e5a26c7cc41a3253ad3648e7e7ea17ea767b0`, registering the adjacent recipient-admission signing-custody dependency.
- `.github` PR #1671 merged at `64c388bdd374adcc81bec50ec21d4987624e5362`, reconciling this Goal Task to the canonical Reusable Task Component Model after exact-head organization-control `34730890300`, deterministic-suite `34730890327`, and Heartbeat `34730890315` all passed.
- stale PR #1495 is closed unmerged as superseded by #1671; its useful coordination corrections are preserved in current canonical source.

The `.github` projection bridge preserves exact `event_sha256` and predecessor lineage. The continuity-vault-kit binding remains the task-specific translator into the existing provider-neutral storage-operation path. Neither owns runtime authority.

## Reusable component composition

Canonical model: `data/reusable-task-component-model.json`
Transport contract: `data/reusable-transport-component-contract.json`
Evidence-validation contract: `data/reusable-evidence-validation-component-contract.json`
Goal profile: `data/goal-task-transport-profiles/TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001.json`

Required components:

| Component | Owner / implementation | Purpose | Evidence / precondition | Cardinality |
| --- | --- | --- | --- | --- |
| `RTC-MANIFEST-001` | reusable transport contract + runtime intake | bind one live Task Registry event, exact hash/predecessor, provider/KV target | exact manifest/input binding | once |
| `RTC-GOVERNED-PROCESSING-002` | existing runtime owners + Interlock/InTr | bounded governed processing of the provider operation | authentic applicable admission | once |
| `RTC-ROUNDTRIP-003` | existing provider path | provider WRITE, then exact stored-event readback | chained authentic request/response receipts | twice |
| `RTC-EVIDENCE-CUSTODY-004` | Master Records | terminal custody and reconstruction | accepted authentic component evidence | once terminally |
| `RTC-STEGVERSE-EGRESS-007` | Interlock/InTr | governed local egress candidate | contemporaneous transition evidence | as required |
| `RTC-INTERLOCK-INTR-TRANSPORT-008` | Interlock/InTr | governed packet movement | authentic ingress/egress receipts | repeatable |
| `RTC-FARSIDE-FINAL-009` | existing provider execution owner | actual far-side provider WRITE | authentic provider execution receipt | once for target write |
| `RTC-EVIDENCE-CURRENT-SELECTOR-010` | KV/SKAP verification domain + TV/TVC admitted-receipt semantics | select exactly one current applicable already-verified KV/SKAP record for this operation | CURRENT_VERIFIED binding, exact context/digest match, exactly one candidate | when provider/session path requires current user-verification evidence |

`RTC-EVIDENCE-CURRENT-SELECTOR-010` is non-authorizing. It creates no verification, performs no device verification, returns no raw secrets, does not select latest-by-time, and may retry only when authoritative current binding or candidates change.

Not selected: `RTC-PUBLISHER-005` and `RTC-SDK-RETURN-006`; this Goal Task neither publishes a public artifact nor assembles an SDK response.

## Existing owners reused

- provider execution/admission lineage: `KV-CONNECTION-REVALIDATION-WORKER-001`;
- Device/KV/SKAP/InTr lineage: `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` until a successor is canonical on `main`;
- candidate runtime successor: `STEGOS-DEVICE-KV-SKAP-AUTHENTIC-RUNTIME-002`, tracked by issue #1500 and source PR #1519;
- credential/provider release: TV/TVC;
- sole user-verification authority: KV/SKAP Vault;
- custody/reconstruction: Master Records;
- provider translator: `StegVerse-Labs/continuity-vault-kit/runtime/task_registry_event_sovereign_kv_binding.py`;
- exact-hash acceptance: `scripts/project_task_registry_event_to_sovereign_kv.py`.

PR #1519 exact head `a3c66f7a0a17ca941be72cc63f2cb9d11134b686` passed organization-control `34637852384`, deterministic-suite `34637852390`, and Heartbeat `34637852446`, but the PR remains unmerged/noncanonical on current `main`. This Goal Task therefore does not replace its canonical dependency with the successor yet.

## Duplicate orchestration prohibited

Do not add a task-specific provider executor, duplicate Interlock/InTr transport, duplicate credential/session handler, task-specific current-verification selector, duplicate custody/reconstruction path, device-local user verifier, or second user-operated device requirement.

Historical source and evidence remain provenance; componentization does not upgrade them into runtime evidence.

## Authority invariants

- Task Registry: coordination only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed state-transition/admission authority.
- TV/TVC: credential/provider/release authority.
- KV/SKAP Vault: sole user-verification authority.
- StegOS devices: interchangeable transport/execution nodes, never user verifiers.
- Master Records: observed-reality custody/reconstruction.
- HeartBeat: timing, freshness, liveness, correlation, observability only.
- GitHub: source/evidence coordination only; runtime authority `NONE`.

Runtime subject, node, Secure Enclave, transport, or device identity never becomes user-verification authority.

## Runtime/evidence state

Fresh canonical source search still finds the sovereign-KV projection receipt schema only in source/contracts/tests/handoffs, not an authentic runtime receipt. No authentic provider WRITE plus exact Task Registry event-hash readback has been established. Component reuse and green CI do not change that evidence class.

Current first unresolved predicate:

`AUTHENTIC_ADMITTED_PROVIDER_WRITE_AND_EXACT_EVENT_HASH_READBACK_FROM_SOVEREIGN_KV`

## Goal-specific completion predicates

1. one live canonical `stegverse.task-registry-checkin-event/v1` is bound with exact `event_sha256` and predecessor lineage;
2. required WorkerCoordinator claim/fence is authentic;
3. Interlock/InTr authentically admits the exact provider WRITE transition;
4. applicable TV/TVC + KV/SKAP evidence is authentic;
5. where current verification selection is required, `RTC-EVIDENCE-CURRENT-SELECTOR-010` selects exactly one matching CURRENT_VERIFIED record without minting authority;
6. existing provider owner executes WRITE with `object_ref` equal to canonical event hash;
7. exact stored-event SHA-256 readback equals canonical event hash;
8. `stegverse.task-registry-sovereign-kv-projection-receipt/v1` is accepted by the existing fail-closed projection logic;
9. required Master Records custody/reconstruction is authentically observed before terminal completion.

## Next admissible work

1. merge the current-selector binding only after exact-head required repository validation is green;
2. continue observing the canonical existing runtime owners for an authentic admitted provider WRITE;
3. if the Device/KV/SKAP successor becomes canonical, rebind this Goal Task to that canonical owner instead of the retired predecessor lineage;
4. on authentic WRITE evidence, perform the second `RTC-ROUNDTRIP-003` exact-hash readback and pass the existing fail-closed projection validator;
5. require Master Records custody/reconstruction before any terminal completion claim.

## README

README was reviewed. The canonical Reusable Task Component Model and evidence-validation family already define the repository-level architecture; this consumer binding does not materially change repository function, so no additional README prose is required.

## Manual work

None.
