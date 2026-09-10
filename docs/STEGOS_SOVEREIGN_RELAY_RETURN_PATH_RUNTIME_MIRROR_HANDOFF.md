# StegOS Sovereign Relay Return Path Runtime Mirror Handoff

Updated: 2026-09-09

```text
goal_id: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
task_id: SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: RESIDENT_EXECUTION_WIRED / ARTIFACT_AUTODISCOVERY_MERGED / REFRESH_DISPATCH_MERGED / CONTROL_PLANE_SOURCE_PACKAGE_MERGED / CURRENT_IPHONE_BOOTSTRAP_REFRESH_MERGED_PUBLICLY_OBSERVED / VERIFIED_ALLOCATOR_AUTO_EXECUTION_MERGED / TASK_0010_G6_RUNTIME_EVIDENCE_PENDING
credential_authority: TV/TVC
github_runtime_authority: NONE
heartbeat_execution_authority: false
worker_registration_merge: 6c4b1227579c7b561458bdf4b8b122df5985d059
artifact_autodiscovery_merge: db2d8095a549a3feee7f55d916c49e8e55dc6aa3
handoff_autodiscovery_reconciliation_merge: 679056bfe6d3624c49085133ef169931816f4ad1
refresh_to_targeted_dispatch_merge: e73e6b9a87cdcff7eb4ffa555d83f6a3b5fa7643
control_plane_source_package_merge: 52f29fbba0751787ceaca5f1c9022bdcb37338fb
public_source_package_gateway_merge: d4601f449743bb086ac2e9e38777b46b21ba8e27
current_iphone_allocator_successor_merge: e484be32e5b017a4a6f172635ea80c5d46913d8e
site_allocator_bootstrap_refresh_merge: 7d52ff8b6cf60b62adcd18aed493b8f6a61b1107
site_allocator_collision_fix_merge: 933a388b0b2ff156446bcbfe5e423fd3f91dc5a0
site_allocator_cache_freshness_merge: e86333e873fa067e42255c2712867cd3b2e96b24
site_allocator_immutable_g6_entry_merge: 34e726d5365e3b9a8f1151a03c867b117696358a
site_allocator_auto_execution_merge: e565105748a5cd52638e365c68de7803d35b5dbd
cosv: 50000000101000
```

This handoff resumes the already-merged StegOS relay round trip after source completion in StegOS PRs #315 and #316. It does not recreate relay materialization, route admission, WorkerCoordinator, HeartBeat, or any scheduler.

## Resident execution

The existing WorkerCoordinator owns execution through registered task:

```text
SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
adapter: process:stegos-sovereign-relay-return-path-v1
state: HANDOFF_READY
fresh fence required: >21
```

The standing worker-runtime cycle already calls `WorkerCoordinator.cycle(...)`; no second scheduler is required.

## Real artifact discovery

The merged resident worker discovers the EGRESS binding, TVC authorization, and exact payload from bounded already-local sovereign roots. `required_local_env` is empty. Optional locator environment variables are constrained overrides only and are independently revalidated against schema, lineage, endpoint, payload SHA-256, and size.

## Refresh -> exact resident execution

```text
already-local canonical source changes
-> existing sovereign source-refresh watcher
-> refresh heartbeat_runtime/ + workers/ + handoffs/ + control fragments/requests
-> existing generic resident dispatcher
-> exact relay-return consumer
-> scripts/refresh_and_execute_resident_task.py --task-id SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
-> existing WorkerCoordinator independent admission
-> fresh fence >21
-> existing relay return worker
-> exact local artifact autodiscovery
-> real round-trip attempt
```

The resident request grants no execution, claim, fence, heartbeat, route, credential, transition, repository, or source-fetch authority.

## Control-plane source transport

`.github` PR #1305 merged `stegverse.control-plane` under `stegverse.source-package/v1` and a bounded `/intr/source-package` ingress on the existing profiled HIL/Universal InTr listener. LLM-adapter PR #330 merged the matching public same-Gateway projection.

