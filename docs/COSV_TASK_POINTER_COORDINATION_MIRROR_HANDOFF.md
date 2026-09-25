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


## Functional Memory authentic assignment result — 2026-09-20 continuation

Continuation after merged generic manifest-provider repair `d7cdfec8f61bff06be4b05b69f788bd01e071daf` verified that:
- `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` remains canonically ACTIVE / UNCLAIMED;
- its exact resident request `RESIDENT-EXEC-SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` remains `REQUESTED`;
- the existing request targets `scripts/refresh_and_execute_resident_task.py --task-id SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001 --cosv-task-vector 71000000111111`;
- no canonical Master Records evidence was found for `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW`, `stegverse.worker-assignment-functional-memory/v1`, or an authentic assignment-review result for this exact task;
- no repository-retained prior `activation_deferred`, worker-task-admission, or assignment-review record for this exact task was found.

A direct targeted invocation of the existing resident path was attempted after the provider repair, but the authorized command surface was unavailable before command execution. Therefore no actual assignment matrix result exists from this continuation and no ALLOW/non-ALLOW disposition is inferred from source state.

No worker, claim, fence, task state, Functional Memory pack, Master Records receipt, or runtime predicate was created or promoted. The absence of an available command surface in this session is not a Task Registry predicate, task blocker, connected-device requirement, or authority condition.

The authentic next transition remains exactly one existing targeted WorkerCoordinator execution for this task. The first observed matrix disposition controls the branch:
- non-ALLOW -> zero worker/claim/fence materialization + Functional Memory Master Records custody and exact reconstruction;
- ALLOW -> do not manufacture a negative control; search only for an authentic prior same-task non-ALLOW disposition, and if none exists retain the conclusion that authentic non-ALLOW Functional Memory runtime proof has not yet occurred.


## Functional Memory authentic assignment attempt — 2026-09-20 14:18 CDT

After canonical handoff commit `3810500dc7eb2a34bff5a6aef860eaac69da0ada`, the already-staged targeted request for `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` was invoked again through the authorized resident command surface using the existing `refresh_and_execute_resident_task.py` entrypoint and exact COSV vector `71000000111111`.

The command surface rejected the request before command execution. No WorkerCoordinator assignment review ran, so no authentic assignment matrix result exists from this attempt.

A canonical evidence check immediately afterward found no new:
- `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW`;
- `WORKERCOORDINATOR_CLAIM_FENCE_BOUND`;
- `stegverse.worker-assignment-functional-memory/v1`;
- retained resident-targeted execution receipt for this exact task.

Therefore no ALLOW/non-ALLOW disposition is inferred, no negative control is manufactured, and no worker/claim/fence/task state/Functional Memory/Master Records predicate is promoted. The execution-surface unavailability remains external to task semantics and is not a Task Registry blocker or dependency.


## Functional Memory canonical custody transport verification — 2026-09-20

End-to-end inspection confirms Functional Memory uses the same canonical state-transition custody path as other WorkerCoordinator transitions:

- `heartbeat_runtime/worker_assignment_functional_memory.py` builds `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW` with `build_state_receipt(...)` and submits it with the shared `workers/canonical_state_transition_custody.py::submit_state_receipt(...)`.
- `WORKERCOORDINATOR_CLAIM_FENCE_BOUND` in `heartbeat_runtime/worker_runtime_legacy.py` uses the same `submit_state_receipt(...)` client.
- HTTP custody posts the common `stegverse.master-records.state-transition-submission/v1` envelope to `POST /api/master-records/state-transitions`; local custody invokes the same Master Records `record_receipt(...)` implementation.
- Master Records stores every canonical transition receipt in `canonical_state_transition_receipts` keyed by exact canonical receipt SHA-256 and stores required evidence in `canonical_state_transition_required_evidence`.
- `record_receipt(...)` re-reads canonical receipt bytes and evidence bytes immediately after persistence, returns `state=RECORDED`, `reconstruction_status=PASS`, `required_evidence_validation_status=PASS`, `master_record_ref`, and exact `receipt_sha256/reconstructed_receipt_sha256`.
- Later `reconstruct_state_receipt(receipt_sha256)` uses the same HTTP reconstruction endpoint or local canonical tables and requires exact receipt digest equality plus required-evidence PASS before Functional Memory is reusable.

