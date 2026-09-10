# StegOS Sovereign Relay Return Path Runtime Mirror Handoff

Updated: 2026-09-09

```text
goal_id: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
task_id: SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: RESIDENT_EXECUTION_WIRED / ARTIFACT_AUTODISCOVERY_MERGED / REFRESH_DISPATCH_MERGED / CONTROL_PLANE_SOURCE_ACQUISITION_REMEDIATION_ACTIVE
credential_authority: TV/TVC
github_runtime_authority: NONE
heartbeat_execution_authority: false
worker_registration_merge: 6c4b1227579c7b561458bdf4b8b122df5985d059
artifact_autodiscovery_merge: db2d8095a549a3feee7f55d916c49e8e55dc6aa3
handoff_autodiscovery_reconciliation_merge: 679056bfe6d3624c49085133ef169931816f4ad1
refresh_to_targeted_dispatch_merge: e73e6b9a87cdcff7eb4ffa555d83f6a3b5fa7643
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

## Newly isolated source-acquisition defect

Post-#1304 inspection showed that the resident refresh layer can only copy from an already-local canonical `.github` checkout. It deliberately performs no clone/fetch/pull/network lookup. The content-addressed source-package subsystem can remediate four application components, but the resident control plane itself is not a packageable/materializable component. The HIL/Universal InTr ingress also persists materialization requests but does not persist referenced source-package bytes.

That leaves one circular failure mode:

```text
new WorkerCoordinator/control-plane source merged
-> resident local checkout remains stale
-> local refresh faithfully copies stale source
-> new task/consumer cannot become resident-local
```

## Control-plane source-package remediation

The active source repair adds `stegverse.control-plane` under the existing `stegverse.source-package/v1` contract and a bounded `/intr/source-package` ingress on the existing profiled HIL/Universal InTr listener.

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

On admitted package receipt:

```text
TVC-authorized InTr relay
-> /intr/source-package
-> exact package validation
-> content-addressed write-once package retention
-> if STEGVERSE_HEARTBEAT_SOURCE_ROOT is declared:
   atomic allowlisted source-file replacement + readback verification
-> existing source watcher observes canonical local source changes
-> existing local source refresh
-> existing exact resident dispatcher
-> SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001 execution attempt
```

The package ingress and materializer grant no execution, claim/fence, credential, canonical transition, custody, or repository-metadata authority. They perform source transport/local materialization only. GitHub is not consulted by the resident path.

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

No such terminal receipt is currently present in repository custody. After source-package validation/merge, the rerun sequence is public Gateway projection -> TVC-authorized control-plane package delivery -> resident source materialization -> existing refresh/dispatch -> real return-path execution.

## README impact

The root README already documents canonical source-shard recovery, local-only resident source refresh, WorkerCoordinator authority, TV/TVC credential authority, InTr transition authority and non-authorizing HeartBeat. This scoped handoff records the new source-transport specialization; root README mutation is deferred only because the repository README is large and connector retrieval is truncated, making whole-file replacement unsafe in this session.
