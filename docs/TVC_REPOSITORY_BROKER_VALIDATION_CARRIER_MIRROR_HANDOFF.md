# TVC Repository Broker Validation Carrier Mirror Handoff

## Canonical authority

```text
goal_id: TVC-REPOSITORY-BROKER-VALIDATION-CARRIER-001
repository: StegVerse-Labs/.github
branch: main
originating_goal: eliminate the unbound TV/TVC-owned local validation carrier blocking StegVerse-Labs/TVC PR #20 and downstream private StegCore validation
canonical_owner: StegVerse-Labs/.github separated carrier + WorkerCoordinator for validation carrier only
upstream_owner: StegVerse-Labs/TVC PR #20 / TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
render_required: false
implementation_claim: RELEASED_TO_MACHINE_WORKER
validation_claim: VALIDATED_REPOSITORY_INTEGRATION_MACHINE_RUNTIME_PENDING
```

## Installed surfaces

```text
handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json
workers/tvc_repository_broker_validation_worker.py
control/worker-registry.d/tvc-repository-broker-validation-001.json
control/process-worker-adapters.d/tvc-repository-broker-validation-001.json
tests/test_tvc_repository_broker_validation_worker.py
control/admissible-existence-retrospective-conformance.json
heartbeat_runtime/engine_v13.py
heartbeat_runtime/__init__.py
tests/test_heartbeat_engine_v13_fragment_triggers.py
docs/TVC_REPOSITORY_BROKER_VALIDATION_FRAGMENT_TRIGGER_REPAIR_MIRROR_HANDOFF.md
receipts/tvc-repository-broker-validation/**   # runtime output
```

The worker does not implement or duplicate the TVC repository broker. It only locates an exact clean local TVC source root and executes the already-installed TVC task:

```text
python tools/task_dispatcher.py tvc.github_repository_operation_broker.verify
```

The validation subprocess receives no `GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PAT`, `TVC_EPHEMERAL_GITHUB_TOKEN`, provider, cloud, wallet, seed, mnemonic, or private-key environment variable. TV/TVC remains credential authority. The worker performs no network fetch and grants no merge, repository mutation, provider, wallet, signing, broadcast, release, local-model, or StegGate authority.

## Current exact source binding

```text
TVC repository: StegVerse-Labs/TVC
PR: #20
branch: feat/github-repository-operation-broker-001
expected_head: dfbf736d9e205e1fc179dc8636af74e638c2aec5
observed_current_PR_head: dfbf736d9e205e1fc179dc8636af74e638c2aec5
head_change_reason: private-repository fanout repair removed automatic anonymous pull_request validation from the supplementary hosted workflow; canonical local TV/TVC validation semantics are unchanged
upstream handoff: docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md
upstream task: tasks/TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001.json
```

The prior pin `6209396bc9846ec5f301b24d3b6f0207e571af1d` is superseded. If PR #20 head changes again before runtime validation, the worker must fail closed until the handoff/test binding is deliberately advanced to the reviewed new head. It must never silently validate a different commit.

## Private-repository hosted-workflow repair consumed

PR #20 itself is in a private repository. Its supplementary hosted workflow previously contained a `pull_request` trigger followed by anonymous private-source fetch, which cannot provide authoritative validation under the TV/TVC-only credential rule.

PR #20 head `dfbf736d9e205e1fc179dc8636af74e638c2aec5` removes that automatic pull-request fanout and restricts the historical anonymous workflow to manual public-mode execution guarded by `github.event.repository.private == false`.

This is noise/failure-surface removal only. It is not a validation PASS and it does not replace the machine-owned local carrier.

## Fragment-trigger repair consumed

The validation task is declared in `control/worker-registry.d/tvc-repository-broker-validation-001.json`, not yet in the persisted canonical `control/worker-registry.json`. The separated v12 carrier derived assignment-trigger packets only from the persisted registry, while the WorkerCoordinator applied registry fragments later. That made this valid `HANDOFF_READY` fragment-only task invisible to the carrier and prevented the non-authorizing packet required before WorkerCoordinator binding.

The scoped repair is now installed:

```text
894d1874fbacca038091a283aa0a89b8f398e927  heartbeat_runtime/engine_v13.py
8b0cb75b9c1acd28dac7e891de0edddf1c84c414  package selects engine_v13 as CarrierHeartbeatRuntime
34e7597877ff5d0b282a97f278c0b72e9524dabd  fragment-trigger regression test
5cec3938ad2b87c651b400348320eb4ed9588eba  scoped mirror handoff
```

`engine_v13` reuses the existing append-only `_apply_registry_fragments` admission path before carrier trigger derivation. The carrier remains non-authorizing: it does not create a claim/fence, bind a worker, grant credential or repository authority, or persist worker lifecycle state.

This source repair is not runtime activation. Current sovereign deployment evidence still requires a real task-capable `WorkerCoordinator` cycle and the repaired carrier has not yet been observed emitting this task's assignment packet. `docs/SOVEREIGN_HEARTBEAT_DEPLOYMENT_MIRROR_HANDOFF.md` remains the canonical owner for live carrier/worker supervision; this lane must not create a second scheduler or compete with that machine-owned runtime lane.

