# SDK TT Richard Seam Authentic Runtime Mirror Handoff

Updated: 2026-09-19
Goal Task ID: `SDK-TT-RICHARD-SEAM-AUTHENTIC-RUNTIME-001`
Parent Goal Task ID: `SDK-TT-ATOMIC-TASK-WORKER-BINDING-001`
Root Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `20010000110000`
Repository: `StegVerse-Labs/.github`
Status: `ACTIVE / CHECKED_OUT / TEST 3 AUTHENTIC SEAM VALIDATION REGISTERED`

## Question

Does the current experimental seam hold under authentic StegVerse governance when the task-bound actor is short-lived and is created and destroyed within one bounded commitment window?

Test 3 carries forward the exact semantic invariant proved by Test 2, but no longer treats SDK-local semantics as sufficient evidence.

## Preserved controls

Test 1 and Test 2 evidence are immutable inputs to this comparison and must not be rewritten.

The substantive task remains the deterministic integrity-summary operation used by the earlier tests:

```text
purpose: Analyze a supplied text payload for a tracked integrity summary.
capability: text.integrity_summary
payload: StegVerse tracks this arbitrary local worker task.
```

The Test 2 deterministic packet hash is retained only as a semantic reference:

```text
b5bbb5476350805a55f365cd27fc0fa8145c75d4cb5b27338d5299d328ca5890
```

Authentic runtime receipts are expected to have their own identities and hashes.

## Required authentic sequence

```text
registered HANDOFF_READY task T + no task-bound W
-> fresh WorkerCoordinator claim/fence prepared for T
-> required TV/TVC warrant/policy verified
-> StegCore/InTr admits ONE constitutive ACTIVATE(T)+CREATE_AND_BIND(W,T) transition
-> Master Records closes/reconstructs that transition
-> INVOCATION_STARTED only after closure
-> result bound to the same T/W/claim/fence
-> StegCore/InTr admits CLOSE(T)+RETIRE(W,T)
-> Master Records closes/reconstructs retirement
-> no continued task-bound authority
-> records-only reconstruction after W disappears
```

WorkerCoordinator coordination, TV/TVC credential/warrant facts, and Master Records custody are not substitutes for the constitutive task transition. No valid state may expose ACTIVE T without its newly created W, nor a task-bound W without ACTIVE T.

## Master Records progression gate

Every governed Test 3 transition must return:

```text
state=RECORDED
reconstruction_status=PASS
required_evidence_validation_status=PASS
receipt_sha256 == reconstructed_receipt_sha256
```

before the next machine-owned progression.

## Falsification requirements

The authentic path must fail closed for the same eight semantic violations proven locally in Test 2: ACTIVE without worker; worker without ACTIVE task; mismatched T/W binding; pre-activation task-bound worker; invocation before constitutive closure; manifest-boundary expansion; completed task with live bound worker; or records-only output retaining executor/callable state.

## Evidence boundary

GitHub/CI validates source and coordination only. Test 3 is complete only with authentic retained runtime evidence through the existing WorkerCoordinator -> TV/TVC -> StegCore/InTr -> StegAgents -> Master Records path. Do not create another runtime, scheduler, dispatcher, WorkerCoordinator, transition authority, custody store, credential plane, or second user-operated device dependency.

## First continuation

Re-read current Task Registry generation 82 and this handoff. Reconcile the existing WorkerCoordinator/StegAgents/InTr path against the Test 2 atomic constitutive transition contract before execution. Repair only concrete existing-path defects required to prevent split task/worker state. Then execute the existing targeted one-shot only when that path can authentically produce and custody the combined ACTIVATE(T)+CREATE_AND_BIND(W,T) transition.


## First concrete existing-path defect — registry generation 82

Source tracing found a concrete seam violation in the current WorkerCoordinator path before any Test 3 runtime attempt.

Current source order in `heartbeat_runtime/worker_runtime_legacy.py::_activate_from_trigger` is:

```text
prepare fresh claim/fence + worker_instance_id
-> submit WORKERCOORDINATOR_CLAIM_FENCE_BOUND to Master Records
-> require RECORDED + reconstruction PASS + required-evidence PASS + exact digest equality
-> mutate task.state = ACTIVE
-> bind worker_id / worker_instance_id / claim_id
-> mark worker BUSY
-> invoke shared worker
-> only inside StegAgents does TV/TVC verification and StegCore/InTr admission occur
```

