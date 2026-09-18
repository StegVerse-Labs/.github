# SDK TT Purpose-Bound Worker Runtime Proof Mirror Handoff

Updated: 2026-09-18
Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`
Parent Goal Task ID: `SDK-TT-PURPOSE-BOUND-WORKER-CONSOLE-001`
Root Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
COSV ID: `71000000111111`
Repository: `StegVerse-Labs/.github`
Status: `ACTIVE / TEST CONTRACT DEFINED / EXISTING STEGAGENTS RUNTIME OWNER REUSED / AUTHENTIC RUNTIME PROOF PENDING`

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


## Cross-session convergence and repository reconciliation — 2026-09-18

The completed AgentEnvelope/MIR reconciliation is a non-blocking adjacent evidence reference: `MIR-AGENTENVELOPE-DERIVED-AUTHORITY-RECONCILIATION-001`. Its usable invariants are construction-bound lineage, lineage not implying authority, deterministic derivation not proving temporal ordering, and deterministic reconstruction being representable without a new Master Records evidence authority. Those invariants constrain this runtime test but do not add a runtime dependency or substitute for authentic WorkerCoordinator/InTr/runtime evidence.

SDK PR #266 merged the local-console implementation; SDK PR #267 merged its closeout; .github PR #2120 registered the console task; .github PR #2122 retired it and registered this runtime successor. Reconciliation PRs #2130 and #2138 were closed unmerged after concurrent main changes made their coordination bases stale. Their branch refs, together with prior merged-work branches, were aligned to newer main before retry. No other open related PR or issue was observed.

The monolithic Task Registry had advanced beyond the original generation-42 prompt while these shard records remained outside its task projection. This reconciliation registers the already-existing retired console identity and active runtime successor rather than minting replacements. The retired console task points to `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001` as its continuation so canonical check-in cannot revive the completed source/local lane.

This leaves one canonical active continuation only: `SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001`. It must continue through the existing `STEGAGENTS-GOVERNED-RUNTIME-001` path and must not create another lifecycle, runtime, scheduler, dispatcher, WorkerCoordinator, credential, transition, or custody authority plane.
