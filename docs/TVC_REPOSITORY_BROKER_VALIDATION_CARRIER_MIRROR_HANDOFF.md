# TVC Repository Broker Validation Carrier Mirror Handoff

## Canonical authority

```text
goal_id: TVC-REPOSITORY-BROKER-VALIDATION-CARRIER-001
repository: StegVerse-Labs/.github
branch: main
canonical_owner: StegVerse-Labs/.github separated carrier + WorkerCoordinator for validation carrier only
upstream_owner: StegVerse-Labs/TVC PR #79 / TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001
superseded_upstream: StegVerse-Labs/TVC PR #20
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
implementation_claim: RELEASED_TO_MACHINE_WORKER
validation_claim: VALIDATED_REPOSITORY_INTEGRATION_MACHINE_RUNTIME_PENDING
archive_ready: false
```

Legacy PR #20 is closed and superseded. It had diverged hundreds of commits behind private `main` and could no longer be the exact admission target. PR #79 re-materializes the bounded broker delta directly on current main and is the only current validation/admission target.

## Current exact source binding

```text
TVC repository: StegVerse-Labs/TVC
PR: #79
branch: repair/github-repository-operation-broker-rebase-001
base_at_rematerialization: 389e2aee2dc00c60149c901f7b5ad4bac6d0309f
expected_head: 2ff7dacc70557f8281c18c92b2ac3ed2cf6f2cf1
observed_current_PR_head: 2ff7dacc70557f8281c18c92b2ac3ed2cf6f2cf1
legacy_PR20_head: dfbf736d9e205e1fc179dc8636af74e638c2aec5
upstream handoff: docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md
upstream task: tasks/TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001.json
```

If PR #79 head changes before governed validation, the worker must fail closed until this handoff, executable handoff, and deterministic binding test are deliberately advanced to the reviewed new head.

## Installed carrier surfaces

```text
handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json
workers/tvc_repository_broker_validation_worker.py
control/worker-registry.d/tvc-repository-broker-validation-001.json
control/process-worker-adapters.d/tvc-repository-broker-validation-001.json
tests/test_tvc_repository_broker_validation_worker.py
heartbeat_runtime/engine_v13.py
heartbeat_runtime/__init__.py
tests/test_heartbeat_engine_v13_fragment_triggers.py
docs/TVC_REPOSITORY_BROKER_VALIDATION_FRAGMENT_TRIGGER_REPAIR_MIRROR_HANDOFF.md
receipts/tvc-repository-broker-validation/**
```

The validation worker performs no source fetch and receives no GitHub/provider/wallet credential. It locates an exact clean local TVC root and executes only:

```text
python tools/task_dispatcher.py tvc.github_repository_operation_broker.verify
```

PASS requires dispatcher `status=ok`, nested `result=PASS`, deterministic suites zero, `credential_authority=TV/TVC`, and all credential/disclosure booleans false.

## Private-repository repair state

Historical anonymous-fetch and GitHub-issued-checkout validation paths are not authoritative for private TVC. Their failures/successes are neither broker PASS nor sovereign runtime evidence.

The fragment-trigger defect is repaired in source: engine v13 applies authority-neutral append-only registry fragments before deriving non-authorizing assignment packets. This allows the fragment-only `HANDOFF_READY` TVC validation task to be visible to the separated carrier without making the carrier an authority surface.

Source repair is not activation. The live chain still requires actual carrier and WorkerCoordinator execution.

## Collision and authority partition

```text
MANUAL / SESSION-STARTABLE:
  manual_execution_allowed: false
  source/handoff defect repair: allowed when nonduplicate

WORKER-OWNED:
  carrier: CarrierHeartbeatRuntime(engine_v13)
  task: SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001
  worker: tvc-repository-broker-validation-worker
  adapter: process:tvc-repository-broker-validation-v1
  expected_head: 2ff7dacc70557f8281c18c92b2ac3ed2cf6f2cf1

AUTHORITY-OWNED AFTER PASS:
  TVC repository integration authority may admit PR #79 only after exact governed PASS.
```

No chat/session may substitute itself for the machine worker, mint a PASS receipt, expose a credential, merge from source completeness, or treat assignment/machine ownership as done.

## Required downstream chain

```text
1. sovereign carrier executes engine_v13 after this exact binding is resident
2. carrier emits worker_assignment_trigger_carried for SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001
3. task-capable WorkerCoordinator consumes the packet and independently binds the registered worker
4. worker locates clean local TVC PR #79 source at 2ff7dacc70557f8281c18c92b2ac3ed2cf6f2cf1
5. worker executes tvc.github_repository_operation_broker.verify with forbidden credential variables removed
6. receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json records actual PASS or fail-closed result
7. only exact PASS permits TVC PR #79 admission review
8. admitted TVC broker permits StegCore private-source MATERIALIZE_SOURCE_ARCHIVE
9. StegCore PR #141 sovereign validation executes against its then-current exact head
10. only actual StegCore PASS permits its downstream merge/release continuation
```

## Execution states

```text
HANDOFF_READY != activated
AVAILABLE != bound
ACTIVE/BOUND != completed
workflow PASS != runtime proof
source complete != activated
release ready != released

COMPLETED only when the exact governed validation receipt is PASS for the pinned head.
```

## Completion inventory

```text
broker delta on current-main PR: 16/16 files
validation worker/control developed surfaces: complete
fragment-trigger repair source/tests/handoff: complete
scaffolding/stubs: 0
missing required source files: 0
fragment-aware sovereign carrier observation: 0/1
WorkerCoordinator binding/invocation proof: 0/1
TVC governed validation receipt: 0/1
TVC PR #79 canonical admission: 0/1
StegCore downstream materialization: 0/1
StegCore sovereign exact-head validation: 0/1
```

## Archive condition

The lane remains open until the repaired runtime path executes, the exact PASS receipt exists, TVC admission occurs, and required StegCore downstream validation is consumed. Transfer, assignment, machine ownership, readiness, source completeness, and hosted workflow results are nonterminal.

```text
DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
```
