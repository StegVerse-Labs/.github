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
validation_claim: MACHINE_RUNTIME_READY_CURRENT_HEAD_VALIDATION_PENDING
heartbeat_dependency: false
archive_ready: false
```

PR #20 and PR #79 are closed and superseded. PR #92 carries the bounded broker delta and is the only current validation/admission target.

## Current exact source binding

```text
TVC repository: StegVerse-Labs/TVC
PR: #92
branch: repair/github-repository-operation-broker-rebase-002
expected_head: b5288f9910ada26c6ab2e9bca3f7701afaae2cef
current_diff_file_count: 16
source_bundle_digest_required: true
source_bundle_file_count_required: 16
current_pr_draft: true
sv_dn1_private_source_consumers: StegVerse-Labs/StegCore + master-records/orchestration
st019_protection_operation: PROTECT_DEFAULT_BRANCH
upstream handoff: docs/GITHUB_REPOSITORY_OPERATION_BROKER_MIRROR_HANDOFF.md
upstream task: tasks/TVC-GITHUB-REPOSITORY-OPERATION-BROKER-001.json
```

PR #92's bounded 16-file broker bundle changed again when ST-019 repository protection execution was integrated from TVC PR #242. The exact governed PASS must therefore bind `b5288f9910ada26c6ab2e9bca3f7701afaae2cef` and a newly computed `source_bundle_sha256`. Subsequent unrelated movement of `main` does not mutate the tested broker source identity. Integration must rematerialize the identical 16-file source bundle and independently verify current-base compatibility. A changed source-bundle digest requires full governed validation again.

## Installed execution surfaces

```text
handoffs/SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001.json
workers/tvc_repository_broker_validation_worker.py
control/worker-registry.d/tvc-repository-broker-validation-001.json
control/process-worker-adapters.d/tvc-repository-broker-validation-001.json
tests/test_tvc_repository_broker_validation_worker.py
control/resident-execution-request.d/tvc-repository-broker-validation-001.json
scripts/consume_tvc_broker_validation_request.py
tests/test_tvc_broker_validation_resident_request.py
cost-basis/worker-runtime/tvc-repository-broker-validation.json
receipts/tvc-repository-broker-validation/**
```

The worker performs no source fetch and receives no GitHub/provider/wallet credential. It locates an exact clean local TVC root and executes only:

```text
python tools/task_dispatcher.py tvc.github_repository_operation_broker.verify
```

PASS requires dispatcher `status=ok`, nested `result=PASS`, deterministic suites zero, `source_bundle_file_count=16`, a retained 64-character `source_bundle_sha256`, `credential_authority=TV/TVC`, and all credential/disclosure booleans false. The current deterministic bundle must include the ST-019 `PROTECT_DEFAULT_BRANCH` broker and spool tests.

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
  expected_head: b5288f9910ada26c6ab2e9bca3f7701afaae2cef
  heartbeat_dependency: false

AUTHORITY-OWNED AFTER PASS:
  TVC repository integration authority may admit the validated broker bundle only after exact governed PASS and current-base compatibility review.
```

A resident source-refresh cycle has a bounded, non-authorizing request consumer for this task. The consumer first looks for the exact clean PR #92 checkout. If it is absent but an already-local TVC control root contains the merged `scripts/advance_tvc_pr92_broker_validation.py`, the consumer may invoke that TVC progression module. That module composes TVC's pre-existing systemd `LoadCredential` private-source service; the consumer itself receives no credential and performs no provider/source fetch. After TVC either materializes the exact checkout or truthfully reports `BLOCKED_CREDENTIAL_NOT_OBSERVED`, the consumer re-evaluates the canonical private-source materialization root and continues only when the exact clean head exists.

The resident request grants no private-source, network, credential, merge, or repository authority. Any provider read occurs solely inside the already-admitted TVC private-source service. Missing resident credential remains retryable `HANDOFF_READY`; digest/source/validation defects fail closed. The consumer derives the expected head and digest from the executable handoff rather than carrying a second admission identity.

No session may substitute itself for the machine validation worker, mint a PASS receipt, expose a credential, merge from source completeness, or treat assignment/machine ownership/readiness as done.

## Required downstream chain

```text
1. independent WorkerCoordinator task control resolves SHWP-TVC-REPOSITORY-BROKER-VALIDATION-001 with a fresh fence >22 independently of heartbeat progression
2. if exact PR #92 source is absent, the resident consumer may invoke merged TVC progression `scripts.advance_tvc_pr92_broker_validation` on an already-local TVC control root
3. TVC's existing systemd LoadCredential private-source service either materializes exact b5288f9910ada26c6ab2e9bca3f7701afaae2cef or reports the truthful retryable credential/source blocker
4. consumer re-discovers the exact clean canonical materialization root and then targeted task control admits the existing validation worker
5. worker executes tvc.github_repository_operation_broker.verify with forbidden credential variables removed
6. receipt records exact head + source_bundle_file_count=16 + source_bundle_sha256 + actual PASS/fail-closed result
7. if main moved, identical digest rematerialization + current-base compatibility are required
8. only PASS + digest identity + compatibility permits TVC broker admission
9. if the active request asks for repository-authority continuation, the .github consumer invokes only TVC's non-secret resident activator and requires a downstream request id to be staged/owned
10. TVC systemd alone exposes TVC_EPHEMERAL_GITHUB_TOKEN to the resident repository-authority service
11. TVC temporal continuation advances broker integration -> PR #266 validation -> successor integration -> resident spool evidence -> issue #264 admission
12. admitted broker may execute bounded ST-019 repository-protection warrants and existing private-source materialization operations under TV/TVC authority
13. repo-standards independently re-observes any protection mutation; executor success alone is not compliance
14. admitted TVC broker permits StegCore private-source MATERIALIZE_SOURCE_ARCHIVE
15. StegCore sovereign exact-head validation executes against its then-current exact head
```

## Completion inventory

```text
broker delta: 16/16 files
validation worker/control developed surfaces: complete
heartbeat-gating dependency in validation worker: REMOVED
stable source-bundle digest emission: IMPLEMENTED / UNVALIDATED
ST-019 PROTECT_DEFAULT_BRANCH source: IMPLEMENTED / UNVALIDATED
tvc governed validation request bridge: MERGED / VALIDATED
TVC PR #92 resident progression driver: MERGED / VALIDATED in TVC a35fb5b93ae30da27848e263f86c929f81636a02
resident request -> TVC progression composition: MERGED / VALIDATED in .github a59e9ffdcc890a79af911c0cd6d81aea5fbc34c2
current-base admission compatibility evaluator: MERGED / VALIDATED in TVC e350225d9e28dc45d3685afa8b7113d54fcf19b9
resident validation -> compatibility -> TVC repository-authority handoff: MERGED / VALIDATED
tvc governed validation receipt: 0/1
tvc broker admission: 0/1
ST-019 authentic protection operation: 0/1
StegCore downstream materialization: 0/1
StegCore sovereign exact-head validation: 0/1
scaffolding/stubs: 0
missing required source files: 0
```

## Current-head validation carrier merge evidence

```text
PR #413: MERGED
merge_commit: 360567287a15a11672989653c2edff8fbab1bdc8
validated_head: 35e36c55cb15f8f365bdee52b21183056d88e59b
organization control plane run 33270534316 / #1430: PASS
heartbeat worker run 33270534341 / #1654: PASS
complete deterministic repository suite: PASS
current exact TVC head binding: b5288f9910ada26c6ab2e9bca3f7701afaae2cef
exact local source retry posture: HANDOFF_READY
```

The validation lane is machine-executable whenever the sovereign runtime can either (a) see an exact clean TVC PR #92 checkout or (b) see an already-local current TVC control root containing the merged PR-#92 progression module. In case (b), the consumer can invoke the existing TVC progression, which uses the pre-existing systemd `LoadCredential` private-source capability and materializes only the exact pinned source into `/var/lib/stegverse/private-source-read/materialized/tvc-pr92-broker-validation-b5288f99`. The consumer remains credential-free and does not perform provider network acquisition itself.

For fresh requests that explicitly set `admission_compatibility_requested=true`, terminal validation is not considered the end of the resident continuation. After authentic validation is observed, the consumer locates the already-local TVC control root and invokes the merged credential-free `scripts.evaluate_github_repository_operation_broker_admission` module. The request is only terminal for that extended continuation when the evaluator reports `TVC_PR92_BROKER_ADMISSION_ELIGIBLE` for the same exact head and source-bundle digest. This still does not merge PR #92.

The resident request grants no source transport, credential, current-base mutation, commit, push, merge, or repository authority. No governed validation or admission-eligibility runtime receipt has yet been observed.

## Continuity and archive semantics

The **validation project lane remains ACTIVE / BLOCKED** until the exact PASS receipt exists, TVC admission occurs, and required downstream consumption is completed. Transfer, assignment, machine ownership, readiness, source completeness, and hosted workflow results remain nonterminal project states.

The ChatGPT session is not part of the execution chain. Continuation is durable in this handoff, the executable handoff, worker/registry surfaces, PR #92, and the receipt target. After global coordination capture, session archival does not alter validation, admission, release, runtime, or activation state.

```text
project_lifecycle: ACTIVE / BLOCKED
chat_session_required: false
tvc_governed_validation_receipt: 0/1
tvc_broker_admission: 0/1
```

## Resident post-validation compatibility continuation — 2026-08-30

TVC main now contains:

`scripts/evaluate_github_repository_operation_broker_admission.py`

Merged source:

`e350225d9e28dc45d3685afa8b7113d54fcf19b9`

The evaluator requires the authentic TVC PR-#92 progression receipt and the exact private-source materialization, clones the already-local current TVC control root with `git clone --local`, overlays only the exact validated 16 files, rechecks the unchanged digest, and reruns the canonical validator with all credential variables removed.

The `.github` resident consumer may invoke this evaluator only after its own canonical validation receipt is terminal PASS and only when the resident request explicitly asks for admission compatibility. The consumer records:

```text
terminal_validation_observed
admission_compatibility_requested
admission_compatibility_observed
admission_compatibility
```

A request with `admission_compatibility_requested=true` is not considered previously consumed until both authentic terminal validation and authentic `TVC_PR92_BROKER_ADMISSION_ELIGIBLE` are observed. This prevents an earlier validation-only attempt from suppressing the current-base compatibility continuation.

Neither the evaluator nor the resident consumer performs repository merge. The separate repository integration authority remains downstream of:

```text
governed validation PASS
+ source_bundle_sha256=0369ed677a014a99a983415a9094e6aaa0c570d163d9818d9a086fee6042dd6a
+ TVC_PR92_BROKER_ADMISSION_ELIGIBLE
```


## Resident repository-authority handoff — 2026-08-31

Merged TVC resident target:

`StegVerse-Labs/TVC@66a6bb34c5465c8070d179b2c495e7a49ebb0d5b`

TVC activator:

`scripts/activate_sv_dn1_repository_authority_request.py`

TVC target task:

`tvc.sv_dn1.repository_authority.continue`

The active resident validation request now sets:

```text
admission_compatibility_requested: true
repository_authority_continuation_requested: true
repository_authority_target_task: tvc.sv_dn1.repository_authority.continue
repository_authority_credential_transport: TVC_SYSTEMD_LOADCREDENTIAL_ONLY
```

After authentic governed validation and authentic current-base compatibility, the
credential-free `.github` consumer may invoke the TVC activator using only:

```text
--request-id <validation-request-id>-repository-authority
--repo-root <already-local TVC control root>
```

No GitHub token or credential field is forwarded. The activator may report
`BLOCKED_CREDENTIAL_NOT_OBSERVED` while still proving that the downstream TVC request
has been staged and is now resident-owned. At that point this validation-carrier request
may be terminal because the TVC path/timer owns retry.

The downstream TVC request does not prove broker integration, PR #266 integration,
issue #264 admission, repository persistence, Pages deployment, or public observation.


## Repository-authority handoff validation evidence

Validated implementation head:

`961fdd24a78fb19fcbe2e3c7cd17420492f5f3a8`

```text
Heartbeat Worker Project - Validation Only / No GitHub Token Authority
  run: 33420361666
  result: SUCCESS

Validate organization control plane - No GitHub Token Authority
  run: 33420361750
  result: SUCCESS
```

The validation proves source/control-plane consistency and that the hosted lane carries no
GitHub authority-bearing construct. It does not prove resident TVC activation, credential
presence, PR #92 governed PASS, compatibility, repository integration, issue #264
admission, persistence, deployment, or public observation.


## Repository-authority handoff merge evidence

```text
PR: #674
merge_commit: cfa5c9a9087259190c08a11429fd22bc001dd97a
final_validated_head: 787a74b1053304f4e532448d4e51b884bc8a4f76
Heartbeat Worker validation: 33420440072 SUCCESS
Organization control-plane validation: 33420440102 SUCCESS
runtime governed validation receipt: NOT OBSERVED
runtime compatibility receipt: NOT OBSERVED
downstream TVC repository-authority request: NOT OBSERVED
```

Source handoff is terminal. Remaining progress is machine/runtime evidence produced by the
sovereign resident control plane and the downstream TVC service; this chat is not an
execution dependency.
