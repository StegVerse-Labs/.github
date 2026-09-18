# SDK TT Purpose-Bound Worker Runtime Proof Mirror Handoff

Updated: 2026-09-18
Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`
Parent Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-CONSOLE-001`
Root Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `71000000111111`
Repository: `StegVerse-Labs/.github`
Status: `ACTIVE / MINIMUM SOURCE CARRIAGE REFINEMENT IMPLEMENTED / VALIDATION PENDING / AUTHENTIC RUNTIME PROOF PENDING`

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


## Source reconciliation — Goal Prompt 3 / registry generation 47

The existing governed runtime owner was inspected directly. The reusable execution chain already exists and remains the only allowed chain:

```text
STEGAGENTS-GOVERNED-RUNTIME-001
-> process:stegagents-governed-runtime-v1
-> workers/stegagents_governed_runtime_worker.py
-> StegAgents src/governed_coderepair_runtime.py
-> existing SDK / StegCore/InTr governance ingress
-> existing Master Records custody/reconstruction
```

The source gap was narrower than a new worker/runtime implementation. The existing request carried the WorkerCoordinator claim/fence and CodeRepair proposal, but it did not carry explicit TT-cell-derived `purpose`, `required_capability`, operation/payload scope, or bounded lifetime. That omission would prevent authentic later receipts from proving that materialization/execution belonged to the exact SDK test object.

Minimum refinement implemented:

```text
exact stegverse.sdk.tt-purpose-bound-worker.v1 request
-> validate source schema + TT cell + arbitrary tracked operation
-> derive/hash-bind transition_cell_hash
-> preserve purpose
-> preserve required_capability
-> preserve scope.operation_id / operation_class / payload_sha256
-> preserve max_lifetime_seconds
-> preserve retirement_condition
-> carry normalized tuple into the existing governance manifest
-> carry same tuple into declared execution context
-> return same tuple in governed result
-> retain same tuple in existing resident evidence receipt
```

StegAgents PR: `#20` on branch `sdk-tt-purpose-bound-worker-runtime-carriage-001`.

The existing `process:stegagents-governed-runtime-v1` adapter is reused. Its capability set is extended only with `purpose_bound_worker_context_carriage`; there is no second command, process adapter, scheduler, dispatcher, WorkerCoordinator, InTr path, credential path, Master Records authority, or device dependency.

This refinement is deliberately non-executing. It does **not** claim worker materialization, task invocation, retirement, Master Records runtime custody, or authentic InTr admission. Those remain gated by the existing resident-root and WorkerCoordinator prerequisites of `STEGAGENTS-GOVERNED-RUNTIME-001`.

### Current first runtime prerequisite

```text
AUTHENTIC_RESIDENT_CUSTODY_ROOT_OBSERVED
```

Only after the source carriage merges and exact-head validation passes should the existing runtime owner be used for the authentic lifecycle attempt.


## Generation-48 dependency reconciliation

The StegAgents source dependency is now merged:

```text
StegAgents PR #20
validated source head: f1bca87f85c29e58280557e69b6eba8e88765bb2
CI: 35398876490 PASS
Test Readiness: 35398876455 PASS
Cross-Agent Authority Validation: 35398876445 PASS
merge: 9ba16a39436686235e4dee965d29936364577f9c
```

Current Task Registry generation was re-read as `48` before continuing the `.github` carrier binding. The successor is still represented by its dedicated canonical task shard, COSV vector, handoff, and README projection; it is not silently inserted into the monolithic registry task array.

Remaining source action is only exact-head validation/merge of the existing `.github` worker + process-adapter carriage binding. Authentic runtime predicates remain unchanged and unclaimed.


## Generation-49 fence reconciliation

Task Registry generation 49 was re-read before further `.github` mutation. The generation-49 change is confined to the unrelated StegBrowser evidence lane; this goal's canonical main shard and handoff did not change. The existing branch therefore remains the applicable candidate, but merge is gated on focused exact-head validation of `tests/test_stegagents_governed_runtime_worker.py` rather than unrelated automatic workflow success.