That ordering does not satisfy Test 2's constitutive invariant for Test 3. It permits `ACTIVE T <-> W` to be exposed before StegCore/InTr has admitted and Master Records has closed the required combined `ACTIVATE(T)+CREATE_AND_BIND(W,T)` transition.

The claim/fence custody itself remains valid coordination evidence. The defect is the promotion of the task to ACTIVE and binding of W before transition authority acts.

### Required repair

For the Test 3 atomic-seam path only:

```text
HANDOFF_READY T + no task-bound W
-> WorkerCoordinator prepares fresh claim/fence as pending coordination state
-> Master Records closes claim/fence custody
-> TV/TVC warrant/policy verification closes
-> StegCore/InTr evaluates ACTIVATE(T)+CREATE_AND_BIND(W,T)
-> Master Records closes/reconstructs that constitutive transition
-> only then is ACTIVE T <-> W exposed and invocation allowed
```

Do not alter Test 1 or Test 2 evidence and do not weaken other worker paths. Reuse the existing WorkerCoordinator, shared StegAgents worker/process adapter, TV/TVC, StegCore/InTr, and Master Records components.

No authentic Test 3 execution has been attempted yet because the current source path would violate the invariant being tested.


## Source repair implementation — StegAgents merged / .github validation pending

StegAgents PR #26 passed Test Readiness, Cross-Agent Authority Validation, and CI at exact head `bd0d349af1f1b03bacd0d5b020d3dc0cdb683c65` and merged as `a847dae9b72b3914b98c33cc94b8d2a87c1a685d`.

The reconciled .github repair preserves the Test-3-only pending-activation seam:

```text
HANDOFF_READY T + no authoritative claim_id/worker_id/worker_instance_id
-> fresh WorkerCoordinator claim/fence retained only in pending_atomic_activation
-> Master Records closes claim/fence custody
-> existing ProcessWorkerAdapter invokes shared StegAgents bridge in ATOMIC_ACTIVATION mode
-> TV/TVC verification
-> StegCore/InTr evaluates ACTIVATE(T)+CREATE_AND_BIND(W,T)
-> Master Records must return RECORDED + reconstruction PASS + required-evidence PASS + exact digest equality
-> only then WorkerCoordinator projects ACTIVE T <-> W
-> separate TASK_EXECUTION mode may invoke W
```

No non-Test-3 worker path is intentionally changed. Authentic Test 3 execution remains unclaimed until the .github exact head is validated and merged.


## Resident request-carriage repair — proposed generation 90

The missing Test 3 resident carriage binding is now implemented without adding a runtime, scheduler, dispatcher, WorkerCoordinator, authority plane, or device dependency.

Added:
- `control/resident-execution-request.d/sdk-tt-richard-seam-authentic-runtime-001.json`
- `scripts/consume_sdk_tt_richard_seam_authentic_runtime_request.py`
- exactly one `sdk_tt_richard_seam_authentic_runtime` selector in the existing resident dispatcher
- focused request/COSV/authority-boundary tests.

The request/consumer is non-authorizing and invokes only the existing `scripts/refresh_and_execute_resident_task.py` path with the exact Task ID and COSV `20010000110000`. It requires the returned canonical COSV pointer binding and retains GitHub runtime authority NONE, TV/TVC credential authority, no network source fetch, and no second-machine dependency.

Authentic Test 3 evidence must come from the resident dispatch/one-shot result after this source is merged; source/CI does not satisfy any runtime predicate.


## Resident materialization correction — proposed generation 91

After resident-carriage PR #2215 merged as `65ab90acb1bca5f911ac4cd2f5046c4c26180f58`, the next concrete source defect was found in the existing source-materialization path: the new request lived under `control/resident-execution-request.d` and would be copied by the directory refresh, but the new request-specific consumer was not yet present in `refresh_sovereign_worker_runtime_source.py`'s static script allowlist. A refreshed resident could therefore receive the request and dispatcher selector while still lacking the consumer executable.

