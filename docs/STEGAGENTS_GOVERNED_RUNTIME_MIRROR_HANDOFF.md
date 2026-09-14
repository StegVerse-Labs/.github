# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / ROUTING READY / RESIDENT PATH + WARRANT-POLICY GATE MERGED+VALIDATED / AUTHENTIC RUNTIME PROOF PENDING`

## Canonical state

- Task Registry: `ACTIVE / UNCLAIMED`.
- completion: `claimed=false`, `validated=false`, `activation_proof_complete=false`.
- WorkerCoordinator projection: `HANDOFF_READY`, `claim_id=null`, `lease=null`, `worker_id=null`, `worker_instance_id=null`.
- runtime profile generation `2` resolves to `canonical-work-coordination-runtime-v1`; routing resolution grants no authority.
- exact registered `CodeRepair-001` governed manifest Git blob: `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`.
- portable selector repair: `.github#1845` merged as `4b13c020ed249b82ffe24cd5939cfffe2534601e`.
- StegAgents warrant/policy enforcement: `StegAgents#18` merged as `c82caae4c8c4cf82d40f352528269823d853f788`.
- `.github` warrant/policy carriage + WorkerCoordinator binding: `#1856` merged as `82bf7600f47b2f339bdbc64b3bcdeac9e8b007c2`.

## Independent warrant/policy conclusion

The governed manifest requires:

```text
warrant_required = true
policy_bundle_required = true
```

WorkerCoordinator claim/fence is execution delegation/fencing evidence and does **not** satisfy the execution-warrant requirement. A `canonical-task:` reference is coordination/task identity and does **not** satisfy the pinned policy-bundle requirement.

The required governance-admission evidence is an authentic TV-issued signed warrant plus its pinned policy bundle. The existing StegAgents live-run contract carries:

```text
STEGVERSE_WARRANT_JSON
TV_POLICY_BUNDLE_SHA256
TV_WARRANT_ISSUER_PUBKEY_B64
TV_WARRANT_MAX_TTL_SECONDS  # optional; default 900
```

StegAgents merge `c82caae4c8c4cf82d40f352528269823d853f788` reuses `src/warrant_verify.py` and fails closed before proposal construction unless Ed25519 signature, validity/TTL, policy-bundle hash, repository identity, and actual local commit identity verify. Only non-secret verification metadata is retained in the governed result; raw warrant/key material is not retained in proposal evidence.

## End-to-end resident carriage

`.github#1856` closes the source-carriage seam across the existing path. The four governance verification inputs are carried by the existing:

```text
refresh_and_dispatch_resident_requests.py
-> dispatch_resident_execution_requests.py
-> consume_stegagents_governed_runtime_targeted_request.py
-> refresh_and_execute_resident_task.py
-> process:stegagents-governed-runtime-v1
```

Regression coverage requires all five carriage points. This creates no second dispatcher, scheduler, WorkerCoordinator, runtime profile, InTr implementation, provider route, credential authority, hosted runtime, network source fetch, or second-device dependency.

The `.github` worker additionally requires returned `warrant_policy_binding.warrant_verified=true` and `policy_bundle_verified=true`, plus repository/commit/hash bindings, before it may return `COMPLETED`.

## Validation

StegAgents PR `#18` exact head `94d668f465bbcf7a7b14a7d8996b5d127cc8f411` passed:

```text
CI                               34873634596 SUCCESS
Test Readiness                   34873634603 SUCCESS
Cross-Agent Authority Validation 34873634684 SUCCESS
```

`.github` PR `#1856` final exact head `dff9697de9ac6b6e24dd295f97c7e30bc1df6fdc` passed all eight triggered lanes:

```text
Heartbeat Worker Project              34874827876 SUCCESS
Organization Control                  34874828033 SUCCESS
Deterministic Repository Suite        34874828069 SUCCESS
Cross-Framework Resident Validation   34874827746 SUCCESS
KV AI Memory Resident Binding         34874827862 SUCCESS
validate-deepseek-resident             34874828087 SUCCESS
SDK WorkSpace Consent Listener        34874827750 SUCCESS
SDK WorkSpace Reseal                  34874827833 SUCCESS
```

These are source/validation evidence only. GitHub/CI runtime authority remains `NONE`.

## Required authentic roundtrip

```text
resident source refresh
-> exact selector steagents_governed_runtime_targeted
-> generic resident dispatcher
-> targeted consumer
-> refresh_and_execute_resident_task.py
-> fresh WorkerCoordinator claim/fence
-> process:stegagents-governed-runtime-v1
-> exact manifest verification
-> authentic TV warrant + pinned policy verification
-> deterministic CodeRepair proposal
-> existing SDK / StegCore/InTr disposition
-> proposal returned with no consequential execution
-> exact claim-bound receipt
-> Master Records custody RECORDED + same-run reconstruction
-> WorkerCoordinator reconciliation/egress
```

The deterministic CodeRepair proof requires no provider operation. TV/TVC remains provider credential/provider-operation authority if a later path actually requires a provider. Provider credentials may never become visible to StegAgents. KV/SKAP retains user-verification authority where applicable. StegCore/InTr retains transition/disposition authority. Master Records retains observed-reality custody/reconstruction authority.

## Current authentic evidence

Post-merge reconciliation found no authentic runtime promotion evidence:

```text
WorkerCoordinator state = HANDOFF_READY
claim_id = null
lease = null
worker_id = null
worker_instance_id = null
```

Repository-visible authentic receipts remain absent:

```text
receipts/sovereign-host/stegagents-governed-runtime-targeted-request-consumption.latest.json
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

No connected sovereign resident device was available through the authorized resident connector during this reconciliation. That is reachability evidence only and creates no second-device requirement.

Therefore no fresh claim/fence, authentic TV warrant/policy verification, StegCore/InTr disposition, governed proposal return, provider operation, claim-bound runtime receipt, Master Records reconstruction, or WorkerCoordinator egress is claimed.

## First unresolved predicate

```text
AUTHENTIC_TARGETED_RESIDENT_REQUEST_CONSUMPTION_OBSERVED
```

All known source/addressability/carriage defects discovered during this goal are now repaired and validated. The next machine-owned action is the existing sovereign resident consuming the already-merged targeted request. Its next required predicates are a fresh WorkerCoordinator claim/fence and authentic TV-issued warrant/policy verification. Missing or invalid warrant/policy evidence must fail closed.

## Retirement decision

Retirement is **not warranted**. The goal remains ACTIVE because its authentic runtime evidence chain has not begun. Source merges, CI, routing readiness, and warrant-carriage readiness cannot substitute for current runtime evidence.

## README decision

No new `.github` README content is required. The repository README already documents targeted Task/COSV execution and separated authority semantics. The owning StegAgents README already documents the live warrant/policy inputs; this work enforces those existing semantics.

## Manual work

None.
