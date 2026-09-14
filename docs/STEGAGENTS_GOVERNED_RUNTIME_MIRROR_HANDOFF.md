# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / RUNTIME PROFILE RESOLUTION CURRENT / ROUTING READY / TARGETED WORKERCOORDINATOR BRIDGE MERGED+VALIDATED / PORTABLE EXACT-SELECTOR REPAIR STAGED / AUTHENTIC RUNTIME PROOF PENDING`

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
- Runtime-profile/routing-order correction: `.github` PR `#1836`, merge `de0ad40f03e588dbf81de34b9fb6f63606987e21`.
- targeted resident WorkerCoordinator bridge: `.github` PR `#1838`, merge `7d79f618052dd029730de582a7e7cd77c6551785`.

## Runtime-profile resolution and routing readiness

The task's persisted generation-2 Runtime Profile Map resolution remains:

```text
candidate_profile_ids = [canonical-work-coordination-runtime-v1]
projection_only = true
selection_grants_authority = false
```

Routing disposition remains `ELIGIBLE_FOR_WORKERCOORDINATOR_ADMISSION_REVIEW`. Runtime-profile matching grants no execution authority.

## Targeted WorkerCoordinator execution bridge

PR `#1838` repaired the source integration gap between routing-ready ACTIVE task state and the existing WorkerCoordinator admission path. The repair reuses the established `TARGETED_INDEPENDENT_TASK_CONTROL` pattern and introduces no second dispatcher, WorkerCoordinator, scheduler, runtime profile, agent registry, InTr implementation, provider route, credential route, or runtime substrate.

Merged task-specific surfaces:

```text
control/resident-execution-request.d/stegagents-governed-runtime-targeted-001.json
scripts/consume_stegagents_governed_runtime_targeted_request.py
```

The existing resident dispatcher exposes selector `stegagents_governed_runtime_targeted`, and the sovereign source-refresh paths carry the targeted consumer and request into a resident runtime. The consumer validates the exact task/COSV pair, rejects hosted execution, strips provider/API/GitHub credential material, preserves `credential_authority=TV/TVC`, requires `github_token_runtime_authority=NONE`, and delegates only to:

```text
scripts/refresh_and_execute_resident_task.py \
  --task-id STEGAGENTS-GOVERNED-RUNTIME-001 \
  --cosv-task-vector 71000000101001
```

That bridge grants no claim/fence or transition authority; the existing WorkerCoordinator remains the only claim/fence authority.

## Portable exact-selector remediation

Post-merge execution-path inspection found one additional reachability defect. The generic resident dispatcher already registered `stegagents_governed_runtime_targeted`, and sovereign source refresh already propagated the consumer and resident-request directory, but `scripts/refresh_and_dispatch_resident_requests.py` omitted that selector from `ALLOWED_TARGET_CONSUMERS`.

That meant an already-existing sovereign resident using the portable local `refresh -> exact targeted dispatch` bridge would fail before invoking the registered StegAgents consumer. This is a source-addressability defect, not permission to create a replacement runtime.

The staged repair adds only the existing selector:

```text
stegagents_governed_runtime_targeted
```

to the portable bridge allowlist and extends `tests/test_stegagents_governed_runtime_targeted_resident_bridge.py` to require agreement among the generic dispatcher, sovereign source refresh, portable exact-selector bridge, targeted consumer, task/COSV binding, and authority ceiling.

No second dispatcher, scheduler, WorkerCoordinator, runtime profile, agent registry, InTr implementation, credential route, provider route, network source fetch, hosted runtime, or second-device dependency is introduced. The portable bridge remains non-authorizing and still delegates to the same existing consumer and WorkerCoordinator path.

## #1838 validation and repository-wide repairs

Final exact head `091ca07862a1fe242411dad124b820794303f809` passed every triggered validation lane before merge, including:

```text
Organization Control                  34868715807 SUCCESS
Heartbeat Worker Project              34868715702 SUCCESS
Deterministic Repository Suite        34868715698 SUCCESS
Cross-Framework Current-Basis         34868715795 SUCCESS
validate-deepseek-resident             34868715779 SUCCESS
KV AI Memory Resident Binding         34868715582 SUCCESS
Workspace DEVICE_KV                   34868715644 SUCCESS
SDK ExtCollab Consent Listener        34868715691 SUCCESS
SDK ExtCollab Reseal                  34868715745 SUCCESS
```