Repair:
- add the Test 3 consumer to the existing resident local-source refresh allowlist;
- add the Test 3 request and consumer to the existing bootstrap-critical control-plane source package allowlist;
- do not add a new transporter, runtime, scheduler, dispatcher, or authority path.

Authentic runtime evidence remains unclaimed until a resident source carrying these bytes produces the exact selector visit and one-shot receipts.


## Post-materialization reconciliation — proposed generation 92

Resident request carriage PR #2215 merged as `65ab90acb1bca5f911ac4cd2f5046c4c26180f58`.

Resident materialization PR #2216 merged as `9244d419e9a5a071dbab9072b4705ab19535c58c` after all exact-head checks passed. The existing local source-refresh static allowlist now carries the Test 3 request-specific consumer, and the existing bootstrap-critical control-plane source package carries both the Test 3 request and consumer.

Therefore the Test 3 source path from canonical source -> existing resident source materialization -> existing resident dispatcher is source-complete. No authentic runtime predicate is promoted from those merges.

The next actual evidence transition is now:

```text
AUTHENTIC_RESIDENT_REQUEST_DISPATCH_VISIT
```

for selector `sdk_tt_richard_seam_authentic_runtime`, followed by the already-defined targeted one-shot and its fresh claim/fence, TV/TVC, InTr, Master Records, T/W invocation/result, close/retire, and records-only evidence.

## Source-delivery relay invocation repair — proposed generation 93

After nine hours with no background execution, canonical state was re-read and remained at generation 92 with no authentic Test 3 resident dispatch or consumption receipt.

Tracing the already-required `RT-CONTROL-PLANE-SOURCE-PACKAGE-001 -> RTC-INTERLOCK-INTR-TRANSPORT-008 / TVC relay` path found the next concrete source-delivery defect: StegOS already contained the correct `ControlPlaneSourcePackageIngressTransport` profile adapter, but `execute_control_plane_source_package_relay()` was referenced only by its module and tests. The generic relay CLI cannot select the control-plane JSON ingress profile, so the exact content-addressed package had no bounded production invocation surface.

StegOS PR #396 added only `scripts/execute_control_plane_source_package_relay.py`, which consumes an already-issued TVC authorization, already-admitted relay binding, and exact `stegverse.control-plane` package and invokes the existing profile adapter. It creates no authorization, binding, transport, runtime, scheduler, dispatcher, credential path, or transition authority. StegOS CI and GADI boundary validation passed and PR #396 merged as `4a1aa89b14292267a4dcff3131900af86083840c`.

The next authentic evidence transition is now the existing bounded relay invocation producing:

```text
stegverse.control-plane-source-package-ingress/v1
state=SOURCE_MATERIALIZED_VERIFIED
source_identity=<exact package identity>
```

Only after that authentic source-materialization receipt may Test 3 advance to resident source refresh, selector visit, and one-shot execution.

## Complete Test 3 control-plane delta repair — proposed generation 95

After rechecking current generation 94, the control-plane package still carried only the Test 3 resident request and consumer, not the already-merged atomic seam implementation those files depend on.

The stale-resident bootstrap package therefore could materialize the Test 3 selector/request while leaving an older WorkerCoordinator/shared-worker path in place, reintroducing the exact pre-InTr ACTIVE T <-> W ordering Test 3 is intended to falsify.

The bounded repair extends only the existing RT-CONTROL-PLANE-SOURCE-PACKAGE-001 allowlist with the already-merged Test 3 delta: heartbeat_runtime/worker_runtime_legacy.py, heartbeat_runtime/process_adapter.py, workers/stegagents_governed_runtime_worker.py, the Test 3 executable handoff, and the Test 3 worker-registry fragment. The existing Test 3 request and consumer remain included.

No new runtime, scheduler, dispatcher, transport, WorkerCoordinator, request plane, custody path, or authority plane is introduced. The next runtime predicate remains authentic delivery of the exact resulting package and far-side SOURCE_MATERIALIZED_VERIFIED evidence.

## Package-delta closeout — proposed generation 96

PR #2223 passed exact-head Cross-Task Coordination, Purpose-Bound Worker, KV AI Memory, and DeepSeek resident validation and merged as `4696d4b0898c504fa0f601f8b879551ba2614903`.

