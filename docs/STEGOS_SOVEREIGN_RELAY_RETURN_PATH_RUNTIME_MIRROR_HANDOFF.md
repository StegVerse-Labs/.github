# StegOS Sovereign Relay Return Path Runtime Mirror Handoff

Updated: 2026-09-10

```text
goal_id: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
task_id: SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: RESIDENT_EXECUTION_WIRED / ARTIFACT_AUTODISCOVERY_MERGED / REFRESH_DISPATCH_MERGED / CONTROL_PLANE_SOURCE_PACKAGE_MERGED / REAL_LOOPBACK_TLS_RETURN_PATH_VERIFIED / EPHEMERAL_LIFECYCLE_HARDENED / LIVE_EXTERNAL_RETURN_PATH_RECEIPT_PENDING
credential_authority: TV/TVC
github_runtime_authority: NONE
heartbeat_execution_authority: false
worker_registration_merge: 6c4b1227579c7b561458bdf4b8b122df5985d059
artifact_autodiscovery_merge: db2d8095a549a3feee7f55d916c49e8e55dc6aa3
refresh_to_targeted_dispatch_merge: e73e6b9a87cdcff7eb4ffa555d83f6a3b5fa7643
control_plane_source_package_merge: 52f29fbba0751787ceaca5f1c9022bdcb37338fb
stegos_round_trip_source_merge: dff05631a6bdab10311013c0da73339667867364
stegos_real_return_integration_merge: f90e8cfc9c9e0409dc74d2bb258d8500e5ca07ca
stegos_real_loopback_tls_merge: 1b2abfe8290da3d4e864af6419f2828b59b425aa
ephemeral_lifecycle_hardening_merge: 252b9767b68bcd270f7c8c97ba665c80f951fe65
cosv: 50000000101000
```

## Primary proof target

```text
StegVerse organization/runtime
-> WorkerCoordinator independent task control
-> ephemeral StegOS relay EGRESS
-> HIL INGRESS_ADMITTED
-> durable ESRL return queue
-> Interlock same-key ingestion/dedupe
-> RETURN_PATH_VERIFIED
```

The current-iPhone/TestFlight lane is separate bootstrap/portability work and does not block this proof.

## Resident execution

The canonical request exists at `control/resident-execution-request.d/stegos-sovereign-relay-return-path-001.json`. Its consumer is registered as `stegos_sovereign_relay_return_path` in the existing resident dispatcher. Materialization copies the complete `control/` and `workers/` trees, so the request and consumer are carried into ephemeral sovereign runtimes without creating a new scheduler or runtime owner.

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

Mutable runtime receipts are intentionally excluded from source propagation. Therefore absence of a request-consumption receipt in GitHub repository custody is not evidence that a resident runtime did not consume the request; runtime observation must be taken from the resident/ephemeral runtime state itself.

## Real integrated return proof

StegOS PR #317 merged `f90e8cfc9c9e0409dc74d2bb258d8500e5ca07ca` after CI run `34473723279` passed. It removed the previous wiring-only gap by exercising the real EGRESS executor, ACK binding, durable return processor, write-once ESRL queue, and Interlock ingestion in one call.

That proof exposed and repaired a replay defect: a replayed single-use `TRANSPORT_ACCEPTED` EGRESS receipt had no newly populated transport object from which to recover the far-side ACK. The round-trip layer now persists verified far-side evidence write-once and reuses it on replay, so reconstruction does not retransmit an already-consumed authorization.

## Real HTTPS/TLS loop proof

StegOS PR #318 merged `1b2abfe8290da3d4e864af6419f2828b59b425aa` after StegOS CI run `34474184074` completed SUCCESS.

This closes the last synthetic transport step in the deterministic loop proof. The test starts an actual loopback HTTPS peer and exercises:

```text
real TLS socket
-> certificate trust validation
-> exact certificate SHA-256 pin
-> actual HTTP POST of opaque relay bytes
-> HIL-style HTTP 202 + INGRESS_ADMITTED JSON receipt
-> real EGRESS execution receipt
-> real ACK binding
-> persisted far-side evidence
-> write-once durable ESRL return queue
-> real Interlock ingestion/dedupe
-> RETURN_PATH_VERIFIED
```

