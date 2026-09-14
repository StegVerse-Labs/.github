# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / ROUTING READY / RESIDENT PATH + WARRANT-POLICY GATE MERGED+VALIDATED / RESIDENT ROOT OBSERVATION OWNED BY EXISTING TASK / AUTHENTIC RUNTIME PROOF PENDING`

## Canonical state

- Task Registry: `ACTIVE / UNCLAIMED`.
- completion: `claimed=false`, `validated=false`, `activation_proof_complete=false`.
- WorkerCoordinator projection: `HANDOFF_READY`, `claim_id=null`, `lease=null`, `worker_id=null`, `worker_instance_id=null`.
- runtime profile generation `2` resolves to `canonical-work-coordination-runtime-v1`; routing resolution grants no authority.
- exact registered `CodeRepair-001` governed manifest Git blob: `061649a4b0b43c01f3009ed3e6c8c4829559fb5b`.
- portable selector repair: `.github#1845` merged as `4b13c020ed249b82ffe24cd5939cfffe2534601e`.
- StegAgents warrant/policy enforcement: `StegAgents#18` merged as `c82caae4c8c4cf82d40f352528269823d853f788`.
- `.github` warrant/policy carriage + WorkerCoordinator binding: `#1856` merged as `82bf7600f47b2f339bdbc64b3bcdeac9e8b007c2`.
- post-merge canonical reconciliation: `#1859` merged as `55888c7569340cf22a895ab874148e91b23f2e2a`.

## Warrant/policy boundary

The governed manifest requires `warrant_required=true` and `policy_bundle_required=true`.

WorkerCoordinator claim/fence is delegation/fencing evidence and is not the TV execution warrant. `canonical-task:` identity is not the pinned policy bundle. StegAgents merge `c82caae4c8c4cf82d40f352528269823d853f788` fails closed before proposal construction unless the existing live-run inputs verify Ed25519 signature, validity/TTL, policy-bundle hash, repository identity, and actual local commit identity:

```text
STEGVERSE_WARRANT_JSON
TV_POLICY_BUNDLE_SHA256
TV_WARRANT_ISSUER_PUBKEY_B64
TV_WARRANT_MAX_TTL_SECONDS
```

No provider operation is required for deterministic `CodeRepair-001`. TV/TVC remains the only provider credential/provider-operation authority if a later path actually requires a provider.

## Existing resident execution path

```text
resident source refresh
-> exact selector steagents_governed_runtime_targeted
-> generic resident dispatcher
-> targeted StegAgents consumer
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

All known source selector, carriage, warrant-policy, and WorkerCoordinator binding defects on this path are merged and validated. GitHub/CI runtime authority remains `NONE`.

## Current resident reachability reconciliation

The authorized resident connector currently exposes no connected resident device. Repository-visible authentic StegAgents runtime receipts remain absent:

```text
receipts/sovereign-host/stegagents-governed-runtime-targeted-request-consumption.latest.json
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

Independent reconciliation found an already-active one-device-first canonical owner for the missing resident custody-root observation:

```text
Goal Task ID: STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001
Issue: StegVerse-Labs/.github#1860
Handoff: docs/STEGBROWSER_RESIDENT_CUSTODY_ROOT_OBSERVATION_MIRROR_HANDOFF.md
State: ACTIVE / CHECKED_OUT
```

That task exists specifically to observe an authentic retained resident custody root and classify receipt reachability without creating a second scheduler, dispatcher, runtime plane, credential path, GitHub authority path, or second user-operated device. Its current first unresolved predicate is `RESIDENT_CUSTODY_ROOT_AUTHENTICALLY_OBSERVED_FOR_STEGBROWSER`.

This StegAgents goal now reuses that existing owner for resident-root reachability instead of creating a duplicate task or runtime. No substrate is selected merely from source state; `STEG-BROWSER-RETAINED-RESIDENT-NODE` remains `PENDING_EVIDENCE` until authentic retained-root evidence exists.

## Current first concrete machine-owned defect

```text
AUTHENTIC_RESIDENT_CUSTODY_ROOT_OBSERVED
```

This is now the earliest concrete prerequisite to `AUTHENTIC_TARGETED_RESIDENT_REQUEST_CONSUMPTION_OBSERVED`. Once the existing resident-root observation owner produces an authentic current custody root, this goal should immediately use the already-merged exact selector against that same resident path and continue to fresh WorkerCoordinator claim/fence, TV warrant/policy verification, StegCore/InTr disposition, proposal return, claim-bound receipt, and Master Records reconstruction.

## Required authentic completion chain

1. authentic resident custody root observed;
2. targeted resident request consumption observed;
3. fresh current WorkerCoordinator claim/fence;
4. authentic TV-issued execution warrant verified;
5. pinned TV policy bundle verified;
6. exact manifest blob `061649a4b0b43c01f3009ed3e6c8c4829559fb5b` verified;
7. governed request identity continuous;
8. `proposal_only=true`;
9. `execution_authority=false`;
10. `self_authorization_allowed=false`;
11. authentic StegCore/InTr disposition;
12. no unauthorized provider operation and no provider credentials visible to StegAgents;
13. governed proposal returned without consequential execution;
14. exact claim-bound receipt retained;
15. Master Records custody `RECORDED` and same-run reconstruction with matching identities;
16. WorkerCoordinator reconciliation/egress complete.

## Authority invariants

- Task Registry: coordination only.
- resident-root observation task: evidence reachability only.
- WorkerCoordinator: claim/fence authority.
- StegCore/InTr: governed transition/disposition authority.
- TV/TVC: provider credential/provider-operation authority and source of authentic warrant/policy evidence where applicable.
- KV/SKAP Vault: user-verification authority where applicable.
- Master Records: observed-reality custody/reconstruction authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.
- no second user-operated device is required or authorized.

## Retirement decision

Retirement is not warranted. No authentic resident custody root, targeted request consumption, current claim/fence, warrant/policy verification, StegCore/InTr disposition, proposal return, claim-bound runtime receipt, Master Records reconstruction, or WorkerCoordinator egress has been observed.

## Next machine-owned action

Reuse `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001` / `.github#1860` to obtain an authentic current resident custody root through retained runtime marker/receipt evidence. Do not create another reachability task. As soon as the root is observed, execute the existing `stegagents_governed_runtime_targeted` selector against that resident path and continue the governed roundtrip fail-closed.

## README decision

No root README change is required. This reconciliation binds an existing runtime-evidence owner and changes no runtime capability or authority model.

## Manual work

None.
