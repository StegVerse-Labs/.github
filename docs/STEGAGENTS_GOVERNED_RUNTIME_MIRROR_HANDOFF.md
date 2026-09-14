# StegAgents Governed Runtime Mirror Handoff

Updated: 2026-09-14
Repository: `StegVerse-Labs/.github`
Target runtime path: `StegVerse-Labs/StegAgents` -> `StegVerse-Labs/StegCore/InTr`
Goal Task ID: `STEGAGENTS-GOVERNED-RUNTIME-001`
COSV: `71000000101001`
Status: `ACTIVE / WORKERCOORDINATOR BINDING MERGED+VALIDATED / AUTHENTIC RUNTIME PROOF PENDING`

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

## #1830 exact-head validation

The final branch head after reconciling current main was `5f7a96f20b2212cfa7a88b534680e468e0325eba`.

Validation-only lanes all passed:

- Organization Control: run `34862438506` — SUCCESS.
- Heartbeat Worker Project: run `34862438427` — SUCCESS.
- Deterministic Repository Suite: run `34862438379` — SUCCESS.

These runs are validation/evidence transport only. They confer no runtime authority and do not prove claim/fence, InTr disposition, proposal return, or Master Records reconstruction.

## Existing runtime reuse

The task reuses only existing authority/runtime surfaces:

- canonical Task Registry for coordination intent;
- existing `scripts/run_worker_runtime.py` WorkerCoordinator for claim/fence;
- `process:stegagents-governed-runtime-v1` task adapter;
- existing `CodeRepair-001` proposal implementation;
- existing StegVerse SDK + canonical StegCore/InTr governance route;
- TV/TVC as exclusive provider credential/provider-operation authority;
- KV/SKAP Vault as user-verification authority where applicable;
- Master Records for observed-reality custody and reconstruction.

No second WorkerCoordinator, scheduler, dispatcher, agent registry, governance engine, InTr implementation, provider route, credential route, or runtime substrate was created.

## Runtime proof contract

`workers/stegagents_governed_runtime_worker.py` accepts only an already-minted ACTIVE WorkerCoordinator invocation with an exact claim/fence pair. It cannot mint either value.

Before invoking StegAgents it computes the Git blob identity of the already-local `agents/governed/CodeRepair-001.manifest.json` and requires exact equality with:

```text
061649a4b0b43c01f3009ed3e6c8c4829559fb5b
```

The worker then requires the returned governed result to preserve:

```text
proposal_only = true
execution_authority = false
self_authorization_allowed = false
provider_operation_required = false
credential_authority = TV/TVC
credential_material_present = false
external_side_effect = false
```

`CodeRepair-001` is deterministic in this proof, therefore no TV/TVC provider operation is required. A later provider-backed agent must still use TV/TVC exclusively.

Successful execution must additionally contain a verified StegCore governance chain, continuous transaction identity, Master Records custody `RECORDED`, and a same-run `reconstruct_sovereign` operation with recorded reconstruction receipt IDs.

A successful claim-bound receipt is retained under:

```text
receipts/sovereign-host/stegagents-governed-runtime/<claim_id>.json
receipts/sovereign-host/stegagents-governed-runtime.latest.json
```

## Current authentic runtime observation

Merged main currently contains the WorkerCoordinator task in `HANDOFF_READY` state with `claim_id = null`, no heartbeat timing/fencing token, and no worker instance. No `receipts/sovereign-host/stegagents-governed-runtime.latest.json` is present in repository-visible evidence.

The direct authorized resident-command connector also reports no connected resident device. This is reachability evidence only; it does not create a second-device requirement and does not authorize another runtime.

Therefore no authentic governed-agent roundtrip is claimed yet.

## First unresolved predicate

```text
AUTHENTIC_CURRENT_WORKERCOORDINATOR_CLAIM_FENCE_OBSERVED
```

## Next executable remediation

```text
existing sovereign resident WorkerCoordinator cycle
-> claim STEGAGENTS-GOVERNED-RUNTIME-001 with process:stegagents-governed-runtime-v1
-> verify exact registered CodeRepair-001 manifest blob
-> submit proposal through existing SDK / canonical StegCore/InTr
-> retain governance disposition and returned proposal
-> retain Master Records custody + reconstruct_sovereign receipts
-> write claim-bound governed-runtime receipt
-> reconcile canonical task/egress through existing WorkerCoordinator
```

The runtime goal must remain ACTIVE until that authentic chain is observed continuously. Source, merge, or CI evidence alone may not retire it.

## README decision

No `.github` README update is required. The work binds one task into already-documented WorkerCoordinator/process-adapter behavior and creates no new repository responsibility.

## Manual work

None.