Only the existing static control-plane source surface is writable. `.git`, runtime receipts, checkpoints, events, heartbeat state, monolithic mutable worker state, claims/fences, and other mutable runtime state remain forbidden package targets.

## Current-iPhone first-hop bootstrap

The first stale-control-plane hop uses the established current-iPhone StegOS Node and canonical organization allocator. TASK-2026-0010 is the fresh Site-scoped successor for the current-iPhone TestFlight static bootstrap:

```text
TASK-2026-0010
repository: StegVerse-Labs/Site
dependency surface: site:current-iphone-testflight-static-bootstrap
workspace: claim/current-iphone-testflight-static-bootstrap-r1
source successor: StegVerse-Labs/StegOS/release/current-iphone-site-projection/successors/current-iphone-testflight-static-bootstrap.json
```

The physical iPhone produced authentic retained allocator state through G5. That evidence exposed two TASK-0010 scope collisions, which `.github#1308` removed. Subsequent retries exposed stale browser/service-worker delivery, which Site #1185 and #1187 repaired with network-only allocator assets, versioned source binding, and a never-before-used immutable entry.

## Verified allocator auto-execution

Site PR #1188 removed the unnecessary manual `Run canonical allocation` interaction. The new immutable entry is:

```text
https://stegverse.org/stegos-node/org-allocator-bootstrap-auto.html
```

The browser remains only the local execution carrier. Canonical organization allocator authority remains in `StegVerse-Labs/.github`.

Auto-commit is allowed only after all of these predicates pass:

```text
established current-iPhone node/device continuity validates
+ exact node journal replay passes
+ canonical portable allocator package validates
+ source_binding.task_0010_git_blob_sha == 248bed8cf5428c3ba759ee0d34db5fec8949a835
+ retained allocator state already exists
+ canonical allocator preview runs against a non-persistent cloned store
+ preview blocked_missing_dependency_declaration is empty
+ preview queued set contains exactly one successor
+ preview selects TASK-2026-0010
+ preview generation == retained generation + 1
-> invoke the same canonical allocator exactly once against the real IndexedDB CAS store
-> committed task/generation must equal preview
-> append same-device execution evidence to the established StegOS node journal
```

Any mismatch fails closed. No allocator-state reset, alternate eligibility implementation, Site claim authority, browser claim authority, HeartBeat execution authority, GitHub runtime authority, second user-operated device, or hosted fallback is introduced.

This removes the manual allocator button as an architectural progression requirement. A page/runtime carrier must still be executing on iOS for browser-resident JavaScript to run; iOS does not provide an always-on unrestricted background web runtime. Once the carrier is active, the allocator transition itself is automatic and deterministic.

## Current progression

```text
current iPhone established StegOS Node continuity
-> verified allocator auto-execution carrier
-> authentic TASK-2026-0010 claim/fence if retained G5 state remains admissible
-> project exact TestFlight/WASM static successor bytes into Site under TASK-0010
-> current-iPhone TestFlight/bootstrap materialization
-> resident obtains current source-capable control plane
-> steady-state /intr/source-package source transport
-> existing local source refresh + exact resident dispatch
-> relay return-path runtime rerun
```

No authentic TASK-2026-0010 G6/fence-6 receipt is yet present in repository custody. The previous manual-button gate is retired; the next evidence condition is the result of the verified auto-execution entry on the established current iPhone.

## Execution entrypoints

```text
python scripts/run_worker_runtime.py --task-id SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
python scripts/refresh_and_execute_resident_task.py --task-id SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
python scripts/build_control_plane_source_package.py --out /tmp/stegverse-control-plane.package.json
```

## Terminal evidence

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

No such terminal receipt is currently present in repository custody.

## README impact

The root README already documents canonical source-shard recovery, local-only resident source refresh, WorkerCoordinator authority, TV/TVC credential authority, InTr transition authority, and non-authorizing HeartBeat. This handoff records the current-iPhone bootstrap trigger specialization; no repository-wide authority model changes.