The inspection also identified the first concrete current resident-carriage defect: `scripts/consume_stegagents_governed_runtime_targeted_request.py::clean_env(...)` preserves Master Records source-root discovery variables but strips both supported custody transports' runtime configuration. It does not preserve HTTP `STEGVERSE_MASTER_RECORDS_ENDPOINT` / `STEGVERSE_MASTER_RECORDS_TOKEN`, and it does not preserve local-binding `MASTER_RECORDS_DB` / `MASTER_RECORDS_RECEIPT_KEY` / `MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS`. Therefore the existing targeted SDK consumer can reach `submit_state_receipt(...)` with neither canonical custody transport configured, causing `CANONICAL_MASTER_RECORDS_CUSTODY_SURFACE_UNAVAILABLE`.

This is a transport-carriage defect in the existing targeted consumer, not a Functional Memory schema/storage divergence and not a new runtime/custody requirement.


## Functional Memory immediate-predecessor lineage enforcement — 2026-09-20

Review of the merged Functional Memory path found a fail-closed ordering defect: when a retained `task.functional_memory.receipt_sha256` could not be reconstructed, assignment review was forced to BLOCK/DENY but the non-ALLOW recorder could still create a successor `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW` receipt pointing at the unreconstructable predecessor.

The existing path is repaired without adding a runtime, scheduler, WorkerCoordinator, authority plane, credential path, or custody store:

```text
retained Functional Memory pointer
-> exact Master Records reconstruction
-> RECORDED/PASS/evidence PASS/digest equality required
-> only then assignment review
-> only then ALLOW or a successor non-ALLOW Functional Memory transition
```

If predecessor reconstruction fails, the admitted WorkerCoordinator now stops at `FUNCTIONAL_MEMORY_RECONSTRUCTION_BOUNDARY` before creating a new admission consequence or Functional Memory sequence. The Functional Memory recorder independently rejects any successor write when a prior pointer exists but the assignment transition does not prove that prior memory was validly reconstructed and consumed.

The existing canonical Master Records subject/transition query is also used as a non-authorizing recovery index when the mutable task pointer is absent. Recovery is accepted only when every retained `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW` record reconstructs successfully, sequences are contiguous from 1, and each successor receipt's `prior_state_ref_or_hash` exactly names the preceding receipt digest. Only after that full chain passes is `task.functional_memory` restored as a convenience pointer to the latest retained record.

Master Records remains the custody/reconstruction authority; the recovered task pointer grants no authority.


### Functional Memory lineage repair merged and validated

The immediate-predecessor enforcement repair merged in `StegVerse-Labs/.github#2367` as:

```text
57415095b055ba04451207fc659bee98855f587a
```

Exact-head validation on `4bb4964d7135af4472543975690effba0b75514d`:
- Test 3 Richard Seam Acceptance run `35539091949`: PASS;
- validate-deepseek-resident run `35539091944`: PASS;
- Validate KV AI Memory Resident Binding run `35539091952`: PASS;
- Cross-Task Coordination Validation run `35539091988`: PASS.

The regression suite now proves an unreconstructable predecessor cannot call `submit_state_receipt` for a successor Functional Memory transition, cannot advance sequence, and cannot mint worker/claim/fence consequences. Pointer recovery is accepted only from the existing canonical Master Records query/reconstruction path after contiguous sequence and predecessor-digest-chain validation.

This merge is source/contract validation. It does not claim that an authentic runtime Functional Memory predecessor or successor transition executed.


## Functional Memory authentic-path first failure — 2026-09-21

Canonical Task Registry had advanced to generation 150 before this continuation. No Functional Memory runtime result was inferred from the earlier source/CI repair.

The only current unclaimed `HANDOFF_READY` task on the generic WorkerCoordinator seam is `STEGFIN-LIVE-ENTRY-003`. Its retained resident evidence records the first authentic pre-assignment failure:

```text
activation_requested
-> activation_deferred
reason=EXECUTOR_NOT_RESOLVED
```

Source reconciliation showed the concrete cause. The mutable/monolithic WorkerCoordinator registry retained `stegfin-live-entry-inventory-worker` with only `runtime_observation` and `bounded_repository_mutation`, while the current executable handoff requires those capabilities plus `stegfin_live_entry_inventory_observation`. The repository fragment already carried the third capability, but the existing fragment loader is intentionally append-only and therefore did not update an already-present worker row. The same fragment also retained policy `shwp-single-hb-stegfin-live-entry-v0.3` while the canonical handoff is `v0.6`.