A second identical call is required to make zero additional HTTP POSTs. It must reuse the persisted single-use EGRESS receipt and far-side ACK evidence and return the identical durable/Interlock result.

## Ephemeral lifecycle hardening

`.github` PR #1318 merged `252b9767b68bcd270f7c8c97ba665c80f951fe65` after organization-control, deterministic-repository, and Heartbeat Worker Project validation all passed.

This closes the previously recorded August 18 release-blocking environment-boundary finding against `scripts/restart_sovereign_ephemeral_node.py`.

Before this repair, the supervisor copied the complete parent environment and blanked only four named token variables. Arbitrary unrelated credentials or session material could therefore reach ephemeral carrier/WorkerCoordinator children despite the runtime receipt claiming no non-TV/TVC secret usage.

The merged lifecycle now requires:

```text
new ephemeral node
-> previously unused or empty runtime root
-> canonical source materialization
-> explicit non-secret child environment allowlist
-> no arbitrary *_TOKEN / *_SECRET / provider/session inheritance
-> STEGVERSE_SOVEREIGN_NODE=1
-> exact STEGVERSE_HEARTBEAT_ROOT
-> TV/TVC credential-authority marker
-> GitHub runtime authority NONE
-> separated carrier + WorkerCoordinator
-> task-capable worker tick observed
```

Intentional same-node continuity remains a separate `restart()` path. A restart refuses to start replacement processes unless the previous carrier and worker are both terminated successfully.

Explicit teardown now performs:

```text
previous carrier + worker PIDs
-> terminate both
-> independently verify both are dead
-> TEARDOWN_COMPLETE only when no supervised-process residue remains
-> retain governed durable evidence
-> mark same-root new-instance reuse forbidden
```

Validation peers created by the sovereign ephemeral console now use this verified teardown instead of sending SIGTERM and assuming success. A supposedly fresh ephemeral instance fails closed if its runtime root is non-empty, preventing stale worker state, receipts, queues, fences, or other mutable residue from silently becoming the state of a new instance.

This hardening does not delete durable evidence during teardown. Reconstruction/continuity must explicitly consume authenticated retained evidence rather than inheriting an old mutable runtime directory.

## What remains

The return-path architecture, real HTTPS/TLS mechanics, and ephemeral instantiation/teardown boundaries are now hardened together without depending on the iPhone lane. The remaining terminal proof is authentic external/runtime execution using the existing sovereign resident/ephemeral StegOS runtime and a concrete HIL HTTPS rendezvous.

The currently documented HIL state still lacks fresh public HTTPS endpoint/identity/readiness evidence. That is the first externally observable deployment boundary—not relay return logic, allocator behavior, physical-device bootstrap, or ephemeral lifecycle source hardening.

Terminal runtime evidence remains:

```text
receipts/stegos-sovereign-relay/SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001.json
state=COMPLETED
transition_id=SOVEREIGN_RELAY_RETURN_PATH_VERIFIED
round_trip_result.state=RETURN_PATH_VERIFIED
round_trip_result.far_side_evidence_present=true
round_trip_result.durable_return_queue_verified=true
round_trip_result.interlock_ingestion_verified=true
round_trip_result.canonical_transition_committed=false
```

## Next execution order

```text
existing sovereign resident/ephemeral StegOS runtime
-> existing resident dispatcher visits stegos_sovereign_relay_return_path
-> WorkerCoordinator fresh fence >21
-> exact already-local EGRESS binding/authorization/payload
-> concrete HIL HTTPS rendezvous
-> real external INGRESS_ADMITTED ACK
-> persisted far-side evidence
-> durable return queue
-> Interlock ingestion
-> terminal RETURN_PATH_VERIFIED receipt
```

Do not reopen allocator, browser, TestFlight, relay source implementation, or lifecycle source hardening unless new runtime evidence specifically binds a failure there.

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

## README impact

The root README already documents the separated carrier/WorkerCoordinator model, TV/TVC credential boundary, non-authorizing Heartbeat, source/runtime separation, and sovereign runtime constraints. This change hardens implementation behavior under those existing rules and does not introduce a new repository-wide architecture contract.
