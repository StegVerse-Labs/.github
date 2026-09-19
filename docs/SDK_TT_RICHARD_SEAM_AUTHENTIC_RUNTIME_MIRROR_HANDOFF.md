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


## Test-3-only atomic activation source repair — proposed generation 85

The existing WorkerCoordinator/shared-Ste gAgents path is now repaired on the feature branch without changing the ordinary owner or purpose-bound worker semantics.

The Test 3 path now keeps the authoritative task in `HANDOFF_READY` with `claim_id=null`, `worker_id=null`, and `worker_instance_id=null` after fresh claim/fence custody. The proposed claim/fence and worker-instance identifier are carried only in a `pending_atomic_activation` envelope through the existing `ProcessWorkerAdapter`.

The shared StegAgents bridge recognizes this Test-3-only preactivation mode and invokes the existing `src.purpose_bound_worker_runtime` using the new atomic activation request. That runtime performs TV/TVC verification, submits the exact `ACTIVATE_TASK_AND_CREATE_BIND_WORKER` candidate through the existing StegCore/InTr path, and requires Master Records:

```text
state=RECORDED
reconstruction_status=PASS
required_evidence_validation_status=PASS
receipt_sha256 == reconstructed_receipt_sha256
```

before returning an activation projection with `invocation_started=false`.

WorkerCoordinator independently re-validates that retained activation evidence before atomically projecting `ACTIVE T <-> W`. Only after that projection does it invoke the separate post-activation execution request, which itself requires the exact closed constitutive activation evidence before recording `TASK_BOUND_WORKER_INVOCATION_STARTED` and `TASK_BOUND_WORKER_TASK_COMPLETED`.

A dedicated executable handoff and worker-registry fragment were added for Test 3. They import the existing `stegagents-governed-runtime-worker` provider; no worker, runtime, scheduler, dispatcher, WorkerCoordinator, custody path, transition authority, credential plane, or device dependency was added.

Authentic runtime execution remains unattempted until exact-head validation passes and the source repair is merged.
