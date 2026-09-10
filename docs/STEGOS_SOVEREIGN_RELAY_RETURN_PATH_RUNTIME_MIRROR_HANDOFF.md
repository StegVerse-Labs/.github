# StegOS Sovereign Relay Return Path Runtime Mirror Handoff

Updated: 2026-09-10

```text
goal_id: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
task_id: SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: RESIDENT_EXECUTION_WIRED / ARTIFACT_AUTODISCOVERY_MERGED / REFRESH_DISPATCH_MERGED / CONTROL_PLANE_SOURCE_PACKAGE_MERGED / DETERMINISTIC_REAL_RETURN_INTEGRATION_VERIFIED / LIVE_EXTERNAL_RETURN_PATH_RECEIPT_PENDING
credential_authority: TV/TVC
github_runtime_authority: NONE
heartbeat_execution_authority: false
worker_registration_merge: 6c4b1227579c7b561458bdf4b8b122df5985d059
artifact_autodiscovery_merge: db2d8095a549a3feee7f55d916c49e8e55dc6aa3
handoff_autodiscovery_reconciliation_merge: 679056bfe6d3624c49085133ef169931816f4ad1
refresh_to_targeted_dispatch_merge: e73e6b9a87cdcff7eb4ffa555d83f6a3b5fa7643
control_plane_source_package_merge: 52f29fbba0751787ceaca5f1c9022bdcb37338fb
public_source_package_gateway_merge: d4601f449743bb086ac2e9e38777b46b21ba8e27
stegos_round_trip_source_merge: dff05631a6bdab10311013c0da73339667867364
stegos_real_return_integration_merge: f90e8cfc9c9e0409dc74d2bb258d8500e5ca07ca
cosv: 50000000101000
```

## Primary proof target

The goal is the StegVerse-to-ephemeral-Stegos return loop, not the current-iPhone bootstrap lane:

```text
StegVerse organization/runtime
-> WorkerCoordinator independent task control
-> ephemeral StegOS relay EGRESS
-> real far-side HIL INGRESS_ADMITTED
-> durable ESRL return queue
-> Interlock same-key ingestion/dedupe
-> RETURN_PATH_VERIFIED
```

The current-iPhone/TestFlight path remains a separate bootstrap/portability lane and does not supersede this primary proof target.

## Resident execution

The existing WorkerCoordinator owns execution through:

```text
SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
adapter: process:stegos-sovereign-relay-return-path-v1
state: HANDOFF_READY
fresh fence required: >21
required_local_env: []
network_source_fetch_allowed: false
physical_additional_machine_required: false
third_party_runtime_required: false
```

The request is already present at `control/resident-execution-request.d/stegos-sovereign-relay-return-path-001.json` and the task-specific consumer is registered as `stegos_sovereign_relay_return_path` in the existing resident dispatcher. The request grants no execution, claim, fence, heartbeat, route, credential, transition, repository, or source-fetch authority.

## Deterministic real-return integration proof

StegOS PR #317 merged at `f90e8cfc9c9e0409dc74d2bb258d8500e5ca07ca` after StegOS CI run `34473723279` completed SUCCESS.

The added integration proof keeps only the socket/TLS hop deterministic. In one integrated call it executes the real:

```text
TVC-bound sovereign relay EGRESS executor
-> far-side HIL ACK binding
-> durable sovereign relay return processor
-> write-once ESRL return queue
-> Interlock same-key ingestion/dedupe
-> RETURN_PATH_VERIFIED
```

The proof discovered and repaired a real replay defect. Before PR #317, a repeated call with the same single-use EGRESS authorization correctly reused the persisted `TRANSPORT_ACCEPTED` EGRESS receipt, but the round-trip layer instantiated a fresh transport and then failed because no new `far_side_receipt` existed. That behavior would prevent deterministic reconstruction after a successful first send.

PR #317 now persists the verified far-side ACK evidence write-once under the authorization identity. On replay:

```text
persisted TRANSPORT_ACCEPTED EGRESS receipt
+ persisted verified far-side ACK evidence
-> no network retransmission
-> real return processor re-entry
-> same write-once return queue
-> same Interlock ingestion
-> RETURN_PATH_VERIFIED
```

The integration executes the same fencing identity twice and requires exactly one durable return-queue artifact and one Interlock ingestion artifact. The queue must declare `survives_compute_teardown=true` and `compute_provider_can_delete_expire_or_rewrite=false`; Interlock ingestion must keep `execute_consequence=false` and `canonical_transition_committed=false`.

This is stronger than the previous wiring-only round-trip test because EGRESS execution and the return processor are no longer monkeypatched. It remains deterministic source/runtime-logic evidence rather than an authentic external-network receipt because the socket/TLS hop is intentionally controlled by the test harness.

## Remaining runtime gate

The repository still does not contain:

`receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001.json`

with all terminal predicates:

```text
state=COMPLETED
transition_id=SOVEREIGN_RELAY_RETURN_PATH_VERIFIED
round_trip_result.state=RETURN_PATH_VERIFIED
round_trip_result.far_side_evidence_present=true
round_trip_result.durable_return_queue_verified=true
round_trip_result.interlock_ingestion_verified=true
round_trip_result.canonical_transition_committed=false
```

The first unresolved runtime boundary is therefore not relay-return logic anymore. It is authentic resident request consumption / real external transport execution from the existing sovereign runtime. The canonical request exists, and the consumer is registered, but no `receipts/sovereign-host/stegos-sovereign-relay-return-path-request-consumption.latest.json` is currently in repository custody.

## Next execution order

```text
existing sovereign resident/ephemeral StegOS runtime
-> existing resident dispatcher visits stegos_sovereign_relay_return_path
-> request consumer invokes refresh_and_execute_resident_task.py
-> WorkerCoordinator admits fresh fence >21
-> exact already-local EGRESS binding/authorization/payload autodiscovery
-> real HIL ingress transport
-> persisted far-side ACK evidence
-> durable return queue
-> Interlock ingestion
-> terminal RETURN_PATH_VERIFIED receipt
```

Do not reopen relay materialization, allocator, browser, or TestFlight work to satisfy this proof unless a later observed runtime failure specifically binds to those surfaces.

## Authority invariants

```text
StegVerse primary: true
credential authority: TV/TVC
GitHub token runtime authority: NONE
HeartBeat execution authority: false
canonical transition authority: Interlock/InTr
second user-operated machine required: false
hosted execution fallback: false
```