The control-plane package now carries the complete `.github` Test 3 atomic-seam delta required for stale-resident recovery. No authentic source-package relay or far-side materialization receipt has been observed yet, so runtime predicates remain unchanged.

Next actual transition: `AUTHENTIC_CONTROL_PLANE_SOURCE_PACKAGE_RELAY_TO_SOURCE_MATERIALIZED_VERIFIED`.


## Test suite execution — proposed generation 99

A current-main suite run was initiated across Test 1, Test 2, and the Test 3 source path.

Current-main SDK validation PR #274 triggered the existing Test 1 and Test 2 workflows. Current-main StegAgents validation PR #27 triggered full StegAgents CI on Python 3.11 and 3.12. A focused .github validation PR #2239 executed the four Test 3 source modules directly.

The first focused Test 3 run produced 11 PASS / 1 FAIL. The failure was not a runtime-seam violation. The test `test_workercoordinator_projects_active_only_after_closed_constitutive_receipt` incorrectly labeled the first `registry["generation"] = generation` inside the Test 3 branch as the later generic activation boundary. Current source inspection confirms the actual Test 3 ordering is:

```text
Master Records closure predicates
-> first authoritative registry generation/task projection
-> ACTIVE T <-> W
-> invocation
-> return from Test 3 branch
-> later generic worker paths
```

The assertion is repaired to bind those exact boundaries, and the existing Purpose-Bound Worker workflow is extended to execute the focused Test 3 modules whenever their source/test surfaces change. No runtime authority or authentic Test 3 completion is inferred from CI.


### Current-main suite result

The requested current-main suite completed with the following source/semantic results:

```text
Test 1 / SDK TT Purpose-Bound Worker Console
run 35450287407 / job 105916138211
4 unit tests PASS
TT_PURPOSE_BOUND_WORKER_CONSOLE_PASS

Test 2 / SDK TT Atomic Task-Worker Binding
run 35450287467 / job 105916138352
4 unit tests PASS
TT_ATOMIC_TASK_WORKER_BINDING_PASS

Test 3 / StegAgents full source suite
run 35450310351
Python 3.11 job 105916200537: 119 passed + 34 subtests passed
Python 3.12 job 105916200664: 119 passed + 34 subtests passed

Test 3 / .github focused seam suite after harness repair
run 35450612281 / job 105916988257
existing runtime-path tests: 6 passed
focused Richard-seam modules: 12 passed
```

The initial focused Test 3 run's single failure was the test-harness boundary-labeling defect described above; the repaired exact-head suite is green. These are source/semantic tests only. Test 3's authentic runtime completion remains pending the existing `SOURCE_MATERIALIZED_VERIFIED` -> resident one-shot evidence chain.


## Dedicated runnable Test 3 acceptance — proposed generation 100

Test 3 now has a first-class executable runner rather than being represented only by constituent test modules.

Entrypoint:

`python scripts/run_sdk_tt_richard_seam_test3.py --stegagents-root <StegAgents checkout> --json-out <result.json>`

The runner validates the exact Test 3 task/COSV/prestate contract, executes the five current .github Test 3/runtime-path modules, executes the StegAgents purpose-bound runtime Test 3 module, and emits one machine-readable `stegverse.sdk-tt-richard-seam-test3-acceptance/v1` result. A dedicated `Test 3 Richard Seam Acceptance` workflow runs the same entrypoint against current .github and current StegAgents source.


### Dedicated Test 3 run result

Exact-head run `35452133634` / job `105920780352` executed `scripts/run_sdk_tt_richard_seam_test3.py`.

Result:

```text
state=PASS
dotgithub=18 passed
StegAgents validation=PASS_119_TESTS_PLUS_34_SUBTESTS_ON_PYTHON_3_11_AND_3_12
constitutive_transition=ACTIVATE_TASK_AND_CREATE_BIND_WORKER
TEST3_RICHARD_SEAM_ACCEPTANCE_PASS
```


## Runnable Test 3 closeout — proposed generation 101

PR #2242 passed all exact-head validations, including dedicated `Test 3 Richard Seam Acceptance` run `35452251194`, and merged as `0b5ea1c76cae7f96b481fe38b339071f34235957`.

The dedicated runner is now on main:

