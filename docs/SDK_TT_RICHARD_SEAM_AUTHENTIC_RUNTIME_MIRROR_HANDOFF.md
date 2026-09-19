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
