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
