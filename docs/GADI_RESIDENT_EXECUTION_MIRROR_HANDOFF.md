# GADI Resident Execution Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
Umbrella goal: `GOVERNED-MULTILANE-MANIFOLD-ACTIVATION-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `SOURCE_CONTRACTS_RECONCILED / WORKERCOORDINATOR_REGISTRATION_REPAIR_MERGED / WORKER_PROTOCOL_BRIDGE_IN_VALIDATION / AUTHENTIC_RESIDENT_EXECUTION_PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and is not superseded.

Merged trajectory includes runtime-evidence materialization, local source resolution, native StegOS command compatibility, canonical InTr admission compatibility, WorkerCoordinator claim/fence compatibility, governed actuator-observation projection, the StegOS controlled-output receipt seam, and the parent source-chain reconciliation. Most recently, PR #1388 repaired targeted WorkerCoordinator registration and merged as `261b1636db05baa3d34072236557618e9607b5e7` after repaired exact head `d2d361327a6a48a1d9afc1109f6506b23fce82eb` passed organization-control, deterministic repository-suite diagnostics, and Heartbeat validation.

PR #1388 resolved five structural claimability defects without creating runtime evidence:

1. projected existing `INDEPENDENT_TASK_CONTROL` authority into the registry admission row;
2. added a conservative finite 16-beat LOW-confidence non-empirical cost basis;
3. removed parent/coordination/runtime authority identifiers from terminal worker dependencies and preserved them as coordination refs;
4. aligned the worker to `process:gadi-resident-execution-v2-preflight-gated`;
5. bound the worker to the narrow `gadi-resident-defensive-execution-v1` capability profile.

The canonical runtime evidence state still remains `HANDOFF_READY` with no authentic current claim/fence, InTr admission, runtime binding, or controlled actuator result observed.

## Canonical execution chain

```text
SOURCE RESOLUTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
```

The four runtime source classes remain independently owned by StegOS command materialization, canonical InTr admission, WorkerCoordinator claim/fence assignment, and the controlled pre-authorized actuator observation plane.

## Post-claim protocol audit — bridge now in validation

After PR #1388 made the GADI task structurally claimable, inspection of the actual ProcessWorkerAdapter invocation path found a post-claim integration mismatch.

The canonical WorkerCoordinator correctly creates the fresh claim/fence before invoking the process adapter. `ProcessWorkerAdapter` then sends the current claimed task row to the worker through `stegverse.worker-invocation/v0.1` stdin, including the current `claim_id` and `fencing_token` in both the task and invocation scope.

The configured GADI adapter, however, directly invoked `scripts/dispatch_gadi_resident_execution.py`. That dispatcher:

- did not read process-worker stdin;
- therefore could not project the just-created WorkerCoordinator claim/fence into `state/gadi-resident-execution/source/worker-claim.json`;
- emitted `stegverse.gadi-resident-dispatch/v1`, while `ProcessWorkerAdapter` requires `stegverse.worker-response/v0.1`;
- returned nonzero while evidence was incomplete, which ProcessWorkerAdapter treats as a process failure rather than a normal relinquishable `HANDOFF_READY` worker response.

This meant the canonical WorkerCoordinator could lawfully create the claim but the existing GADI process worker could neither consume that exact claim nor speak the required worker-response protocol.

## Worker protocol bridge

Current branch:

`gadi-worker-protocol-bridge-001`

New source:

`workers/gadi_resident_execution_worker.py`

The bridge is deliberately not a new runtime. It executes inside the existing `ProcessWorkerAdapter` sandbox and:

1. requires `stegverse.worker-invocation/v0.1`;
2. requires task `GADI-RESIDENT-EXECUTION-001` to already be `ACTIVE`;
3. requires a non-empty current claim, worker identity, worker instance and positive fence;
4. requires exact invocation-scope claim/fence equality and claim-generation/fence equality;
5. passes the exact already-created WorkerCoordinator task row to the existing dispatcher;
6. maps `AUTHENTIC_RUNTIME_EVIDENCE_CONSUMED` to a standard `COMPLETED` worker response;
7. maps any non-consumed/fail-closed dispatcher state to `HANDOFF_READY`, causing the existing WorkerCoordinator to relinquish the claim rather than retain stale ownership;
8. grants no InTr, credential, claim/fence, runtime, actuator, deployment or Master Records authority.

## Current-claim staging order

`scripts/dispatch_gadi_resident_execution.py` now accepts an optional already-created `current_worker_claim` row from the worker bridge.