The bounded repair extends the already-existing unclaimed-`HANDOFF_READY` preclaim reconciliation seam. It may update only an already-existing `AVAILABLE` worker when worker ID, adapter, executor type, and authority source are unchanged, and only when the fragment capabilities satisfy the current handoff. It changes only static capabilities/profile metadata and grants no worker identity, assignment, claim, fence, timing, lease, credential, execution, transition, or custody authority. Claimed/timed tasks remain immutable to this reconciliation.

This repair addresses only the first concrete existing-path failure before the Functional Memory assignment seam. It does not claim that a fresh resident assignment disposition has yet occurred.


### Functional Memory authentic-path repair merge — 2026-09-21

The first retained authentic failure for the only current generic unclaimed WorkerCoordinator candidate, `STEGFIN-LIVE-ENTRY-003`, remained `activation_deferred / EXECUTOR_NOT_RESOLVED` at heartbeat epoch 29. No later authentic assignment review or `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW` receipt was found after source inspection.

The bounded preclaim worker-registration repair was rebased onto current canonical main and merged through PR #2392 as `b0cd6274bbd7e536a91322a0f42f2f58df747aac` from exact head `57b626a548ee97b14d3d9e80ed0202aa70745ca1`.

Exact-head validation:
- Test 3 Richard Seam Acceptance `35567657664`: PASS;
- Cross-Task Coordination Validation `35567657698`: PASS;
- Validate KV AI Memory Resident Binding `35567657662`: PASS;
- validate-deepseek-resident `35567657765`: PASS.

The repair reuses the existing preclaim reconciliation seam and changes no live claim/fence/timing/lease state. It refreshes only static capability/profile metadata for the already-existing AVAILABLE worker when identity, adapter, executor type, and authority source are unchanged and the refreshed fragment satisfies the canonical handoff.

A fresh authentic assignment disposition has not yet been observed after the merge. Therefore the requested non-ALLOW/ALLOW branch and the controlled missing-local-pointer recovery exercise are not advanced yet. The pointer-recovery exercise must retain a real same-task canonical Master Records Functional Memory history; manufacturing that predecessor would violate the requested authentic-state-dependent sequence.


### Functional Memory post-repair resident observation — 2026-09-21

Canonical Task Registry had advanced to generation 160 before this continuation.

Fresh repository-retained resident evidence was checked specifically for `STEGFIN-LIVE-ENTRY-003` after merged repair `b0cd6274bbd7e536a91322a0f42f2f58df747aac`. No post-repair assignment review, `WORKERCOORDINATOR_ASSIGNMENT_NON_ALLOW` receipt, claim/fence, or newer same-task runtime result is retained. The latest retained same-task runtime result remains the pre-repair heartbeat-29 `activation_deferred / EXECUTOR_NOT_RESOLVED` event.

The existing post-repair source/runtime path was traced before declaring another failure:
- `scripts/refresh_sovereign_worker_runtime_source.py` watches/copies `heartbeat_runtime/**` and `control/worker-registry.d/**`, preserves mutable runtime state, and records exact `source_git_head` in `worker-source-refresh.latest.json`;
- `install_sovereign_worker_source_refresh_service.py` watches those source paths, runs resident request dispatch after refresh, then restarts/starts the existing `stegverse-worker-runtime.service`;
- `scripts/run_worker_runtime.py` enters the existing WorkerCoordinator cycle, whose fragment application runs before task evaluation.

No new deterministic defect was identified in that chain. Therefore absence of a post-repair resident receipt is not promoted to failure and no additional runtime/source seam was changed.

The next admissible evidence is the first authentic post-repair source-refresh or WorkerCoordinator-cycle result proving whether the same `STEGFIN-LIVE-ENTRY-003` task now resolves the refreshed existing worker registration. Only that authentic result may choose the non-ALLOW/ALLOW branch. Missing-local-pointer recovery remains downstream of a real retained same-task Functional Memory receipt.


### Functional Memory control-plane package carriage repair — 2026-09-21

Tracing the existing resident path from canonical source to the far-side/local resident source found the first deterministic post-repair break before `worker-source-refresh.latest.json`: `scripts/build_control_plane_source_package.py` did not carry the canonical admitted WorkerCoordinator / Functional Memory delta or the corrected `STEGFIN-LIVE-ENTRY-003` fragment.

The existing TVC-authorized control-plane relay could therefore succeed while still materializing a source set incapable of reproducing the merged Functional Memory repair. The bounded repair adds only the already-canonical files required by that existing execution seam:

- `heartbeat_runtime/worker_runtime.py`
- `heartbeat_runtime/admitted_worker_runtime.py`
- `heartbeat_runtime/worker_assignment_functional_memory.py`
- `workers/canonical_state_transition_custody.py`
- `control/worker-registry.d/stegfin-live-entry-003.json`

