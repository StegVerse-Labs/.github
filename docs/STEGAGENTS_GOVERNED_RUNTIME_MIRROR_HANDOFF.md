# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / RUNTIME PROFILE RESOLUTION CURRENT / ROUTING READY FOR WORKERCOORDINATOR REVIEW / AUTHENTIC RUNTIME PROOF PENDING`

## Canonical state

- Current Task Registry state: `ACTIVE / UNCLAIMED`.
- Predecessor `STEGAGENTS-GOVERNED-AGENT-REGISTRATION-001` remains `RETIRED / COMPLETED`; it is not reopened.
- `CodeRepair-001` remains `REGISTERED_GOVERNED_PROPOSAL_ONLY`.
- exact governed-manifest source merge: `b768eeeb0ceca14fcfd50ce665cd6c0885e2774f`.
- exact governed-manifest Git blob: `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`.
- StegAgents governed runtime/reconstruction bridge merge: `b4115293803fd1d3beaf0335baf4308b6e13052e`.
- runtime task registration: `.github` PR `#1827`, merge `a06d9d3b8c564f267c2a9b9ffcd9826a798dc168`.
- Canonical Work resident request/stale-registry remediation: `.github` PR `#1829`, merge `2fadbb9cde25557ccbcbb6ace49ef5301fba9441`.
- WorkerCoordinator process-adapter binding: `.github` PR `#1830`, merge `e3fe9aa090acd46b9f82111299144c4092fee192`.

## Runtime-verification ordering correction

A Task Registry policy review found the prior handoff advanced one stage too early by naming fresh WorkerCoordinator claim/fence as the first unresolved predicate while `runtime_resolution` was still null.

Canonical `data/task-coordination-policy.json` requires runtime requirements to be resolved against the Canonical Runtime Profile Map and routing readiness to be evaluated before WorkerCoordinator admission review. Runtime-profile matching grants no authority; WorkerCoordinator claim/fence and current Interlock/InTr admission remain mandatory afterward.

The task's prior runtime requirements also combined pre-admission routing capabilities with post-claim bounded process execution and used `INTERNAL_AND_OPTIONAL_PROVIDER`, a direction not declared by any current runtime profile. That formulation deterministically produced no compatible canonical routing candidate.

The corrected routing requirements are:

```text
capabilities:
- task_registry_reconciliation
- worker_claim_projection
- intr_task_admission
- canonical_artifact_validation
- master_records_reconciliation
environment: SOVEREIGN_RESIDENT
direction: INTERNAL
mutation_required: true
deployment_required: false
current_observation_required: false
```

`bounded_process_execution` remains a capability of the existing post-claim WorkerCoordinator process adapter and is not a prerequisite for choosing the coordination/admission route. Authentic current runtime observation remains part of the later execution/evidence chain rather than profile-discovery authorization.

## Current runtime-profile resolution

Against `control/runtime-profile-map.json` generation `2`, the corrected requirements resolve to exactly one compatible declared routing profile:

```text
canonical-work-coordination-runtime-v1
```

The canonical task now persists:

```text
runtime_resolution.map_ref = control/runtime-profile-map.json
runtime_resolution.map_generation = 2
runtime_resolution.candidate_profile_ids = [canonical-work-coordination-runtime-v1]
runtime_resolution.projection_only = true
runtime_resolution.selection_grants_authority = false
```

This satisfies the runtime-profile-resolution and routing-readiness stages only. It does not prove runtime execution, process liveness, task ingress, WorkerCoordinator ownership, InTr disposition, provider operation, proposal return, or Master Records reconstruction.

## Routing-readiness disposition

Given the current canonical state:

- runtime requirements are explicit;
- one compatible current-map routing candidate exists;
- no route-blocking dependencies exist;
- task `blockers` is empty;
- no existing WorkerCoordinator claim/fence is projected;
- the runtime-resolution projection is current for map generation `2`.

Therefore the correct non-authorizing routing disposition is:

```text
ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW
```

The next unresolved predicate may now correctly be:

```text
AUTHENTIC_CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
```

This is materially different from the prior state: claim/fence is now next only because the required canonical runtime-resolution/routing-readiness step has been satisfied first.

## Authority boundaries

Canonical authority remains:

- Task Registry: work intent and coordination only.
- Runtime Profile Map: discovery/compatibility/routing projection only.
- WorkerCoordinator: execution claim/fence.
- StegCore/InTr: governed ingress/disposition/state-transition authority.
- TV/TVC: provider credential and provider-operation authority.
- KV/SKAP Vault: user-verification authority where applicable.
- Master Records: observed-reality custody/reconstruction.
- GitHub/CI: source validation and evidence transport only; runtime authority `NONE`.

`CodeRepair-001` is deterministic for this first proof, so no provider operation is required. Any later provider-backed agent remains exclusively behind TV/TVC.

## Governed roundtrip contract

The existing WorkerCoordinator adapter may proceed only after its own admission review and must mint a fresh claim/fence. The task worker then:

1. verifies the exact registered `CodeRepair-001` manifest blob;
2. invokes the existing proposal-only StegAgents runtime;
3. submits the proposal through the existing SDK/canonical StegCore/InTr route;
4. requires an authentic governance disposition with continuous transaction identity;
5. performs no direct consequential execution;
6. performs no TV/TVC provider operation for this deterministic proof;
7. retains exact claim-bound result evidence;
8. requires Master Records custody and same-run reconstruction receipts;
9. returns `COMPLETED` only when all authority and evidence predicates are continuous.

Expected successful resident receipt:

```text
receipts/sovereign-host/stegagents-governed-runtime/<claim_id>.json
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

## Current authentic runtime observation

The task remains `ACTIVE / UNCLAIMED`; no authentic WorkerCoordinator claim/fence or claim-bound governed-runtime receipt is currently observed. Therefore no StegCore/InTr runtime disposition, governed proposal return, or same-run Master Records reconstruction is claimed yet.

GitHub source, PR merges, Actions validation, runtime-profile matching, and routing readiness are all non-authorizing evidence surfaces and do not substitute for that authentic runtime chain.

## Next executable remediation

```text
existing WorkerCoordinator reviews routing-ready STEGAGENTS-GOVERNED-RUNTIME-001
-> fresh claim/fence
-> process:stegagents-governed-runtime-v1
-> exact CodeRepair-001 manifest verification
-> existing StegAgents proposal runtime
-> existing SDK / canonical StegCore/InTr disposition
-> governed proposal returned with no consequential execution
-> Master Records custody + reconstruct_sovereign receipts
-> claim-bound resident receipt
-> canonical WorkerCoordinator reconciliation/egress
```

## README decision

No README update is required. This corrects task-specific runtime-resolution state and handoff ordering; it introduces no new repository runtime class, scheduler, authority, or general repository responsibility.

## Manual work

None.
