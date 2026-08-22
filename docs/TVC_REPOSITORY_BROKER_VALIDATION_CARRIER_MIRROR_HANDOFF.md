# TVC Repository Broker Validation Carrier Mirror Handoff

## Canonical authority

```text
goal_id: TVC-REPOSITORY-BROKER-VALIDATION-CARRIER-001
repository: StegVerse-Labs/.github
branch: main
canonical_owner: separate WorkerCoordinator/task-control runtime for validation execution only
upstream_owner: StegVerse-Labs/TVC PR #92 / TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001
superseded_upstream: StegVerse-Labs/TVC PR #20, PR #79
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_allowed: false
implementation_claim: RELEASED_TO_MACHINE_WORKER
validation_claim: VALIDATED_REPOSITORY_INTEGRATION_MACHINE_RUNTIME_PENDING
heartbeat_dependency: false
archive_ready: false
```

PR #20 and PR #79 are closed and superseded. PR #92 carries the same bounded broker delta and is the only current validation/admission target.

## Current exact source binding

```text
TVC repository: StegVerse-Labs/TVC
PR: #92
branch: repair/github-repository-operation-broker-rebase-002
base_at_latest_rematerialization: e718abdacfce1a0c6d524464f549cbbb54af7724
expected_head: a817cc8aa58ece1ae104ebfc59f4074ccbc60031
current_diff_file_count: 16
latest_compare_at_reconciliation: one commit ahead / zero behind
current_pr_mergeable: true
current_pr_draft: true
upstream handoff: docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md
upstream task: tasks/TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001.json
```

If PR #92 head changes before governed validation, the worker must fail closed until this handoff, executable handoff, and deterministic binding test are deliberately advanced to the reviewed head. Subsequent unrelated movement of `main` does not change the exact validation identity; integration must re-check base compatibility immediately before merge without silently substituting a different validated head.

## Installed execution surfaces

```text
handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json
workers/tvc_repository_broker_validation_worker.py
control/worker-registry.d/tvc-repository-broker-validation-001.json
control/process-worker-adapters.d/tvc-repository-broker-validation-001.json
tests/test_tvc_repository_broker_validation_worker.py
receipts/tvc-repository-broker-validation/**
```

The worker performs no source fetch and receives no GitHub/provider/wallet credential. It locates an exact clean local TVC root and executes only:

```text
python tools/task_dispatcher.py tvc.github_repository_operation_broker.verify
```

PASS requires dispatcher `status=ok`, nested `result=PASS`, deterministic suites zero, `credential_authority=TV/TVC`, and all credential/disclosure booleans false.

## Heartbeat separation

Heartbeat progression is not a validation trigger, scheduler, execution gate, or dependency. The canonical heartbeat remains the independent 10 ms / 100 Hz oscillator reference. Worker/task execution is a separate downstream runtime lane. No heartbeat observation, missed observation, carrier epoch, assignment packet, or phase state permits, delays, suppresses, or advances this validation task.

The former wording that required a heartbeat-carried assignment packet before this validation could run is superseded. The task may execute whenever the separate task-control runtime independently satisfies its authority and source predicates.

## Collision and authority partition

```text
MANUAL / SESSION-STARTABLE:
  manual_validation_execution_allowed: false
  source/handoff defect repair: allowed when nonduplicate

WORKER-OWNED:
  task: SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001
  worker: tvc-repository-broker-validation-worker
  adapter: process:tvc-repository-broker-validation-v1
  expected_head: a817cc8aa58ece1ae104ebfc59f4074ccbc60031
  heartbeat_dependency: false

AUTHORITY-OWNED AFTER PASS:
  TVC repository integration authority may admit PR #92 only after exact governed PASS and current-base compatibility review.
```

No session may substitute itself for the machine validation worker, mint a PASS receipt, expose a credential, merge from source completeness, or treat assignment/machine ownership/readiness as done.

## Required downstream chain

```text
1. separate task-control runtime resolves SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001 independently of heartbeat progression
2. exact clean local TVC PR #92 source at a817cc8aa58ece1ae104ebfc59f4074ccbc60031 is resolved
3. worker executes tvc.github_repository_operation_broker.verify with forbidden credential variables removed
4. receipts/tvc-repository-broker-validation/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json records actual PASS or fail-closed result
5. only exact PASS plus current-base compatibility permits TVC PR #92 admission review
6. admitted TVC broker permits StegCore private-source MATERIALIZE_SOURCE_ARCHIVE
7. StegCore PR #141 sovereign validation executes against its then-current exact head
8. only actual StegCore PASS permits its downstream merge/release continuation
```

## Completion inventory

```text
broker delta on current-main repair PR: 16/16 files
validation worker/control developed surfaces: complete
scaffolding/stubs: 0
missing required source files: 0
TVC governed validation receipt: 0/1
TVC PR #92 canonical admission: 0/1
StegCore downstream materialization: 0/1
StegCore sovereign exact-head validation: 0/1
```

## Archive condition

The lane remains open until the exact PASS receipt exists, TVC admission occurs, and required StegCore downstream validation is consumed. Transfer, assignment, machine ownership, readiness, source completeness, and hosted workflow results are nonterminal.

```text
DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
```
