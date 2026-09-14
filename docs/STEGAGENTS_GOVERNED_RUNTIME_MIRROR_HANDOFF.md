# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / RUNTIME PROFILE RESOLUTION CURRENT / ROUTING READY / TARGETED WORKERCOORDINATOR BRIDGE MERGED+VALIDATED / PORTABLE EXACT-SELECTOR REPAIR MERGED+VALIDATED / AUTHENTIC RUNTIME PROOF PENDING`

## Canonical state

- Task Registry: `ACTIVE / UNCLAIMED`.
- Predecessor `STEGAGENTS-GOVERNED-AGENT-REGISTRATION-001`: `RETIRED / COMPLETED`.
- `CodeRepair-001`: `REGISTERED_GOVERNED_PROPOSAL_ONLY`.
- exact governed manifest source merge: `b768eeeb0ceca14fcfd50ce665cd6c0885e2774f`.
- exact governed manifest Git blob: `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`.
- StegAgents governed runtime/reconstruction bridge: `b4115293803fd1d3beaf0335baf4308b6e13052e`.
- task registration: PR `#1827`, merge `a06d9d3b8c564f267c2a9b9ffcd9826a798dc168`.
- Canonical Work request/stale-registry repair: PR `#1829`, merge `2fadbb9cde25557ccbcbb6ace49ef5301fba9441`.
- WorkerCoordinator process-adapter binding: PR `#1830`, merge `e3fe9aa090acd46b9f82111299144c4092fee192`.
- runtime-profile/routing correction: PR `#1836`, merge `de0ad40f03e588dbf81de34b9fb6f63606987e21`.
- targeted resident WorkerCoordinator bridge: PR `#1838`, merge `7d79f618052dd029730de582a7e7cd77c6551785`.
- targeted bridge handoff reconciliation: PR `#1839`, merge `04db0be28a97a3ceca71976fff2bac4c8da52a1e`.
- portable exact-selector repair: PR `#1845`, merge `4b13c020ed249b82ffe24cd5939cfffe2534601e`.

## Runtime profile and routing

Generation `2` resolves this task to exactly `canonical-work-coordination-runtime-v1`. The resolution is projection-only and grants no authority. Routing remains `ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW`.

## Resident execution path

The existing task-specific request remains:

```text
control/resident-execution-request.d/stegagents-governed-runtime-targeted-001.json
```

with selector:

```text
stegagents_governed_runtime_targeted
```

The path is now continuous in source through the existing resident mechanisms:

```text
existing sovereign resident local source refresh
-> scripts/refresh_and_dispatch_resident_requests.py --only-consumer steagents_governed_runtime_targeted
-> existing scripts/dispatch_resident_execution_requests.py
-> scripts/consume_stegagents_governed_runtime_targeted_request.py
-> scripts/refresh_and_execute_resident_task.py
-> existing WorkerCoordinator admission review
-> fresh claim/fence
-> process:stegagents-governed-runtime-v1
-> exact CodeRepair-001 manifest verification
-> existing StegAgents proposal-only runtime
-> existing SDK / canonical StegCore/InTr disposition
-> governed proposal returned with no consequential execution
-> Master Records custody + same-run reconstruction
-> claim-bound resident receipt
-> WorkerCoordinator reconciliation/egress
```

PR `#1845` repaired the final source-addressability defect in that path: the generic dispatcher already registered `stegagents_governed_runtime_targeted`, and sovereign source refresh already propagated the consumer/request, but the portable one-consumer bridge did not admit the selector. The repair adds only that existing selector and regression coverage. It creates no second dispatcher, scheduler, WorkerCoordinator, runtime profile, InTr implementation, agent registry, provider route, credential route, hosted runtime, network source fetch, or second-device dependency.

## PR #1845 validation

Final exact head `86cda945d3321a987664bc9ef5e037f5303a2b53` was reconciled with then-current `main` and passed all triggered lanes before merge:

```text
Organization Control                  34871530189 SUCCESS
Heartbeat Worker Project              34871530230 SUCCESS
Deterministic Repository Suite        34871530349 SUCCESS
KV AI Memory Resident Binding         34871530245 SUCCESS
Cross-Framework Current-Basis         34871530351 SUCCESS
```

These results validate source/conformance only. They grant no runtime authority and do not prove resident request consumption or governed execution.

## Authority invariants

- Task Registry: coordination only.
- Runtime Profile Map: discovery/routing projection only.
- WorkerCoordinator: claim/fence authority.
- StegCore/InTr: governed transition/admission authority.
- TV/TVC: provider credential/provider-operation authority.
- KV/SKAP Vault: user-verification authority where applicable.
- Master Records: observed-reality custody/reconstruction authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- HeartBeat: timing/freshness/correlation/reference only.

`CodeRepair-001` is deterministic for this first proof, so a TV/TVC provider operation is not required unless the runtime unexpectedly selects a provider-backed path. Provider credentials must never be visible to StegAgents.

## Required governed-roundtrip predicates

The authentic run must prove:

1. fresh current WorkerCoordinator claim/fence;
2. exact manifest blob `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`;
3. `proposal_only=true`;
4. `execution_authority=false`;
5. `self_authorization_allowed=false`;
6. StegCore/InTr authentic governance disposition;
7. provider credentials absent from StegAgents;
8. no provider operation unless actually required;
9. governed proposal returned without direct consequential execution;
10. exact claim-bound receipt retained;
11. Master Records custody `RECORDED` and same-run reconstruction with continuous transaction identity;
12. WorkerCoordinator reconciliation/egress.

Expected authentic evidence:

```text
receipts/sovereign-host/stegagents-governed-runtime-targeted-request-consumption.latest.json
receipts/sovereign-host/stegagents-governed-runtime/<claim_id>.json
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

## Current authentic runtime observation after #1845

Post-merge inspection still shows:

```text
WorkerCoordinator state = HANDOFF_READY
claim_id = null
lease = null
worker_id = null
worker_instance_id = null
```

The targeted-consumption receipt is not repository-visible. The claim-bound governed-runtime latest receipt is not repository-visible. The authorized remote resident connector reports no connected resident device in this session. This is reachability evidence only; it does not establish a second-device requirement and does not authorize a substitute runtime.

Therefore no authentic targeted request consumption, fresh WorkerCoordinator claim/fence, StegCore/InTr disposition, governed proposal result, provider operation, or Master Records reconstruction is claimed.

## First unresolved predicate

```text
AUTHENTIC_TARGETED_RESIDENT_REQUEST_CONSUMPTION_AND_CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
```

The source path to that predicate is now merged and validated. The goal remains ACTIVE until authentic resident evidence advances it.

## README decision

No root README content change was required for PR `#1845`. The repository README already documents targeted execution and exact task/COSV pointer semantics; the selector repair does not change authority roles, runtime class, or generic bridge semantics. The canonical task record contains the explicit non-material README determination and evidence refs.

## Manual work

None.
