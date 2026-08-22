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

PR #20 and PR #79 are closed and superseded. PR #92 carries the bounded broker delta and is the only current validation/admission target.

## Current exact source binding

```text
TVC repository: StegVerse-Labs/TVC
PR: #92
branch: repair/github-repository-operation-broker-rebase-002
expected_head: 06569c885f33e5761d43911ba1088fdf958855b4
current_diff_file_count: 16
source_bundle_digest_required: true
source_bundle_file_count_required: 16
current_pr_draft: true
upstream handoff: docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md
upstream task: tasks/TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001.json
```

The exact governed PASS binds both the tested PR head and `source_bundle_sha256`. Subsequent unrelated movement of `main` does not mutate the tested broker source identity. Integration must rematerialize the identical 16-file source bundle and independently verify current-base compatibility. A changed source-bundle digest requires full governed validation again.

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

PASS requires dispatcher `status=ok`, nested `result=PASS`, deterministic suites zero, `source_bundle_file_count=16`, a retained 64-character `source_bundle_sha256`, `credential_authority=TV/TVC`, and all credential/disclosure booleans false.

## Heartbeat separation

Heartbeat progression is not a validation trigger, scheduler, execution gate, fence source, retry clock, or dependency. The canonical heartbeat remains the independent 10 ms / 100 Hz oscillator reference. Worker/task execution is a separate downstream runtime lane.

The validation worker no longer requires `heartbeat_epoch`, `heartbeat_timing`, or a heartbeat-derived fencing token to execute. If an invocation carries a heartbeat epoch, it is retained only as a non-causal observation. Recheck scheduling is `SEPARATE_TASK_CONTROL_EVALUATION`, not `epoch + 1`.

## Moving-main resilience

Repeated source rematerialization solely because unrelated TVC main commits land is no longer the validation model. The governed validation receipt establishes:

```text
validated_commit_sha: exact PR #92 head
validated_source_bundle_sha256: complete ordered 16-file broker bundle
```

If TVC main advances after PASS:

```text
1. rematerialize the same bounded 16 files onto the then-current main
2. recompute source_bundle_sha256
3. require equality with the validated digest
4. perform current-base compatibility review
5. admit only if both digest identity and compatibility pass
```

Any change to broker bytes invalidates the prior digest and requires full validation again. Moving `main`, mergeability, source presence, assignment, or machine ownership never substitutes for PASS.

## Collision and authority partition

```text
MANUAL / SESSION-STARTABLE:
  manual_validation_execution_allowed: false
  source/handoff defect repair: allowed when nonduplicate

WORKER-OWNED:
  task: SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001
  worker: tvc-repository-broker-validation-worker
  adapter: process:tvc-repository-broker-validation-v1
  expected_head: 06569c885f33e5761d43911ba1088fdf958855b4
  heartbeat_dependency: false

AUTHORITY-OWNED AFTER PASS:
  TVC repository integration authority may admit the validated broker bundle only after exact governed PASS and current-base compatibility review.
```

No session may substitute itself for the machine validation worker, mint a PASS receipt, expose a credential, merge from source completeness, or treat assignment/machine ownership/readiness as done.

## Required downstream chain

```text
1. separate task-control runtime resolves SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001 independently of heartbeat progression
2. exact clean local TVC PR #92 source at 06569c885f33e5761d43911ba1088fdf958855b4 is resolved
3. worker executes tvc.github_repository_operation_broker.verify with forbidden credential variables removed
4. receipt records exact head + source_bundle_file_count=16 + source_bundle_sha256 + actual PASS/fail-closed result
5. if main moved, identical digest rematerialization + current-base compatibility are required
6. only PASS + digest identity + compatibility permits TVC broker admission
7. admitted TVC broker permits StegCore private-source MATERIALIZE_SOURCE_ARCHIVE
8. StegCore PR #141 sovereign validation executes against its then-current exact head
9. only actual StegCore PASS permits its downstream merge/release continuation
```

## Completion inventory

```text
broker delta: 16/16 files
validation worker/control developed surfaces: complete
heartbeat-gating dependency in validation worker: REMOVED
stable source-bundle digest emission: IMPLEMENTED / UNVALIDATED
tvc governed validation receipt: 0/1
tvc broker admission: 0/1
StegCore downstream materialization: 0/1
StegCore sovereign exact-head validation: 0/1
scaffolding/stubs: 0
missing required source files: 0
```

## Archive condition

The lane remains open until the exact PASS receipt exists, TVC admission occurs, and required StegCore downstream validation is consumed. Transfer, assignment, machine ownership, readiness, source completeness, and hosted workflow results are nonterminal.

```text
DO NOT ARCHIVE THIS SESSION — REQUIRED EXECUTION REMAINS IN AN ACTIVE DEPENDENCY LANE.
```