No transport, relay, runtime, WorkerCoordinator, scheduler, dispatcher, authority plane, credential path, custody store, deployment plane, device dependency, or invocation is added. The package remains an allowlisted content-addressed source delta and the downstream source-refresh/worker-service path remains unchanged.


### Functional Memory package-carriage repair merged — 2026-09-21

PR #2460 merged as `12e1dd5630c6d1b729c3089d9a53325ca357c24b` from exact head `b754fbacc11f025cb84610b8f801dfa7e4864b3a`.

Exact-head validation:
- Validate Purpose-Bound Worker Derived Lifetime `35602677794`: PASS;
- validate-deepseek-resident `35602677909`: PASS;
- Validate KV AI Memory Resident Binding `35602677907`: PASS;
- Test 3 Richard Seam Acceptance `35602677880`: PASS.

The existing content-addressed control-plane source package now carries the minimum complete Functional Memory execution delta plus the corrected `STEGFIN-LIVE-ENTRY-003` fragment. No authentic post-repair relay/materialization/source-refresh/assignment result is claimed by this merge. The next admissible state transition must come from the existing TVC-authorized control-plane relay and far-side source materialization, followed by the existing source refresh and WorkerCoordinator cycle.


### Existing control-plane relay continuation seam — 2026-09-21

Tracing `RT-CONTROL-PLANE-SOURCE-PACKAGE-001 -> RTC-INTERLOCK-INTR-TRANSPORT-008 / TVC relay` after the five-file carriage repair found the next deterministic break: the reusable package runner intentionally stopped after writing `outbox/control-plane-source-package/<source_identity>.json`. The bounded StegOS relay CLI existed, but no production caller consumed that outbox.

The repair keeps the same reusable task invocation and, only when the already-retained `STEGVERSE_RELAY_EGRESS_AUTHORIZATION`, `STEGVERSE_RELAY_EGRESS_BINDING`, and `STEGVERSE_STEGOS_ROOT` inputs are present, continues through the existing `scripts/execute_control_plane_source_package_relay.py`. It issues no authorization, creates no binding or transport, and adds no scheduler/dispatcher/runtime.

Acceptance is fail-closed: the packaged manifest must include all five Functional Memory/StegFin files with exact digests, the far-side receipt must return `SOURCE_MATERIALIZED_VERIFIED` for the exact `source_identity`, and `source_materialization.files[]` must reproduce the exact packaged digest and size for every required file before the continuation receipt is retained.


### Existing control-plane relay continuation repair merged — 2026-09-21

PR #2482 merged as `5f605bf76904c25fd0041be558d0eac085ddcae3` from exact head `867c7f47e8073a87d094fdc631e1565fae93a63b`.

Exact-head validation:
- Validate Purpose-Bound Worker Derived Lifetime `35605682837`: PASS;
- validate-deepseek-resident `35605682688`: PASS;
- Validate KV AI Memory Resident Binding `35605682942`: PASS;
- Test 3 Richard Seam Acceptance `35605682614`: PASS.

The reusable source-package lifecycle now continues through the already-existing StegOS control-plane relay only when the already-issued TVC authorization, already-admitted relay binding, and existing StegOS root are present. It creates no new authorization, binding, transport, runtime, scheduler, dispatcher, WorkerCoordinator, credential path, custody store, or invocation type.

Far-side acceptance is fail-closed: `SOURCE_MATERIALIZED_VERIFIED` must name the exact package `source_identity`, and `source_materialization.files[]` must exactly reproduce path, sha256, and size for all five Functional Memory/StegFin carriage files before the continuation receipt is retained.

No authentic post-merge relay/materialization, worker-source-refresh, WorkerCoordinator assignment disposition, Functional Memory receipt, claim, or fence is promoted by this source repair.


## Generation-227 full-shard cross-goal audit follow-up

The existing `STEGVERSE-CANONICAL-WORK-COORDINATION-001` / COSV `10100000100000` source-only PR #2677 records the initial 35 user-supplied IDs and adds a reusable read-only entire-local-shard/aggregate/COSV-index reporter (`scripts/audit_canonical_task_projections.py`) with regression coverage. It does not silently project checked-out owners, mint IDs, infer missing GitHub-visible receipts as failed runtime or claim a new scheduler. Check the report's actual overlaps and use existing checked-out task owners for any state-changing repair. Source snapshot at this update: Registry generation 227; refresh before execution and use Master Records for observed consequence evidence.