## Execution ownership and collision partition

### MANUAL / SESSION-STARTABLE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:validation
release_condition: none; this bucket contains no manually executable action
next_executable_action: NONE_MANUAL
```

A chat/session may inspect evidence and repair this carrier's own declarative/source defects, including stale exact-head or trigger visibility bindings, but it must not directly substitute itself for the separated carrier/WorkerCoordinator or execute credential-bearing TVC transport.

### WORKER-OWNED / DO NOT COMPETE

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:validation
release_condition: receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json state=COMPLETED for exact head dfbf736d9e205e1fc179dc8636af74e638c2aec5
next_executable_action: sovereign carrier running CarrierHeartbeatRuntime(engine_v13) emits the fragment-visible non-authorizing assignment packet; task-capable WorkerCoordinator consumes it and invokes process:tvc-repository-broker-validation-v1
```

The registered worker owns exact local-source discovery plus deterministic execution of the already-installed TVC verifier. No session may compete for the same validation receipt. `HANDOFF_READY`, `AVAILABLE`, or machine ownership is not completion.

### ESCALATED / AUTHORITY-OWNED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:integration
release_condition: validation carrier receipt COMPLETED, followed by TVC repository-owner admission decision for PR #20
next_executable_action: StegVerse-Labs/TVC canonical integration authority reviews the exact PASS receipt and admits or retains PR #20 according to its handoff
```

Credential-bearing source materialization and any repository integration remain TV/TVC/repository-owner authority, not this worker's authority.

### COMPLETED / SUPERSEDED

```text
manual_execution_allowed: false
worker_registry_ref: control/worker-registry.d/tvc-repository-broker-validation-001.json
collision_scope: tvc:github-repository-operation-broker:validation
release_condition: terminal PASS receipt retained and downstream TVC admission state recorded, or this lane is explicitly superseded by a narrower canonical machine-owned validation carrier
next_executable_action: release this worker claim and allow the existing formalism TVC transport consumer plus StegCore private-source validation task to observe the downstream release
```

Completion of this validation carrier grants no transport, credential, merge, model, wallet, signing, broadcast, or runtime authority.

## Execution states

```text
HANDOFF_READY
  worker registered and process adapter enabled; not activated

ACTIVE/BOUND
  WorkerCoordinator has consumed a real carried assignment packet and created a valid bounded worker instance; still not completed

BLOCKED
  exact locally materialized TVC source is absent or dirty

FAILED
  exact source exists but the repository-native validation task fails or returns malformed/unsafe evidence

COMPLETED
  exact source validates with dispatcher status=ok and result.result=PASS and all credential/disclosure booleans false
```

## Downstream release chain

```text
engine_v13 carrier packet observed
-> WorkerCoordinator binding/invocation observed
-> carrier receipt COMPLETED for dfbf736d9e205e1fc179dc8636af74e638c2aec5
-> TVC integration authority may admit PR #20 after its own branch/task/claim consistency check
-> formalism TVC transport worker may mark broker standing CANONICAL_VALIDATED
-> StegCore private-source bridge may use TVC MATERIALIZE_SOURCE_ARCHIVE
-> StegCore PR #141 sovereign validation executes against its then-current exact head
-> only actual PASS permits StegCore merge/consumer release
```

No downstream state is inferred from source, handoff, assignment, machine ownership, carrier continuity, or workflow success alone.

## Validation evidence

Repository integration for this carrier was previously validated after the AE denominator and ownership-partition repairs, including successful Heartbeat Worker Project and organization-control-plane validation on implementation head `871e764b1a09550dd6ad8fccf18e377981286d4b`.

The exact-head pin was advanced after the TVC private-repository fanout repair. The handoff and its deterministic test agree on `dfbf736d9e205e1fc179dc8636af74e638c2aec5`. The fragment-trigger defect was subsequently repaired in source, but no sovereign carrier execution of that repair is yet observed. Historical hosted validation and source inspection are not substituted for runtime proof.

## Completion inventory

```text
validation worker/control developed files: 7/7
fragment-trigger repair source/tests/handoff: 4/4
scaffolding/stubs: 0
missing required source files: 0
repository integration validation: HISTORICAL PASS; exact-head declarative pin reconciled
fragment-aware sovereign carrier observation: 0/1
WorkerCoordinator binding/invocation proof: 0/1
runtime carrier receipt: 0/1
TVC PR #20 admission: 0/1
StegCore downstream source-materialization release: 0/1
StegCore sovereign exact-head validation: 0/1
```

## Archive condition

Product activation remains incomplete until the repaired carrier path is actually observed, the machine-owned validation receipt exists, TVC admission occurs, and StegCore downstream sovereign validation completes. A runtime `BLOCKED`, `HANDOFF_READY`, assigned, machine-owned, source-complete, workflow-pass, or release-ready state does not authorize a PASS or archival claim.

```text
DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
```
