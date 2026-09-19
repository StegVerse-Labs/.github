# SDK TT Atomic Task-Worker Binding Mirror Handoff

Updated: 2026-09-19
Goal Task ID: `SDK-TT-ATOMIC-TASK-WORKER-BINDING-001`
Parent Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`
Root Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `20010000110000`
Repository: `StegVerse-org/StegVerse-SDK`
Status: `ACTIVE / CHECKED_OUT / TEST 2 IMPLEMENTATION`

## Purpose

Prove the replayable semantic proposition that task activation and creation/binding of the task-specific worker are one constitutive event for the tested executable-task class.

```text
registered HANDOFF_READY task T
+ manifest-governed worker capability M
-> one atomic ACTIVATE(T)+CREATE_AND_BIND(W,T) transition
-> evidence closure
-> invocation by W for T
-> result bound to T and W
-> CLOSE(T)+RETIRE(W,T)
-> records-only reconstruction
```

The test must preserve Test 1 unchanged and must not claim authentic WorkerCoordinator, TV/TVC, Interlock/InTr, resident runtime, or Master Records execution.

## Required positive invariants

- Before the constitutive transition, T is HANDOFF_READY and the task-specific worker does not exist.
- The transition simultaneously produces ACTIVE T and newly created W.
- T references W and W binds back to T.
- W is constrained by the supplied registered manifest/capability.
- No valid intermediate ACTIVE-without-worker or worker-without-ACTIVE-task state exists.
- Invocation is accepted only after the constitutive transition receipt exists.
- Result remains bound to the same T/W lineage.
- Task close and worker retirement terminate the same binding.
- Final output is records-only and independently replayable.

## Required falsification cases

1. ACTIVE without worker -> fail closed.
2. Worker without ACTIVE task -> fail closed.
3. Mismatched reciprocal task/worker binding -> fail closed.
4. Pre-created worker supplied to activation -> fail closed.
5. Invocation before constitutive transition closure -> fail closed.
6. Requested capability/authority exceeds manifest -> fail closed.
7. Task completes while bound worker remains live -> fail closed.
8. Records-only packet retains executor/callable -> fail closed.

## Evidence boundary

This goal is source/local semantic evidence only. It tests whether the seam contract holds at the replayable semantic level. Authentic governed execution belongs to a later successor and must not be inferred from SDK source or CI.

## Generation fence

This goal was registered after re-reading canonical Task Registry generation 77. Registration advances the proposed branch registry to generation 78.
