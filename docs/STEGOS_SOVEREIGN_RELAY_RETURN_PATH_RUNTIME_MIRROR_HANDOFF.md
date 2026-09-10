# StegOS Sovereign Relay Return Path Runtime Mirror Handoff

Updated: 2026-09-09

```text
goal_id: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
task_id: SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: RESIDENT_EXECUTION_WIRED / ARTIFACT_AUTODISCOVERY_MERGED / REFRESH_DISPATCH_MERGED / CONTROL_PLANE_SOURCE_PACKAGE_MERGED / CURRENT_IPHONE_BOOTSTRAP_REFRESH_MERGED_PUBLICLY_OBSERVED / TASK_0010_G6_PHYSICAL_ALLOCATION_PENDING
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
site_bootstrap_claim_terminalization_merge: 5a6a70730d01210b70954f0857575efe60b80b1f
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

The standing worker-runtime cycle already calls `WorkerCoordinator.cycle(...)`; when no exact `--task-id` is supplied it remains the normal task sweep. No second scheduler is required.

## Real artifact discovery

Manual paths for the EGRESS binding, authorization and payload are not required. The merged resident worker searches bounded already-local sovereign roots and requires:

1. JSON schema `stegos.sovereign_relay_egress_binding.v1`;
2. JSON schema `stegverse.tvc.sovereign-relay-egress-authorization/v1` with `ALLOW_RELAY_EGRESS` and TV/TVC authority;
3. exact binding-id, route-id, transport-id and next-hop endpoint agreement;
4. exact payload bytes discovered by the authorization's SHA-256 and size.

The executable handoff matches that behavior: `required_local_env` is empty. Optional locator environment variables remain constrained overrides only and are revalidated against the same hashes/lineage.

## Refresh -> immediate exact execution

PR #1304 merged the deterministic post-refresh continuation:

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

The request `RESIDENT-EXEC-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001` grants no execution, claim, fence, heartbeat, route, credential, transition, repository, or source-fetch authority.

## Control-plane source-package remediation

`.github` PR #1305 merged `stegverse.control-plane` under the existing `stegverse.source-package/v1` contract and a bounded `/intr/source-package` ingress on the existing profiled HIL/Universal InTr listener. LLM-adapter PR #330 merged the matching public same-Gateway projection.

Package invariants:

```text
component_id = stegverse.control-plane
package_version = 1.0.0
credential_material_included = false
authority_effect = NONE_SOURCE_TRANSPORT_ONLY
TVC_RELAY_EGRESS origin required
TVC authorization-id required
exact HTTP body SHA-256 required
```

Only the existing static control-plane source surface is writable. `.git`, runtime receipts, checkpoints, events, heartbeat state, monolithic mutable worker state, claims/fences, and other mutable runtime state are forbidden package targets.

This closes steady-state source acquisition after a resident already has the package-capable ingress. It does not by itself solve the first stale-control-plane bootstrap hop.

## First stale-control-plane bootstrap remediation

The canonical current-iPhone path already had a same-device organization allocator bootstrap under Site `stegos-node/`. Inspection found that public Site was still serving the original September 2 two-task allocator/package, so it could not see later successor tasks.

A fresh non-overlapping allocator successor was therefore created rather than widening or reactivating TASK-2026-0008:

```text
TASK-2026-0010
repository: StegVerse-Labs/Site
dependency surface: site:current-iphone-testflight-static-bootstrap
workspace: claim/current-iphone-testflight-static-bootstrap-r1
source successor: StegVerse-Labs/StegOS/release/current-iphone-site-projection/successors/current-iphone-testflight-static-bootstrap.json
```

`.github` PR #1306 merged the four-task current-iPhone allocator catalog and exact TASK-0010 source binding. Its regression proves retained G3/G4/G5 allocator state can preserve prior claims and select TASK-0010 only at monotonic generation/fence 6 when its disjoint Site scope is admissible.

Site PR #1181 then refreshed only the public `stegos-node/` bootstrap transport copies to the exact merged allocator bytes. During validation it also repaired one stale HIL source assertion that incorrectly required the historical two-profile Universal InTr literal after `MasterRecords:SV001Custody` had already been canonically added. All four Site PR gates passed.

The post-merge push workflow `StegOS Node Public Observation` run `34424948923` completed successfully against the deployed `https://stegverse.org/stegos-node/` surface. Site PR #1182 subsequently terminalized the bootstrap repair claim.

Current first-hop topology is therefore:

```text
current iPhone established StegOS Node continuity
-> deployed current four-task canonical allocator package
-> existing IndexedDB portable allocator state / atomic CAS
-> TASK-2026-0010 fresh claim/fence when physically executed and admissible
-> only then project exact TestFlight/WASM static successor bytes into Site
-> current-iPhone TestFlight/bootstrap materialization
-> resident obtains current source-capable control plane
-> steady-state /intr/source-package path available for later control-plane source transport
-> existing local source refresh + exact resident dispatch
-> relay return-path runtime rerun
```

## Current physical gate

No authentic TASK-2026-0010 claim receipt has appeared in repository/runtime custody. The deployed `stegos-node/org-allocator-bootstrap.html` verifies established current-iPhone continuity automatically, loads the exact current allocator package, and then deliberately waits for the `Run canonical allocation` control. Its current source does not automatically invoke the allocator after continuity verification.

The required physical action is therefore bounded to the established current iPhone:

```text
open https://stegverse.org/stegos-node/org-allocator-bootstrap.html
-> continuity verified
-> Run canonical allocation
-> expected selected_task_id = TASK-2026-0010 if retained current state is collision-free
-> retain/export generated allocator evidence if the page does not otherwise surface it into canonical custody
```

The expected G6/fence-6 value is a source-tested continuation from retained G5 state, not a runtime claim. If authentic retained state differs, the allocator's actual returned generation/fence is authoritative and must be reconciled instead of forcing 6.

## Execution entrypoints

Targeted execution remains:

```text
python scripts/run_worker_runtime.py --task-id SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
```

Portable already-local refresh + execution remains:

```text
python scripts/refresh_and_execute_resident_task.py --task-id SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
```

Control-plane delta package construction is source-side only:

```text
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

No such terminal receipt is currently present in repository custody. The next progression condition is the authentic current-iPhone TASK-0010 allocator receipt, followed by its separately scoped Site TestFlight static projection and current-iPhone bootstrap materialization.

## README impact

The root README already documents canonical source-shard recovery, local-only resident source refresh, WorkerCoordinator authority, TV/TVC credential authority, InTr transition authority and non-authorizing HeartBeat. This scoped handoff records the source-transport/bootstrap specialization; no authority model or repository-wide execution concept is changed by this documentation update.
