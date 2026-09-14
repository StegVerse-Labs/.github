# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / WORKERCOORDINATOR ADAPTER STAGED / AUTHENTIC RUNTIME PROOF PENDING`

## Goal

Activate and prove the first governed StegAgents runtime path using the already-registered `CodeRepair-001` governed manifest while reusing the existing WorkerCoordinator, StegCore/InTr, TV/TVC provider boundary if required, and Master Records reconstruction path.

## Proven predecessor and registration

- `STEGAGENTS-GOVERNED-AGENT-REGISTRATION-001` remains `RETIRED / COMPLETED`; it is not reopened.
- `CodeRepair-001` remains `REGISTERED_GOVERNED_PROPOSAL_ONLY`.
- exact governed-manifest source merge: `b768eeeb0ceca14fcfd50ce665cd6c0885e2774f`.
- exact governed-manifest Git blob: `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`.
- StegAgents governed runtime/reconstruction bridge main merge: `b4115293803fd1d3beaf0335baf4308b6e13052e`.
- StegCore 001/002 baseline is `activated`.
- StegAgents/StegCore handshake is `handshake_ready`.
- Runtime Goal Task registration merged through `.github` PR `#1827` as `a06d9d3b8c564f267c2a9b9ffcd9826a798dc168`.
- Canonical Work resident-request/stale-registry remediation merged through `.github` PR `#1829` as `2fadbb9cde25557ccbcbb6ace49ef5301fba9441`.

Source/CI state is validation/evidence transport only and is not runtime proof.

## Existing runtime reuse

The runtime task is staged through the already-existing `canonical_work_coordination` resident consumer and the existing `scripts/run_worker_runtime.py` WorkerCoordinator lifecycle. No new dispatcher, scheduler, WorkerCoordinator, InTr implementation, provider route, credential path, runtime substrate, governance engine, or agent registry is introduced.

Current task-specific reuse surfaces:

- `control/resident-execution-request.d/canonical-work-stegagents-governed-runtime-001.json`
- `handoffs/STEGAGENTS-GOVERNED-RUNTIME-001.json`
- `control/worker-registry.d/stegagents-governed-runtime-001.json`
- `control/process-worker-adapters.d/stegagents-governed-runtime-001.json`
- `workers/stegagents_governed_runtime_worker.py`
- existing `scripts/run_worker_runtime.py`
- existing Canonical Work / Universal InTr ingress
- existing StegAgents `src/governed_coderepair_runtime.py`
- existing SDK / canonical StegCore governance runtime
- existing Master Records custody/reconstruction runtime

The task-specific worker consumes only a WorkerCoordinator-created ACTIVE task row and exact claim/fence scope. It cannot mint a claim or fencing token.

## Exact manifest proof

Before invoking StegAgents, the worker computes the Git blob identity of the already-local `agents/governed/CodeRepair-001.manifest.json` bytes and requires it to equal:

```text
061649a4b0b43c01f3009ed3e6c8c4829559fb5b
```

That is the exact blob on merged registration source `b768eeeb0ceca14fcfd50ce665cd6c0885e2774f`. A mismatch fails closed before proposal execution.

## Authority boundaries

Canonical authority remains:

- Task Registry: coordination intent only.
- WorkerCoordinator: execution claim/fence.
- StegCore/InTr: governed ingress/disposition/state-transition authority.
- TV/TVC: provider credential and provider-operation authority.
- KV/SKAP Vault: user-verification authority where applicable. This first deterministic CodeRepair proof does not require a user-verification transition.
- Master Records: observed-reality custody/reconstruction.
- GitHub/CI: source validation and evidence transport only; runtime authority `NONE`.

`CodeRepair-001` is deterministic for this proof, so no provider operation is required. Any later model/provider requirement remains exclusively behind TV/TVC and provider credentials may not become visible to StegAgents.

## Runtime receipt contract

On authentic execution, the WorkerCoordinator bridge retains a write-once claim-bound receipt under:

```text
receipts/sovereign-host/stegagents-governed-runtime/<claim_id>.json
```

and projects the latest observed result to:

```text
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

The receipt binds:

- exact request identity and SHA-256;
- exact WorkerCoordinator claim/fence;
- exact registered manifest blob and registration merge;
- returned CodeRepair proposal and SHA-256;
- StegCore governance disposition/transaction/route receipt chain;
- `proposal_only=true`;
- `execution_authority=false`;
- `self_authorization_allowed=false`;
- `provider_operation_required=false`;
- `credential_authority=TV/TVC`;
- `credential_material_present=false`;
- `external_side_effect=false`;
- Master Records reconstruction operation and receipt IDs;
- GitHub runtime authority `NONE`;
- KV/SKAP user-verification authority preserved.

The worker returns `COMPLETED` only when the governance chain is verified, transaction identity is continuous, Master Records custody is `RECORDED`, same-run reconstruction receipts exist, and all authority invariants remain intact. Otherwise it returns `HANDOFF_READY` and relinquishes the claim through the existing WorkerCoordinator lifecycle.

## Required runtime evidence chain

```text
canonical runtime task registration
-> canonical_work_coordination resident request consumption
-> exact CodeRepair-001 governed manifest identity
-> fresh WorkerCoordinator claim/fence
-> governed request identity
-> existing StegAgents proposal path
-> existing StegCore/InTr ingress
-> authentic governance disposition
-> no TV/TVC provider operation for this deterministic proof
-> governed proposal result returned
-> exact claim-bound resident receipt retention
-> Master Records custody + reconstruction receipts
-> canonical task reconciliation/egress
```

## Current runtime observation

Current canonical Task Registry state remains `ACTIVE / UNCLAIMED`. No authentic claim/fence or claim-bound governed-runtime receipt has yet been observed in repository-visible evidence. The authorized direct resident-command connector currently reports no connected device. This is reachability evidence only; it neither requires another device nor authorizes another runtime.

## First unresolved predicate

```text
AUTHENTIC_CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
```

Next executable remediation after this source change is merged and revalidated:

```text
existing resident WorkerCoordinator cycle
-> claim STEGAGENTS-GOVERNED-RUNTIME-001 using process:stegagents-governed-runtime-v1
-> worker verifies exact merged manifest
-> worker invokes existing StegAgents governed CodeRepair runtime
-> SDK/canonical StegCore governance disposition
-> returned proposal + Master Records reconstruction
-> claim-bound resident receipt
-> WorkerCoordinator reconciliation/egress
```

## Completion predicates

Retire this task only after authentic current evidence exists for every expected predicate in the canonical task record, including merged-main validation of required source changes and canonical reconciliation. Source/CI success alone cannot satisfy any runtime predicate.

## README decision

No `.github` README update is required because this adds no new runtime class or repository responsibility; it binds one task to the already-documented WorkerCoordinator/process-adapter mechanism.

## Manual work

None.