The dispatcher still runs the existing local source resolver first. Only after source resolution completes does it stage the exact current task row into:

`state/gadi-resident-execution/source/worker-claim.json`

This ordering prevents a stale `source-locators.json` worker-claim entry from overwriting the fresh WorkerCoordinator claim. The staging helper validates task identity, `ACTIVE` state, worker identity/instance, positive fencing token, and claim-generation/fence equality. It never manufactures any of those values.

The existing materializer already accepts an authentic WorkerCoordinator task row directly and derives `worker_claim_ref`, `fence_ref`, worker identity, and worker instance from it.

## Exact fenced mutation scope

The GADI executable handoff now admits only the exact files the existing resolver/materializer/preflight/consumer chain may write:

```text
state/gadi-resident-execution/source/stegos-command.json
state/gadi-resident-execution/source/intr-admission.json
state/gadi-resident-execution/source/worker-claim.json
state/gadi-resident-execution/source/actuator-observation.json
state/gadi-resident-execution/source-resolution.json
state/gadi-resident-execution/materialization.json
state/gadi-resident-execution/command.json
state/gadi-resident-execution/execution-context.json
state/gadi-resident-execution/actuator-result.json
state/gadi-resident-execution/preflight.json
receipts/sovereign-host/gadi-resident-dispatch.latest.json
receipts/sovereign-host/gadi-resident-execution-consumption.latest.json
```

No wildcard repository mutation scope was added.

The process adapter now invokes only:

`python workers/gadi_resident_execution_worker.py`

and retains the existing preflight-gated adapter identity and timeout.

## Regression coverage

`tests/test_gadi_worker_protocol_bridge.py` verifies:

- only matching current invocation claim/fence is accepted;
- the dispatcher stages the exact WorkerCoordinator task row without altering it;
- non-ready dispatch maps to `HANDOFF_READY` and therefore relinquishable ownership;
- authentic-consumption state alone maps to `COMPLETED`;
- zero external cost and no new authority are claimed;
- the process adapter routes through the bridge;
- handoff mutation scope equals the exact bounded GADI state/receipt set.

## Evidence boundary

This protocol bridge is source/validation work only. It does not prove or create:

- a current native GADI StegOS command;
- a current canonical InTr admission;
- a current runtime binding;
- a controlled pre-authorized actuator effect;
- an authentic current WorkerCoordinator claim/fence outside an actual targeted runtime invocation;
- resident consumption;
- adaptive reassessment/termination;
- Continuity/Master Records custody or reconstruction;
- GADI activation.

The historical controlled simulation remains non-runtime evidence.

## Remaining authentic completion predicates

1. Validate and merge the post-claim worker protocol bridge.
2. Produce or locate an authentic current native StegOS GADI command.
3. Produce or locate the exact current canonical InTr admission carrying the matching `intr_decision_ref` and runtime binding context.
4. Produce the controlled pre-authorized software test-surface effect and governed output receipt through the merged StegOS seam.
5. Materialize those non-claim runtime sources locally.
6. Invoke the existing targeted WorkerCoordinator; it alone creates the fresh claim/fence, which the protocol bridge then stages into the existing claim source slot.
7. Require zero-blocker materialization/preflight before resident consumption.
8. Independently inspect the subject-bound resident receipt.
9. Complete closed-loop reassessment/adaptation/termination evidence.
10. Pass the authentic receipt chain to Continuity/Master Records and prove exact reconstruction.
11. Reconcile parent `GADI-001` and the umbrella manifold only from authentic observations.

## Immediate continuation

After this bridge validates and merges, inspect the current Universal InTr/GADI ingress and locally available non-claim source state. Do not run targeted WorkerCoordinator solely because source code is ready. The targeted run is appropriate only when current command/InTr/runtime-binding/controlled-output evidence is locally available; otherwise the bridge must return `HANDOFF_READY` and relinquish its temporary claim.

## Collision boundary

No second heartbeat, WorkerCoordinator, scheduler, resident service, runtime lease plane, claim/fence plane, InTr authority, provider transport, credential route, actuator implementation, or Master Records custody path is introduced.

## README impact

`README.md` was reviewed. Existing top-level documentation already defines WorkerCoordinator authority separation, targeted independent execution, local-only source refresh, and non-authorizing heartbeat semantics. This bridge is an internal protocol alignment within those existing surfaces, so no root README mutation is required.

## Release rule

This protocol bridge is not a GADI release or activation. Release/tag propagation remains deferred until authentic resident runtime execution, closed-loop evidence, exact reconstruction, and canonical activation predicates are satisfied.
