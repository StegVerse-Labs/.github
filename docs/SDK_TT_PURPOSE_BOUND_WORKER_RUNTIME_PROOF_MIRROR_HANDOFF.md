# SDK TT Purpose-Bound Worker Runtime Proof Mirror Handoff

Updated: 2026-09-18
Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`
Parent Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-CONSOLE-001`
Root Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `71000000111111`
Repository: `StegVerse-Labs/.github`
Status: `ACTIVE / SOURCE REFINEMENT MERGED / EXISTING STEGAGENTS WORKER+ADAPTER REUSED / AUTHENTIC RUNTIME PROOF PENDING`

## Purpose

Prove the stronger runtime proposition that the completed SDK local-console demonstration intentionally did not claim:

```text
one TT transition cell
-> declared bounded purpose
-> required worker capability
-> existing governed runtime admits materialization
-> purpose-bound worker exists for the needed interval
-> worker performs one tracked arbitrary task
-> execution/result state is receipted
-> worker retires or transforms when purpose ends
-> no live worker authority remains
-> durable output decomposes to records only
-> Master Records custody/reconstruction preserves the lifecycle
```

The initial arbitrary purpose remains deterministic and externally inspectable:

```text
purpose: analyze an exact supplied UTF-8 text payload for an integrity summary
required capability: text.integrity_summary
expected task output: SHA-256 + UTF-8 byte count + word count
```

## Non-competing execution owner

This task MUST reuse the existing governed worker/runtime chain owned by:

```text
STEGAGENTS-GOVERNED-RUNTIME-001
-> existing resident source refresh
-> existing resident dispatcher
-> existing targeted StegAgents consumer
-> existing WorkerCoordinator claim/fence
-> existing StegAgents governed worker/process adapter
-> existing StegCore/InTr admission
-> TV/TVC warrant/policy or credential semantics where required
-> existing Master Records custody/reconstruction
```

This task must not create another runtime, scheduler, dispatcher, WorkerCoordinator, InTr implementation, credential authority, Master Records authority, resident reachability task, or second user-operated device dependency.

## Test object

The runtime test begins from the exact SDK contract already merged by SDK PR #266:

```text
schema: stegverse.sdk.tt-purpose-bound-worker.v1
source merge: f0c3296650018d9cf298fa392c48315331a575fe
reference console command:
  stegverse worker-lifecycle --input inspection/examples/tt-purpose-worker.example.json
```

The local console packet is reference input/evidence only. It is not runtime authority and must not be treated as proof that a worker existed.

## Required authentic runtime chain

The authentic test must retain evidence for each distinct stage:

1. exact TT cell/request hash observed;
2. exact purpose and capability requirement observed;
3. WorkerCoordinator claim/fence for the test execution observed;
4. any required TV-issued warrant/pinned policy evidence verified;
5. StegCore/InTr admits the exact materialization transition;
6. an actual purpose-bound worker instance identifier is emitted;
7. worker instance is bound to exact purpose, capability, scope, and lifetime/retirement condition;
8. invocation starts only after materialization/admission;
9. the tracked arbitrary task result is produced from the exact input;
10. task result hash is bound to the same worker/transition identity;
11. retirement/transformation occurs after task completion or bounded failure;
12. a post-retirement observation establishes no continued live worker authority for this purpose;
13. lifecycle receipts preserve monotonic ordering;
14. Master Records custody is RECORDED for the authentic lifecycle;
15. reconstruction returns the same purpose/worker/result/retirement lineage;
16. final returned projection is a records-only packet and does not contain a live callable/executor object.

## Required evidence distinctions

```text
construction lineage != authority
purpose != authority
WorkerCoordinator claim != TV warrant
StegCore/InTr ALLOW != proof worker executed
worker materialized != task completed
task completed != continued authority
retirement receipt != historical erasure
records-only reconstruction != consequence re-execution
GitHub/CI != runtime authority
SDK local console PASS != authentic resident materialization
```

## Runtime relationship to STEGAGENTS-GOVERNED-RUNTIME-001

`STEGAGENTS-GOVERNED-RUNTIME-001` currently owns the reusable governed runtime path and remains blocked on authentic resident execution evidence. This successor must converge on that owner rather than bypass it.

If the existing CodeRepair-specific manifest/process adapter cannot represent the purpose-bound test without source refinement, the smallest allowed refinement is to expose this already-defined purpose-bound worker request through that same governed StegAgents runtime path. Such refinement may not duplicate runtime or authority semantics.

## Positive and falsification cases

The eventual runtime test should include at least:

```text
A. valid bounded purpose -> materialize -> execute -> retire -> records-only reconstruction
B. expired/closed purpose -> no renewed execution authority
C. task invocation before materialization/admission -> fail closed
D. result without matching worker/transition identity -> fail closed
E. retirement missing -> runtime proof incomplete
F. records-only packet that still contains a callable/live executor reference -> fail
```

