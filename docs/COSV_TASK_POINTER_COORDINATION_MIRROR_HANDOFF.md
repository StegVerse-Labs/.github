# COSV Task Pointer Coordination Mirror Handoff

Status: SOURCE_POLICY_ACTIVE_RUNTIME_ENFORCEMENT_PENDING
Repository: `StegVerse-Labs/.github`
Canonical policy: `data/task-coordination-policy.json`
COSV profile: `management/COSV_PROFILE_V1.json#task.v1`
COSV task index: `control/task-vector-index.json`
Canonical task registry: `data/canonical-task-registry.json`
Reusable task registry: `data/reusable-task-registry.json`
Reusable construct contract: `data/reusable-task-ephemeral-construct-contract.json`

## Purpose

A compact StegVerse task continuation prompt requires only two canonical values:

```text
task_id
cosv_task_vector
```

The task ID is the stable identity. The 14-position COSV `task.v1` vector is the compact current-state projection. Everything else that is already canonical must be resolved from the task registry, COSV source-state vector, applicable mirror handoffs, Master Records, WorkerCoordinator claim/fence state, cross-task coordination, receipts, runtime-profile map, reusable-task identities, and other referenced evidence.

A prompt must not restate canonical task prose merely to transport task state between sessions. Additional prompt data is permitted only for information that is not yet canonically resolvable and must itself be materialized into canonical state before session close.

## Resolution contract

On receipt of `task_id + cosv_task_vector`, the receiving session/runtime must:

1. verify the vector is a valid `task.v1` vector and is bound to the supplied task ID;
2. resolve the canonical task record and its source vector/evidence references;
3. resolve applicable `*_MIRROR_HANDOFF.md` continuation records;
4. reconcile Master Records observed reality;
5. resolve active WorkerCoordinator claim/fence state;
6. resolve dependencies, adjacent tasks, shared predicates, systemic incidents, and non-collision boundaries;
7. resolve applicable reusable-task identities and invocation parameters;
8. derive and bind the invocation-specific RTG -> GTG -> TT construct where reusable execution is required;
9. reuse existing implementation/evidence rather than recreate it;
10. select the highest-priority admissible nonduplicate work;
11. execute only through the existing authority boundaries.

Neither the task ID, COSV vector, reusable identity, derived construct, nor manifest binding grants execution, admission, claim/fence, credential, transition, custody, publication, or runtime authority.

## Reusable identity construct

Reusable tasks are durable identities. Parameters are invocation-specific and determine the exact derived construct. The canonical lifecycle is:

```text
Reusable identity = durable
Parameters = invocation-specific
TT/RTG/GTG construct = derived
Runner = ephemeral where possible
Evidence = durable
Canonical task/COSV identity = durable when tracking is needed
Manifest = bound
Receipts = chained
Recording = at necessary levels
```

A runner expires before recording continuity expires. If required recording remains, a residual non-executing TT/RTG/GTG construct may remain solely to preserve identity/manifest binding, carry chained receipts, project required task/COSV state, complete required scoped recording, carry evidence to Master Records, and support reconstruction verification.

After required recording and Master Records custody/reconstruction are complete, the residual construct is displaced through **entropy recovery**. Entropy recovery does not delete durable evidence or Master Records history and does not reactivate the original runner.

Canonical source: `docs/REUSABLE_TASK_EPHEMERAL_CONSTRUCT_MIRROR_HANDOFF.md`.

## Adjacent-task derivation

When work on the current task or goal reveals a distinct necessary piece of work that is not already canonically tracked, the system should create a new adjacent task rather than expanding the originating prompt or silently changing the meaning of the original task.

Before creating a new task it must:

- search for equivalent or already-adjacent work;
- reuse existing predicates, claims, evidence, implementations, and tasks when equivalent;
- preserve the root correlation and same-goal relationship;
- preserve authority and non-collision boundaries;
- avoid turning a dependency or evidence gap into a duplicate implementation owner.

A genuinely new adjacent task must receive:

- a unique task ID;
- a canonical Task Registry record;
- parent/adjacent/root-correlation relationship to the originating goal/task;
- a COSV `task.v1` state-vector projection;
- applicable handoff projection;
- runtime requirements when applicable;
- existing evidence references and known completion predicates.

Creation of the task is coordination only. WorkerCoordinator still owns execution claim/fence, Interlock/InTr still owns governed task transitions, Master Records still owns observed reality/reconstruction, and TV/TVC remains credential authority.

## Prompt form

Preferred continuation payload:

```text
<TASK_ID>
<COSV_TASK_VECTOR>
```

If multiple tasks are intentionally combined in one session, repeat the same two-field pair for each task. Relationship grouping should be resolved canonically wherever already recorded. Temporary relationship information may accompany the pair only until it is projected into canonical coordination state.

## Session-close invariant

No unique task continuity should remain only in chat prose. Before session close:

- newly discovered distinct same-goal work must be registered as adjacent task(s);
- current vectors must be projected through the canonical COSV path;
- reusable invocation evidence must reach required recording levels;
- residual recording constructs must remain only until Master Records custody/reconstruction allows entropy recovery;
- applicable handoffs/indexes/docs must be reconciled;
- the successor prompt should collapse back to `task_id + cosv_task_vector` for each task that still requires continuation.

## README completeness

The pointer interface change is covered by `receipts/preflight/COSV-TASK-POINTER-ADJACENT-DERIVATION-001.json`. The reusable identity/ephemeral construct and entropy-recovery extension is covered by `receipts/preflight/REUSABLE-TASK-EPHEMERAL-CONSTRUCT-001.json`; `README.md` is updated in the same change set because the extension materially changes reusable-task invocation, runner lifetime, recording continuity, and final displacement semantics.