`python scripts/run_sdk_tt_richard_seam_test3.py --json-out <result.json>`

Exact-head result:

```text
state=PASS
dotgithub=18 passed
StegAgents current validation=PASS_119_TESTS_PLUS_34_SUBTESTS_ON_PYTHON_3_11_AND_3_12
constitutive_transition=ACTIVATE_TASK_AND_CREATE_BIND_WORKER
TEST3_RICHARD_SEAM_ACCEPTANCE_PASS
```

The runnable acceptance portion is complete and merged.


## Runtime dependency reconciliation — generation 102

Current executable state was re-read against the authoritative Test 3 executable handoff and WorkerCoordinator fragment. The earlier source-package relay/materialization step is retained as historical source-delivery evidence, but it is not a current Test 3 runtime predecessor. The executable handoff declares `task.dependencies=[]`, `carrier_trigger_required=false`, and authorizes a fresh independent WorkerCoordinator claim as the next action. The WorkerCoordinator fragment independently records `FRESH_WORKERCOORDINATOR_CLAIM_FENCE_PREPARED_FOR_T` as the next actual transition.

The current machine-owned Test 3 progression therefore begins:

```text
HANDOFF_READY T + no task-bound W
-> FRESH_WORKERCOORDINATOR_CLAIM_FENCE_PREPARED_FOR_T
-> Master Records closes claim/fence custody
-> TV/TVC warrant/policy verification
-> InTr ACTIVATE(T)+CREATE_AND_BIND(W,T)
-> Master Records closure
-> invocation/result
-> CLOSE(T)+RETIRE(W,T)
-> Master Records closure
-> records-only reconstruction
```

No source-package relay, connected-device discovery, carrier trigger, second runtime, or new authority plane is a prerequisite for this progression. Historical source-delivery work remains preserved and is not rewritten as runtime evidence.


## Targeted one-shot carrier-gate repair — generation 103

The first concrete post-generation-102 execution defect was in `scripts/refresh_and_execute_resident_task.py`: after refreshing already-local source, it rejected every non-Ecosystem-Chat targeted invocation unless `control/heartbeat-carrier-runtime-state.json` existed. That guard contradicted the Test 3 executable handoff (`carrier_trigger_required=false`) and the targeted `run_worker_runtime.py --task-id` path, which already performs independent WorkerCoordinator admission without carrier bootstrap.

The repair removes the carrier prerequisite for independent `--task-id` execution while preserving the historical carrier requirement only for `--resume-claimed-task-id`, where an existing claim/fence is being resumed. Regression coverage proves the Test 3 task reaches the targeted runner without a carrier file.

This is a source-path repair only. It does not claim that the fresh claim/fence transition has already occurred. The next authentic transition remains `FRESH_WORKERCOORDINATOR_CLAIM_FENCE_PREPARED_FOR_T`, followed immediately by Master Records custody and the existing TV/TVC -> InTr atomic activation sequence.


## Same-root resident execution repair — generation 104

After the carrier gate was removed, tracing the actual resident dispatcher argument flow found the next concrete defect: the native WorkerCoordinator dispatcher invokes resident consumers with the resident root as both `source_root` and `runtime_root`. The Test 3 consumer correctly forwards those values into `refresh_and_execute_resident_task.py`, but the refresh helper rejects identical roots because its copy-refresh operation is designed only for distinct canonical-source and resident-runtime trees.

For an already-materialized resident source tree, copying the tree onto itself is unnecessary and is not a state-transition prerequisite. The targeted bridge now treats `source_root == runtime_root` as `SOURCE_EQUALS_RUNTIME_NO_REFRESH_REQUIRED`, preserves mutable runtime state in place, performs no network fetch or credential acquisition, and proceeds directly to the existing targeted WorkerCoordinator runner. Distinct roots retain the existing refresh behavior.

Regression coverage executes the Test 3 independent task with one same root, no carrier file, and verifies that the targeted runner is reached. Authentic claim/fence evidence remains required before progression.


## Master Records custody-binding carriage repair — generation 105

Tracing the first post-WorkerCoordinator transition found that the Test 3 request consumer and targeted bridge sanitized the environment before `run_worker_runtime.py`, but did not preserve the variables consumed by `workers/canonical_state_transition_custody.py`. As a result, even a correctly prepared fresh claim/fence would reach `submit_state_receipt()` with neither a configured canonical Master Records HTTP custody surface nor the durable local Master Records binding, forcing `CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE` before progression.

