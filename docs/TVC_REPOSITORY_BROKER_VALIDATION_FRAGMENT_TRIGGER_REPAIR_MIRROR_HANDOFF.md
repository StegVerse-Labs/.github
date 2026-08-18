# TVC Repository Broker Validation Fragment Trigger Repair Mirror Handoff

## Scope

```text
goal_id: TVC-REPOSITORY-BROKER-VALIDATION-FRAGMENT-TRIGGER-REPAIR-001
repository: StegVerse-Labs/.github
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
parent_goal: TVC-REPOSITORY-BROKER-VALIDATION-CARRIER-001
canonical_tvc_pr: #79
superseded_tvc_pr: #20
archive_ready: false
```

This scoped handoff supplements `docs/TVC_REPOSITORY_BROKER_VALIDATION_CARRIER_MIRROR_HANDOFF.md`. It owns only the carrier observation defect that prevented fragment-only `HANDOFF_READY` tasks from producing worker-assignment trigger packets.

## Observed defect

The canonical TVC validation task exists in `control/worker-registry.d/tvc-repository-broker-validation-001.json`, but it is absent from the persisted `control/worker-registry.json`. The separated v12 carrier loaded only the persisted registry before `_assignment_triggers`, while the WorkerCoordinator independently applied registry fragments later. Therefore the carrier could not observe the fragment-only task and emitted no `worker_assignment_trigger_carried` packet for `SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001`.

Live evidence before repair:

```text
control/worker-registry.d/tvc-repository-broker-validation-001.json:
  task.state: HANDOFF_READY
  executor_binding: AUTHORIZED
  worker.status: AVAILABLE

control/worker-runtime-state.json:
  seen_assignment_packet_ids: []
  observation_mode: CARRIER_REFERENCE_ONLY_NO_TASK_EXECUTION

events/heartbeat-runtime.jsonl:
  no TVC-REPOSITORY-BROKER-VALIDATION trigger observed
```

## Applied repair

```text
heartbeat_runtime/engine_v13.py
  commit: 894d1874fbacca038091a283aa0a89b8f398e927
  effect: apply existing authority-neutral append-only registry fragments to the carrier's in-memory registry view immediately before trigger derivation

heartbeat_runtime/__init__.py
  commit: 8b0cb75b9c1acd28dac7e891de0edddf1c84c414
  effect: select engine_v13 as canonical CarrierHeartbeatRuntime

tests/test_heartbeat_engine_v13_fragment_triggers.py
  commit: 34e7597877ff5d0b282a97f278c0b72e9524dabd
  effect: regression test proving a fragment-only HANDOFF_READY task becomes a non-authorizing carrier trigger and its worker declaration becomes visible in-memory
```

The repair reuses `_apply_registry_fragments` from the existing heartbeat runtime. That function accepts only `NONE_REGISTRATION_ONLY` fragments, requires `github_token_required=false`, validates handoff/worker declarations, appends only IDs absent from the canonical registry, and cannot overwrite live claims/fences/timing/receipts.

## Authority preservation

This repair does not bind a worker, create a claim, mint a fence, execute the TVC broker validator, fetch private source, expose a credential, merge TVC PR #79, or claim validation PASS. The carrier remains non-authorizing. The separate WorkerCoordinator must still consume the carried packet, independently validate authority/eligibility, bind the worker, and execute the existing process adapter.

Legacy PR #20 is closed and superseded. The active exact source binding is maintained in `handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json` and `docs/TVC_REPOSITORY_BROKER_VALIDATION_CARRIER_MIRROR_HANDOFF.md`; this scoped repair does not independently pin a moving TVC head.

## Validation state

```text
source inspection: PASS
regression test source installed: YES
hosted/sovereign execution of regression test: NOT_YET_OBSERVED
carrier cycle after repair: NOT_YET_OBSERVED
worker assignment packet after repair: NOT_YET_OBSERVED
TVC validation carrier receipt: NOT_YET_OBSERVED
```

No workflow or source-complete state is treated as runtime proof.

## Required downstream transitions

```text
1. next sovereign carrier cycle uses CarrierHeartbeatRuntime(engine_v13)
2. carrier applies registry fragment and emits worker_assignment_trigger_carried for SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001
3. WorkerCoordinator consumes packet and binds tvc-repository-broker-validation-worker under existing authorization
4. worker executes exact locally materialized TVC PR #79 head validation with no non-TV/TVC credential
5. receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json records actual PASS or fail-closed evidence
6. only actual PASS permits TVC PR #79 admission review
7. admitted TVC broker permits StegCore private-source materialization and downstream sovereign validation
```

## Completion inventory

```text
repair source files: 3/3
scaffolding/stubs: 0
runtime carrier observation: 0/1
worker binding proof: 0/1
TVC validation receipt: 0/1
TVC admission: 0/1
StegCore downstream validation: 0/1
```

## Archive condition

```text
DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
```