These are validation/evidence-transport results only and grant no runtime authority.

Two current-main conformance regressions encountered during validation were repaired without creating new task owners:

1. commit `7cc024b69ab2925ec107de22ce76edc070c7c43d` had accidentally truncated the canonical README tail. The complete canonical repository-wide README invariants, including the Operational Observer Standard, were restored from the immediately preceding complete canonical state.
2. existing adjacent task `SV-KV-AI-WORKERCOORDINATOR-ADMISSION-001` lacked the now-required `execution_substrate_resolution`; the minimum one-device-first non-authorizing substrate review was added with all local candidates still `PENDING_EVIDENCE`, no selected substrate, and external/second-device use false. No KV-AI runtime advancement was claimed.

## Authority invariants

- Task Registry: work intent/coordination only.
- Runtime Profile Map: discovery/routing projection only.
- WorkerCoordinator: execution claim/fence.
- StegCore/InTr: governed transition/admission authority.
- TV/TVC: provider credential/provider-operation authority.
- KV/SKAP Vault: user-verification authority where applicable.
- Master Records: observed-reality custody/reconstruction.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

The deterministic first CodeRepair proof requires no provider operation. Provider credentials must never become visible to StegAgents.

## Governed roundtrip contract

After authentic targeted resident consumption, the existing WorkerCoordinator must independently admit the task and mint a fresh claim/fence. The existing task worker must then:

1. verify the exact registered `CodeRepair-001` manifest blob `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`;
2. preserve `proposal_only=true`, `execution_authority=false`, and `self_authorization_allowed=false`;
3. invoke the existing proposal-only StegAgents runtime;
4. submit through the existing SDK/canonical StegCore/InTr route;
5. retain the authentic governance disposition and continuous transaction identity;
6. perform no direct consequential execution;
7. perform no provider operation for this deterministic proof;
8. retain exact claim-bound evidence;
9. require Master Records custody and same-run reconstruction receipts;
10. reconcile/egress through the existing WorkerCoordinator lifecycle.

Expected authentic evidence:

```text
receipts/sovereign-host/stegagents-governed-runtime-targeted-request-consumption.latest.json
receipts/sovereign-host/stegagents-governed-runtime/<claim_id>.json
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

## Current authentic runtime observation

Current repository-visible WorkerCoordinator state remains:

```text
state = HANDOFF_READY
claim_id = null
lease = null
worker_id = null
worker_instance_id = null
```

The targeted resident request remains `REQUESTED`. Neither expected runtime receipt is repository-visible. The authorized remote resident connector reports no connected resident device in this session. That is reachability evidence only and does not establish a second-device requirement.

Therefore no authentic targeted request consumption, fresh WorkerCoordinator claim/fence, StegCore/InTr runtime disposition, governed proposal return, provider operation, or Master Records reconstruction is claimed.

## First unresolved predicate

Until the portable selector repair is merged and an authentic resident consumes the request, the continuous runtime predicate remains:

```text
AUTHENTIC_TARGETED_RESIDENT_REQUEST_CONSUMPTION_AND_CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
```

## Next machine-owned execution

```text
existing sovereign resident local source refresh
-> refresh_and_dispatch_resident_requests.py --only-consumer steagents_governed_runtime_targeted
-> existing resident dispatcher visits steagents_governed_runtime_targeted
-> targeted consumer verifies task/COSV and authority ceiling
-> existing refresh_and_execute_resident_task.py
-> existing WorkerCoordinator admission review
-> fresh claim/fence
-> process:stegagents-governed-runtime-v1
-> exact CodeRepair-001 manifest verification
-> existing StegAgents proposal runtime
-> existing SDK / canonical StegCore/InTr disposition
-> governed proposal return with no consequential execution
-> Master Records custody + reconstruct_sovereign receipts
-> claim-bound resident receipt
-> canonical WorkerCoordinator reconciliation/egress
```

The goal remains ACTIVE until this authentic chain exists. No human-authority checkpoint has been identified.

## README decision

No root README content change is required for this task-specific selector repair. The repository README already documents the existing targeted execution and exact task/COSV pointer semantics; this change does not alter those semantics, authority roles, or runtime class. The canonical task record carries the explicit non-material README determination and evidence refs.

## Manual work

None.