The existing path now preserves the canonical Master Records custody binding through both sanitization boundaries. Supported carriage includes the existing HTTP endpoint/token/timeout and the existing durable local database/receipt-key/storage-durability tuple plus the already-supported Master Records repository roots. GitHub credentials remain stripped, no new custody store or authority plane is created, and Master Records still grants no transition authority.

The next authentic state remains a fresh WorkerCoordinator claim/fence followed by Master Records `RECORDED`, reconstruction PASS, required-evidence PASS, and exact receipt/reconstruction digest equality. Only that closure permits TV/TVC and InTr progression.


## StegAgents adapter Master Records carriage repair — generation 106

The Test 3 worker uses the shared `process:stegagents-governed-runtime-v1` adapter. After generation 105 preserved the canonical Master Records binding into `run_worker_runtime.py`, the adapter's own `env_allowlist` still dropped that binding before launching `workers/stegagents_governed_runtime_worker.py`. Test 3 atomic activation requires the StegAgents runtime to return closed `TV_TVC_WARRANT_POLICY_VERIFIED` and `ACTIVATE_TASK_AND_CREATE_BIND_WORKER` Master Records transitions, so stripping the binding made those required transitions unreachable.

The existing adapter now carries the same canonical Master Records HTTP or durable-local binding already admitted upstream. TV warrant/policy variables remain unchanged, GitHub runtime authority remains NONE, and no new credential, custody, or transition authority is created.


## Governed close/retire phase implemented — generation 108

The terminal Test 3 defect was source-level, not evidentiary: after the existing shared StegAgents worker returned `GOVERNED_TASK_RESULT_READY_FOR_CLOSE`, WorkerCoordinator set `test3_waiting_for_governed_close=true` and then emitted a waiting event forever. There was no executable edge to `CLOSE_TASK_AND_RETIRE_WORKER`.

That edge now exists without adding another runtime, scheduler, dispatcher, WorkerCoordinator, transition authority, or custody plane. StegAgents merge `eae52ac20b06846bc0fca55980d778d57108ef9f` adds the third request mode `stegverse.stegagents-atomic-task-worker-close-request/v1`. The existing WorkerCoordinator invokes the same `process:stegagents-governed-runtime-v1` adapter in `GOVERNED_CLOSE` mode on the next targeted cycle.

The close phase requires the same task, worker, claim, fence, and worker-instance lineage as activation and execution; requires the already-recorded `TASK_BOUND_WORKER_TASK_COMPLETED` receipt; submits `CLOSE_TASK_AND_RETIRE_WORKER` through StegCore/InTr; and refuses terminal projection unless canonical Master Records returns `RECORDED`, reconstruction PASS, required-evidence PASS, and exact receipt/reconstruction digest equality.

Only after that closure does the worker return `COMPLETED` to WorkerCoordinator. The records-only result must prove `worker_live_after_close=false`, `continued_authority_after_retirement=false`, `callable_retained=false`, and `executor_reference_retained=false`. WorkerCoordinator then releases W through its existing completed-response semantics.

This generation implements the previously missing state-machine edge. It does not claim that the already-REQUESTED authentic one-shot has yet produced the runtime receipts. The next authentic predicate remains a fresh WorkerCoordinator claim/fence.


## Resident dispatcher Master Records carriage repair — generation 111

The first concrete remaining `REQUESTED -> WorkerCoordinator` defect was in `scripts/dispatch_resident_execution_requests.py`. Its environment sanitizer preserved the canonical Master Records HTTP endpoint/token/timeout but dropped the durable-local binding variables `MASTER_RECORDS_DB`, `MASTER_RECORDS_RECEIPT_KEY`, and `MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS` before invoking the Test 3 consumer. That made the downstream generation-105/106 custody-carriage fixes unreachable for resident installations using the durable local Master Records binding.

The existing dispatcher now preserves those three canonical custody inputs. No runtime, scheduler, dispatcher, authority plane, source relay, carrier dependency, or device prerequisite was added. The next authentic transition remains the fresh WorkerCoordinator claim/fence and canonical Master Records closure.