## Completion criteria

This goal is complete only when authentic retained evidence proves the exact lifecycle above on the existing governed runtime path.

Source/console CI, fixtures, simulated workers, or documentation-only receipts do not satisfy completion.

## First authorized action

Reconcile the purpose-bound request shape against the existing `STEGAGENTS-GOVERNED-RUNTIME-001` StegAgents manifest/process-adapter contract. Identify the smallest source refinement, if any, needed to carry the exact TT cell/purpose/capability/lifetime tuple through the already-existing runtime. Do not attempt runtime execution until the existing resident/root/WorkerCoordinator prerequisites permit an authentic run.

## Source refinement reconciliation — 2026-09-18

StegAgents PR #21 merged as `4363333520f381370b7ae8f93b88a98bf8526aeb` after all exact-head workflows completed successfully:

```text
CI = success
Test Readiness = success
Cross-Agent Authority Validation = success
```

That immutable merge adds only the task-specific governed consequence module and focused StegAgents tests:

```text
src/purpose_bound_worker_runtime.py
tests/test_purpose_bound_worker_runtime.py
```

The `.github` refinement intentionally does **not** add another worker or process adapter. It extends the existing:

```text
worker_id: stegagents-governed-runtime-worker
adapter_ref: process:stegagents-governed-runtime-v1
```

with capability `stegagents_purpose_bound_worker_lifecycle`, and registers this successor task as a separate `HANDOFF_READY` task whose fragment contains `workers: []`. The shared worker selects the original proposal-only runtime for `STEGAGENTS-GOVERNED-RUNTIME-001` and the new purpose-bound module only for `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`.

The executable handoff carries the exact reference tuple from the already-merged SDK contract:

```text
schema: stegverse.sdk.tt-purpose-bound-worker.v1
purpose: Analyze a supplied text payload for a tracked integrity summary.
required_capability: text.integrity_summary
max_lifetime_seconds: 30
payload.text: StegVerse tracks this arbitrary local worker task.
```

Focused `.github` regression coverage checks shared-worker dispatch, exact request carriage, lifecycle ordering, records-only closeout, and absence of a duplicate worker/authority plane.

No authentic runtime execution has been attempted. The existing runtime owner's resident custody-root / WorkerCoordinator prerequisites remain authoritative gates. Source or CI success must not promote any authentic lifecycle predicate.

## Post-merge source state — 2026-09-18

The shared-worker `.github` refinement merged through PR #2150 as `00d5cadd3048dc1e44d8877a65ddc1ebf8fc6a29`.

The merged source now contains exactly one existing StegAgents worker/adapter path for both the original proposal-only owner and this bounded successor:

```text
worker_id: stegagents-governed-runtime-worker
adapter_ref: process:stegagents-governed-runtime-v1
successor fragment workers: []
```

The successor carries the exact `stegverse.sdk.tt-purpose-bound-worker.v1` request and validates ordered `MATERIALIZED -> INVOCATION_STARTED -> TASK_COMPLETED -> RETIRED` closeout with records-only/no-live-authority invariants. No standalone workflow, second worker, second adapter, scheduler, dispatcher, WorkerCoordinator, InTr implementation, credential authority, Master Records authority, or runtime plane was added.

GitHub reported PR #2150 mergeable/clean and merged the exact head. This repository exposed no PR workflow runs or commit statuses for that head, so the source record does not promote an automated `.github` CI result that was not observed. Focused regression source is merged; authentic runtime evidence remains entirely unclaimed.

The first remaining runtime prerequisite is inherited from `STEGAGENTS-GOVERNED-RUNTIME-001`: authentic resident custody-root reachability followed by a fresh WorkerCoordinator claim/fence. Until those existing prerequisites are observed, this task must not attempt or claim authentic worker materialization, InTr admission, task execution, retirement, or Master Records reconstruction.


## Derived lifetime semantics — Goal Prompt 4

The 30-second lifetime in the deterministic demonstration is **not** a production worker-lifetime rule. It is the computed result of this explicit demonstration budget:

```text
expected task execution                 6 s
known delay                             4 s
inferred unknown-delay reserve          8 s
records-enabled packet decomposition    7 s
safety reserve                          5 s
                                      ----
derived demonstration maximum          30 s
```

The request now carries `lifetime_policy.mode=DERIVED_COST_TASK_DELAY_BUDGET`. Production must recompute lifetime per intended task from task cost/work analysis, known delay, an explicitly stated inferred reserve for unknown delay, the allowance needed to decompose the worker into the records-enabled packet, and a safety reserve. There is no global production lifetime default.

