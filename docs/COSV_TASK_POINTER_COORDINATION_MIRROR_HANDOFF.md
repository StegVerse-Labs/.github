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


## WorkerCoordinator Functional Memory assignment contract

Worker assignment is a canonical state transition determined from the current task state. The existing WorkerCoordinator admission packet is bound to the canonical Task Registry generation and task.v1 COSV projection before assignment consequence is selected.

The canonical bifurcation is:

```text
assignment candidate
-> assignment/admissibility review
   -> ALLOW: carry task-generation/COSV + prior-memory context into the existing claim/fence assignment record and worker path
   -> non-ALLOW: materialize Functional Memory records pack -> canonical Master Records state-transition custody
```

Functional Memory is reconstructable prior state, not narrative history. A retained non-ALLOW pack binds the exact task identity, Task Registry generation, generation-bound COSV identifier, admission predicate matrix + digest, disposition/reasons, assignment request identity, and explicit worker_materialized=false / claim_minted=false / fence_minted=false facts. The next assignment review must reconstruct the retained Master Records receipt with exact digest equality and required-evidence PASS before consuming it. If reconstruction fails, assignment fails closed and no worker authority artifact is minted.

This contract creates no scheduler, runtime, WorkerCoordinator replacement, Interlock/InTr replacement, credential path, or custody store. WorkerCoordinator remains claim/fence authority, Interlock/InTr remains governed transition authority, TV/TVC remains credential authority, and Master Records remains custody/reconstruction authority.


## Functional Memory implementation evidence — 2026-09-19

PR #2289 merged the canonical WorkerCoordinator Functional Memory assignment-transition contract as `9c48c12fa38b1bfece448c878843ee352429d83d`.

Exact-head validation evidence:
- Test 3 Richard Seam Acceptance run `35469405536`: PASS; the run explicitly executed `tests/test_worker_assignment_functional_memory.py` and the bundled .github test set reported 29 passed.
- Cross-Task Coordination Validation run `35469405509`: PASS.

Merged behavior:
- assignment review is bound to task identity, canonical Task Registry generation, and task.v1 COSV context;
- only ALLOW may continue into the existing WorkerCoordinator claim/fence assignment path;
- every non-ALLOW assignment disposition materializes a Functional Memory records pack through the existing canonical Master Records state-transition custody client;
- retained Functional Memory must reconstruct with exact receipt digest equality and required-evidence PASS before later assignment review may consume it;
- the ALLOW branch carries the same task-generation/COSV and prior-memory context into the existing worker-assignment record.

No authentic runtime assignment, non-ALLOW records-pack emission, or later-generation memory reuse is claimed by this source/CI merge alone.


## Functional Memory authentic runtime exercise boundary — 2026-09-20

The source contract remains merged and validated, but this session did not obtain an authentic WorkerCoordinator/Master Records runtime result.

Runtime-path investigation established:
- `COSV-TASK-POINTER-RUNTIME-ENFORCEMENT-001` is registered in the canonical Task Registry and resident request dispatcher but is not present in the checked-in WorkerCoordinator registry, so using it would fail before the assignment/admissibility seam and would not exercise Functional Memory.
- `SHWP-ECOSYSTEM-CHAT-INFERENCE-001` is HANDOFF_READY but its canonical handoff explicitly uses the dedicated independent parent executor rather than the generic WorkerCoordinator assignment seam where Functional Memory is implemented.
- `STEGFIN-LIVE-ENTRY-003` is a genuine generic WorkerCoordinator candidate whose current dependency state would produce non-ALLOW, but advancing its predecessor would require substantive StegFin/runtime work unrelated to this Functional Memory proof; no StegFin state was modified.
- No canonical Master Records receipt matching `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW` or `stegverse.worker-assignment-functional-memory/v1` was found for the candidate tasks.
- Direct invocation of the authorized resident command surface was unavailable to this session before any command executed. This is an execution-surface limitation only; it is not recorded as a Task Registry predicate, connected-device dependency, blocker, or reason to alter task state.

Therefore no claim/fence, worker, task state, Functional Memory pack, or Master Records state was fabricated or advanced. The next authentic proof remains: run one already-registered generic WorkerCoordinator task whose current canonical matrix resolves non-ALLOW, require Functional Memory custody `RECORDED + reconstruction_status=PASS + required_evidence_validation_status=PASS + receipt_sha256==reconstructed_receipt_sha256`, then change only the real same-task predicate that caused the non-ALLOW result and re-evaluate that same task so the retained Functional Memory is reconstructed before any subsequent ALLOW worker materialization.


## Functional Memory generic manifest-assignment repair — 2026-09-20

While continuing authentic Functional Memory proof, the first generic manifest-driven assignment defect was isolated before any runtime state was changed:

- manifest-bound task `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` correctly references shared provider fragment `control/worker-registry.d/stegagents-governed-runtime-001.json`;
- targeted WorkerCoordinator fragment loading already composes that provider fragment;
- the provider row had no `capability_profile_ref`, so canonical non-fixture `_worker_for` necessarily returned no eligible worker;
- after adding the canonical profile, exact-head validation exposed the next directly coupled defect: the manifest requires both `stegagents_purpose_bound_worker_lifecycle` and `stegagents_purpose_bound_worker_state_graph`, while the provider advertised only the lifecycle capability.

PR #2348 repaired only that generic provider-registration seam and merged as `d7cdfec8f61bff06be4b05b69f788bd01e071daf` from exact head `da1d35d343dd53d2443763eb939c2fcc95ff4ca3`. Validation run `35528296653` PASS proves the manifest-bound task and shared provider now resolve through the real WorkerCoordinator eligibility loader with no claim/fence created by capability matching.

The repair adds no Functional Memory implementation, worker runtime, scheduler, authority plane, credential path, custody store, or task-specific executor.

Post-merge canonical evidence search found no authentic `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW`, `stegverse.worker-assignment-functional-memory/v1`, or `WORKERCOORDINATOR_CLAIM_FENCE_BOUND` receipt for `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`. A direct resident targeted invocation was attempted after merge, but the authorized command surface was unavailable before command execution. This condition is not a Task Registry predicate or task blocker and does not alter the task state.

The remaining authentic predicate is unchanged: execute the existing targeted WorkerCoordinator task on an authorized resident surface; if its current admissibility matrix resolves non-ALLOW, require Functional Memory Master Records custody with no worker/claim/fence; then modify only the exact same-task predicate that caused the non-ALLOW state and re-evaluate the same task, requiring prior Functional Memory reconstruction before any ALLOW materialization.