## Targeted one-shot dispatch/drive repair — generation 114

Tracing the already-REQUESTED request after the dispatcher custody fix exposed why the Test 3 one-shot was still not being driven promptly. The native worker process invoked the resident dispatcher only every 100 ticks in global sequential mode; Test 3 was consumer 35 of 51. In addition, the Test 3 consumer invoked exactly one targeted WorkerCoordinator cycle, while the repaired lifecycle requires a second targeted cycle to consume `test3_waiting_for_governed_close` and execute `GOVERNED_CLOSE`.

The existing native dispatcher path now invokes the already-registered exact selector `sdk_tt_richard_seam_authentic_runtime` first whenever the canonical Test 3 request is present, then preserves the normal global dispatcher pass so unrelated resident work is not suppressed. The Test 3 consumer now drives a maximum of two targeted WorkerCoordinator cycles in the same request consumption, stopping early if the authentic terminal close receipt already exists.

This adds no runtime, scheduler, dispatcher, authority plane, carrier requirement, source relay, or device prerequisite. It makes the existing `TARGETED_INDEPENDENT_TASK_CONTROL_ONE_SHOT` behave as one bounded Test 3 request rather than a globally delayed multi-visit sequence.


## Option-A reconciliation and post-retirement stale-fence falsification — generation 184 candidate

Completed predecessor `SDK-FOUR-STAGE-EVIDENCE-REMEDIATION-001` is now reconciled into this existing authentic-runtime lineage rather than creating a duplicate task. The predecessor remains immutable RETIRED / COMPLETED / VALIDATED and contributes one additional runtime falsification predicate:

`POST_RETIREMENT_STALE_FENCE_INVOCATION_REFUSED_AND_REFUSAL_RETAINED`.

The predecessor evidence is source/test evidence only: SDK PR #304 merged as `e1116e9cb5f5043c9198505d64560b710c517e88`; four-stage run `35648276053`; artifact `10661081336` with SHA-256 `82fd8e824fe5fb175ae17fc57ea34a729996dd37b02878b11969f10abcd93ba5`. None of that establishes authentic standing, retirement, stale-fence refusal, or runtime completion for this task.

Tracing the existing Test-3 terminal path found one concrete source gap. `CLOSE_TASK_AND_RETIRE_WORKER` already closes through StegCore/InTr and canonical Master Records, but the state machine previously returned records-only completion immediately afterward. It did not attempt a post-retirement invocation using the just-retired claim/fence, so the required refusal could not be authentically observed or retained.

The bounded repair reuses the existing StegAgents -> SDK/StegCore/InTr -> canonical Master Records path. After the close receipt is `RECORDED` and reconstructed, the same retired claim/fence is submitted as `INVOKE_RETIRED_TASK_BOUND_WORKER` with task state `COMPLETED`, worker state `RETIRED`, actor authority false, delegation false, validity-window false, capability disallowed, and permission absent. The consequence executor is forbidden from running. The canonical governance result must be `DENY`, and only then is `POST_RETIREMENT_STALE_FENCE_INVOCATION_REFUSED` submitted to Master Records using the denied transaction/manifest identity as evidence.

Terminal acceptance now requires that refusal transition to satisfy:

`state=RECORDED`
`reconstruction_status=PASS`
`required_evidence_validation_status=PASS`
`receipt_sha256 == reconstructed_receipt_sha256`

The WorkerCoordinator bridge rejects a governed-close response unless the refusal, zero executor invocation, refusal Master Records closure, and refusal reconstruction are all present. No second runtime, scheduler, dispatcher, WorkerCoordinator, custody store, credential path, authority plane, carrier requirement, or device prerequisite is introduced.

StegAgents PR #35 passed all three exact-head gates at `a1772001cf8e6ee97214944e009d624df8c54f2b` and merged as `f12abf3e062de95f7bbd5eb56247e91fdcd8481f`. This validates the source path only; source/CI validation must not be interpreted as authentic runtime evidence. The first still-unobserved authentic transition remains `FRESH_WORKERCOORDINATOR_CLAIM_FENCE_PREPARED_FOR_T`; only an actual machine-owned targeted one-shot can advance that predicate.