The budget is an upper bound, not permission to remain live. Purpose completion or bounded failure may retire/decompose the worker earlier. Budget exhaustion closes the purpose; extension requires a newly governed recalculation. The lifetime calculation itself grants no WorkerCoordinator claim/fence, StegCore/InTr admission, TV/TVC warrant, runtime execution, or Master Records truth.

StegAgents PR #22 merged this fail-closed validation at `19b83dda96cf3c1d2fd5435daf8fce67a90c6228` after CI, Test Readiness, and Cross-Agent Authority Validation all passed. Authentic runtime execution remains unattempted.


## Derived lifetime post-merge reconciliation

StegAgents PR #22 is merged at `19b83dda96cf3c1d2fd5435daf8fce67a90c6228`. The `.github` projection and canonical registration merged through PR #2153 at `53133aaa65b432f022a95713c8ab3913a132394d`, from exact head `7d9f0751075c3f4e2ce7543d7e1fd961851d0386`.

Exact-head validation evidence:

```text
Validate Purpose-Bound Worker Derived Lifetime
run: 35402863215
job: 105786330855
conclusion: success

Cross-Task Coordination Validation - Non-Authorizing
run: 35402863119
conclusion: success
```

The source/lifetime refinement is therefore complete. No authentic resident execution was attempted. The first remaining runtime progression still belongs to the existing `STEGAGENTS-GOVERNED-RUNTIME-001` resident-root / WorkerCoordinator / TV warrant-policy / StegCore-InTr / Master Records chain; source or CI evidence does not satisfy those predicates.


## Coordination hygiene reconciliation — registry generation 64

`MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001` is restored as non-blocking adjacent evidence only. All surviving purpose-bound branch refs inspected are behind current `main` with zero unique commits and remain historical. Current `STEGAGENTS-GOVERNED-RUNTIME-001` evidence still does not establish an authentic retained resident root, targeted consumption, current WorkerCoordinator claim/fence, or Master Records runtime custody/reconstruction, so authentic purpose-bound execution remains unattempted.


## Healer checkpoint Master Records identity carriage repair — Goal Prompt 8

Current Task Registry generation 70 and this handoff were re-read before source mutation. The Goal remains ACTIVE and authentic purpose-bound lifecycle execution remains unattempted.

Tracing the existing Healer path exposed a concrete source defect after the already-documented fenced ProcessWorkerAdapter projection. The executable Healer handoff requires canonical Master Records custody, but `scripts/consume_healer_sovereign_scheduler_request.py` did not submit the projected checkpoint through `workers/canonical_state_transition_custody.py` and therefore did not retain either canonical Master Records lookup identity:

```text
transition_id
receipt_sha256
```

The existing consumer path is repaired without adding an API, custody store, scheduler, dispatcher, runtime, authority plane, or device dependency. After the existing targeted WorkerCoordinator execution returns, the consumer now:

```text
reads receipts/healer-sovereign-scheduler/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json
-> requires task_id + claim_id + fencing_token + transition_id
-> binds claim/fence/transition identity to the current WorkerCoordinator cycle
-> submits the exact checkpoint as canonical-json required evidence
-> uses the existing canonical state-transition custody client
-> requires RECORDED
-> requires reconstruction_status=PASS
-> requires required_evidence_validation_status=PASS
-> requires receipt_sha256 == reconstructed_receipt_sha256
-> retains transition_id + receipt_sha256 + master_record_ref in the existing consumption receipt
```

The required evidence item is `HEALER_FENCED_CHECKPOINT` and is bound to the checkpoint's existing worker transition ID. The checkpoint's exact canonical SHA-256 is both retained in transition evidence and used as the resulting state reference. This supplies the lookup identity needed by the existing Master Records read contract; it does not create a separate lookup/index API.

The existing consumption receipt fails closed as `MASTER_RECORDS_BOUNDARY` when custody/reconstruction is unavailable, incomplete, required evidence does not validate, or receipt/reconstruction digests differ. Source repair does not prove that a resident Healer cycle has run with this code.

Authentic continuation remains ordered:

```text
existing resident Healer cycle
-> fenced ProcessWorkerAdapter checkpoint projection
-> canonical Master Records RECORDED + reconstruction PASS + required-evidence PASS + digest equality
-> reconstruct exact checkpoint using carried receipt_sha256
-> validate child_receipt.resident_custody_root_observation_retention
-> require exactly one packet_state=RESIDENT_CUSTODY_ROOT_OBSERVED root
-> fresh WorkerCoordinator claim/fence
-> TV/TVC warrant/policy
-> InTr admission
-> existing purpose-bound lifecycle
```

No retained-root pointer, authentic Master Records receipt, WorkerCoordinator claim/fence for the purpose-bound task, TV/TVC warrant, InTr admission, worker materialization, task result, retirement, or records-only final packet is promoted by this source repair.
