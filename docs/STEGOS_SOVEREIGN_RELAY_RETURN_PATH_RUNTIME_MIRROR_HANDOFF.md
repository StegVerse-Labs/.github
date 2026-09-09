# StegOS Sovereign Relay Return Path Runtime Mirror Handoff

Updated: 2026-09-09

```text
goal_id: STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
task_id: SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
state: RESIDENT_EXECUTION_WIRED_ARTIFACT_AUTODISCOVERY_MERGED
credential_authority: TV/TVC
github_runtime_authority: NONE
heartbeat_execution_authority: false
worker_registration_merge: 6c4b1227579c7b561458bdf4b8b122df5985d059
artifact_autodiscovery_merge: db2d8095a549a3feee7f55d916c49e8e55dc6aa3
cosv: 50000000101000
```

This handoff resumes the already-merged StegOS relay round trip after source completion in StegOS PRs #315 and #316. It does not recreate relay materialization, route admission, or HIL ingress.

## Resident execution

The existing WorkerCoordinator owns execution through registered task:

```text
SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
adapter: process:stegos-sovereign-relay-return-path-v1
state: HANDOFF_READY
fresh fence required: >21
```

The standing worker-runtime cycle already calls `WorkerCoordinator.cycle(...)`; when no exact `--task-id` is supplied it remains the normal task sweep. No second resident-request scheduler is required merely to make this HANDOFF_READY independent task eligible.

## Real artifact discovery

Manual paths for the EGRESS binding, authorization and payload are no longer required. The merged resident worker searches bounded already-local sovereign roots and requires:

1. JSON schema `stegos.sovereign_relay_egress_binding.v1`;
2. JSON schema `stegverse.tvc.sovereign-relay-egress-authorization/v1` with `ALLOW_RELAY_EGRESS` and TV/TVC authority;
3. exact binding-id, route-id, transport-id and next-hop endpoint agreement;
4. exact payload bytes discovered by the authorization's SHA-256 and size.

Optional explicit locator environment variables remain supported only as constrained overrides and are revalidated against the same hashes/lineage:

```text
STEGVERSE_RELAY_EGRESS_BINDING
STEGVERSE_RELAY_EGRESS_AUTHORIZATION
STEGVERSE_RELAY_EGRESS_PAYLOAD
```

Normal resident roots such as `STEGVERSE_STEGOS_ROOT`, `STEGVERSE_TVC_ROOT`, `STEGVERSE_ORG_CONTROL_ROOT`, `STEGVERSE_HIL_STATE_ROOT`, and optional `STEGVERSE_RELAY_RUNTIME_BASE` provide discovery scope; no network source fetch is performed.

## Execution entrypoints

Targeted execution remains available:

```text
python scripts/run_worker_runtime.py --task-id SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
```

Portable existing-source refresh + execution remains available:

```text
python scripts/refresh_and_execute_resident_task.py --task-id SHWP-STEGOS-SOVEREIGN-RELAY-RETURN-PATH-001
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

No such terminal receipt is currently present in repository custody. The next state change is therefore resident-owned execution against a real locally retained route/authorization/payload set. Source changes, CI, or GitHub-hosted execution do not substitute for that receipt.
