# SDK TT Richard Scenario Seam Runtime Mirror Handoff

Updated: 2026-09-19
Goal Task ID: `SDK-TT-RICHARD-SCENARIO-SEAM-RUNTIME-001`
Parent Goal Task ID: `SDK-TT-ATOMIC-TASK-WORKER-BINDING-001`
Root Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `51000000111111`
Repository: `StegVerse-Labs/.github`
Status: `ACTIVE / UNCLAIMED / TEST 3 AUTHENTIC RUNTIME PROOF PENDING`

## Purpose

Test 3 asks the original seam question under authentic StegVerse execution rather than at the SDK semantic-contract level:

> Does the seam proven by Test 2 continue to hold when the short-lived actor scenario is actually executed through StegVerse's existing governed runtime?

The exact semantic baseline is immutable Test 2:

```text
HANDOFF_READY task T + manifest-governed capability M
-> ACTIVATE(T)+CREATE_AND_BIND(W,T)
-> evidence closure
-> INVOCATION_STARTED
-> TASK_COMPLETED
-> CLOSE(T)+RETIRE(W,T)
-> records-only reconstruction
```

Test 3 must preserve that structure while requiring authentic evidence from the existing StegVerse runtime authorities.

## Required authentic chain

```text
registered task T + registered manifest/capability M
-> fresh WorkerCoordinator claim/fence
-> required TV/TVC warrant/policy verification
-> Interlock/InTr admits one atomic ACTIVATE(T)+CREATE_AND_BIND(W,T) transition
-> Master Records records and reconstructs that constitutive transition
-> only then may W invoke T
-> result remains bound to T/W/claim/fence/transition
-> CLOSE(T)+RETIRE(W,T)
-> Master Records records/reconstructs closeout
-> final records-only projection with no live task-bound authority
```

## Seam pass condition

The seam holds under Richard's scenario only if authentic retained evidence shows T existed before W; W was created for T in the same governed transition that made T ACTIVE; no split task/worker state is admitted; invocation follows constitutive-transition evidence closure; the result remains bound to the same T/W lineage; task close and worker retirement close the same binding; post-retirement continued task-bound authority is false; and Master Records reconstructs the lineage after W no longer exists.

## Falsification obligations

The authentic path must continue to fail closed for all eight Test 2 invalid conditions rather than weakening the semantic contract at runtime.

## Reuse boundary

Reuse only the existing `STEGAGENTS-GOVERNED-RUNTIME-001` runtime, WorkerCoordinator, TV/TVC, StegCore/InTr, and Master Records paths. No duplicate runtime, scheduler, dispatcher, worker coordinator, credential authority, transition authority, custody authority, or second user-operated device may be introduced.

GitHub/CI validates source and retained evidence only; it is not runtime authority.

## First actual transition

`FRESH_WORKERCOORDINATOR_CLAIM_FENCE`.

No Test 3 lifecycle predicate may be promoted from Test 1, Test 2, source validation, CI, or documentation.
